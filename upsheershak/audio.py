from gtts import gTTS

class SubtitleLine:

    def __init__(self, id, start, end, text):
        self.id = id
        self.start = start
        self.end = end
        self.text = text

def get_timestamps(timestamp_data):
    ts = timestamp_data.split(" --> ")
    start, end = ts[0], ts[1]
    print(start, end)
    return start, end

def read_srt(fileName):
    with open(fileName, "r") as srt_file:
        data = srt_file.read()
        srt_data = data.split("\n")
        subtitles = []
        line_data = []
        while srt_data[-1] == "":
            srt_data.pop()
        for dt in srt_data:
            if len(dt) == 0:
                start, end = get_timestamps(line_data[1])
                subtitles.append(SubtitleLine(line_data[0], start, end, line_data[2]))
                line_data = []
            else:
                line_data.append(dt)
        if len(line_data) > 0:
            subtitles.append(SubtitleLine(line_data[0], start, end, line_data[2]))
        return subtitles

for subtitle in subtitles:
    myobj = gTTS(text=subtitle.text, lang=lang, slow=False)
    myobj.save(f"{subtitle.id}.mp3")
