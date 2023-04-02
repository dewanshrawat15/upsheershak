import os
import subprocess
from datetime import timedelta
from threading import Thread

import whisper
from django.utils import timezone

from mysite import settings
from .models import FileRequest
from .utils import s3

class ResultSegment:

    def __init__(self, id, start, end, text):
        self.id = id
        self.start = start
        self.end = end
        self.text = text

    def toJSON(self):
        return {
            "id": self.id,
            "start": self.start,
            "end": self.end,
            "text": self.text
        }


class TranscriptionResult:

    def __init__(self, text, lang, segments):
        self.text = text
        self.lang_code = lang
        self.segments = segments

    def toJSON(self):
        return {
            "text": self.text,
            "lang_code": self.lang_code,
            "segments": [res.toJSON() for res in self.segments]
        }


def get_segments(segments):
    results = [
        ResultSegment(seg["id"], seg["start"], seg["end"], seg["text"]) for seg in segments
    ]
    return results


def get_result(decoded_result):
    lang = decoded_result["language"]
    text = decoded_result["text"]
    segments = get_segments(decoded_result["segments"])
    return TranscriptionResult(text, lang, segments)


class TranscriptionHelper:

    def langs(self, probs):
        return max(probs, key=probs.get)

    def decode(self, mel, model, audio, lang_code):
        options = {
            "language": lang_code,
            "task": "transcribe",
            "fp16": False
        }
        result = whisper.transcribe(model, audio, **options)
        return result

    def start_processing(self, fileName):
        model = whisper.load_model("large-v2")
        audio = whisper.load_audio(fileName)
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        _, probs = model.detect_language(mel)
        lang_code = self.langs(probs)
        decoded_result = self.decode(mel, model, audio, lang_code)

        result = get_result(decoded_result)
        return result

    def translate(self, fileName, lang_code):
        model = whisper.load_model("large-v2")
        audio = whisper.load_audio(fileName)
        audio = whisper.pad_or_trim(audio)

        options = {
            "language": lang_code,
            "task": "transcribe",
            "fp16": False
        }

        result = get_result(whisper.transcribe(model, audio, **options))
        return result

    def generate_srt(self, s3, result, s3_key, lang=""):
        try:
            segments = result.segments
            file_name = f"{s3_key}.srt" if len(lang) == 0 else f"{s3_key}-{lang}.srt"
            for segment in segments:
                startTime = str(0) + str(timedelta(seconds=int(segment.start))) + '.000'
                endTime = str(0) + str(timedelta(seconds=int(segment.end))) + '.000'
                text = segment.text
                segmentId = segment.id + 1

                segmentData = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] == ' ' else text}\n\n"
                with open(file_name, "a", encoding='utf-8') as srtFile:
                    srtFile.write(segmentData)
            s3.upload_file(
                file_name,
                settings.AWS_STORAGE_BUCKET_NAME,
                f"files/{s3_key}/{file_name}"
            )
            return {
                "error": False
            }
        except Exception as e:
            print(e)
            return {
                "error": True
            }

    def generate_vtt(self, s3, result, s3_key, lang=""):
        try:
            segments = result.segments
            file_name = f"{s3_key}.vtt" if len(lang) == 0 else f"{s3_key}-{lang}.vtt"
            with open(file_name, "a", encoding='utf-8') as srtFile:
                srtFile.write("WEBVTT\n\n")
            for segment in segments:
                startTime = str(0) + str(timedelta(seconds=int(segment.start))) + '.000'
                endTime = str(0) + str(timedelta(seconds=int(segment.end))) + '.000'
                text = segment.text
                segmentId = segment.id + 1

                segmentData = f"{startTime} --> {endTime}\n{text[1:] if text[0] == ' ' else text}\n\n"
                with open(file_name, "a", encoding='utf-8') as srtFile:
                    srtFile.write(segmentData)
            s3.upload_file(
                file_name,
                settings.AWS_STORAGE_BUCKET_NAME,
                f"files/{s3_key}/{file_name}"
            )
            return {
                "error": False
            }
        except Exception as e:
            print(e)
            return {
                "error": True
            }

    def save_result(self, s3, result, s3_key, lang=""):
        self.generate_srt(s3, result, s3_key, lang)
        self.generate_vtt(s3, result, s3_key, lang)


helper = TranscriptionHelper()


def delete_files(s3_key, file_name):
    os.remove(f"{file_name}")
    os.remove(f"{s3_key}.srt")
    os.remove(f"{s3_key}.vtt")


def run_translations(s3, lang_codes, file_name):
    s3_key = file_name.split(".")[0]
    res = FileRequest.objects.filter(key=s3_key)
    if len(res) != 0:
        file_req = res[0]
        for code in lang_codes:
            translated_result = helper.translate(file_name, code)
            helper.save_result(s3, translated_result, s3_key, code)
            file_req.last_modified = timezone.now()
            file_req.save()
        file_req.is_processed = True
        file_req.save()
        return
    else:
        return


def run_transcription(s3_key):
    res = FileRequest.objects.filter(key=s3_key)
    if len(res) == 0:
        return
    else:
        file_request = res[0]
        s3_file_path = file_request.file.url.split(".amazonaws.com/")[-1].split("?")[0]
        file_name = s3_file_path.split("/")[-1]
        s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, s3_file_path, file_name)

        audio_file_name = file_name.split(".")[0] + ".mp3"

        subprocess.call(["ffmpeg", "-y", "-i", file_name, f"{audio_file_name}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT)

        res = helper.start_processing(audio_file_name)

        helper.save_result(s3, res, s3_key)
        # delete_files(s3_key, file_name)
        file_request.detected_lang = res.lang_code
        file_request.last_modified = timezone.now()
        file_request.save()
        lang_codes = file_request.lang_codes.split(",")
        lang_codes = [code for code in lang_codes if code != res.lang_code]
        if len(lang_codes) != 0:
            background_thread = Thread(target=run_translations, args=(s3, lang_codes, audio_file_name))
            background_thread.start()
        else:
            file_request = FileRequest.objects.filter(key=s3_key)[0]
            file_request.is_processed = True
            file_request.save()
        return
