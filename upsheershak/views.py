from drf_yasg import openapi
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser

from .helper import TranscriptionHelper, run_transcription
from .models import FileRequest
from .serializers import AudioUploadSerializer
from threading import Thread

helper = TranscriptionHelper()


# Create your views here.
class AudioUploadAPI(APIView):
    serializer_class = AudioUploadSerializer

    parser_classes = [MultiPartParser]

    @swagger_auto_schema(request_body=AudioUploadSerializer)
    def post(self, request):
        serializer = AudioUploadSerializer(data=request.data)
        if serializer.is_valid():
            res = serializer.save()
            return Response({
                "message": "File has been uploaded successfully",
                "key": res.key
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "AN ERROR OCCURRED"
            }, status=status.HTTP_400_BAD_REQUEST)


class FileDetailsAPI(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('key', openapi.IN_QUERY, description="S3 File Key", type=openapi.TYPE_STRING)]
    )
    def get(self, request):
        s3_key = self.request.query_params.get('key')
        res = FileRequest.objects.filter(key=s3_key)
        if len(res) == 0:
            return Response({
                "message": "File not found"
            }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                "message": "Results found",
                "data": res[0].toJSON()
            }, status=status.HTTP_200_OK)


class TranscriptionAPI(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('key', openapi.IN_QUERY, description="S3 File Key", type=openapi.TYPE_STRING)]
    )
    def get(self, request):
        s3_key = self.request.query_params.get('key')
        background_thread = Thread(target=run_transcription, args=(s3_key,))
        background_thread.start()
        return Response({
            "message": f"Starting transcription for job {s3_key}"
        }, status=status.HTTP_200_OK)


class TranscriptionStatusAPI(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('key', openapi.IN_QUERY, description="S3 File Key", type=openapi.TYPE_STRING)]
    )
    def get(self, request):
        try:
            s3_key = self.request.query_params.get('key')
            res = FileRequest.objects.filter(key=s3_key)
            if len(res) == 0:
                return Response({
                    "message": "Transcription job not found",
                    "status": False
                }, status=status.HTTP_200_OK)
            else:
                file = res[0]
                return Response({
                    "message": "Transcription is complete" if file.is_processed else "Transcription under progress",
                    "status": file.is_processed
                }, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({
                "message": "AN ERROR OCCURRED"
            }, status=status.HTTP_400_BAD_REQUEST)


class TranscriptionResultAPI(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('key', openapi.IN_QUERY, description="S3 File Key", type=openapi.TYPE_STRING)]
    )
    def get(self, request):
        s3_key = self.request.query_params.get('key')
        res = FileRequest.objects.filter(key=s3_key)
        if len(res) == 0:
            return Response({
                "message": {
                    "file": "File not found"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            file = res[0]
            file_result = file.toJSON()
            return Response({
                "message": {
                    "file": file_result["file"],
                    "captions": file.get_captions(),
                    "audios": file.get_audios(),
                    "detected_lang": file_result["detected_lang"]
                }
            }, status=status.HTTP_200_OK)
