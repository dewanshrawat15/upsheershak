from rest_framework import serializers
from .models import FileRequest
from django.utils import timezone

from .utils import gen_uuid


class AudioUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileRequest
        fields = ('file', 'lang_codes',)

    def create(self, validated_data):
        s3_file_key = gen_uuid(8)
        file_request_obj = FileRequest.objects.create(
            file=validated_data.pop("file"),
            lang_codes=validated_data.pop("lang_codes"),
            key=s3_file_key,
            created_on=timezone.now(),
            last_modified=timezone.now()
        )
        return file_request_obj
