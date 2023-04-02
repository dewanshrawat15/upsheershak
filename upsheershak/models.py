import subprocess

from django.db import models
from .utils import s3
from mysite import settings

# Create your models here.
def modify_filename(instance, filename):
    extension = filename.split(".")[-1].strip()
    return f"files/{instance.key}/{instance.key}.{extension}"


class FileRequest(models.Model):
    lang_codes = models.CharField(max_length=128)
    is_processed = models.BooleanField(default=False)
    key = models.CharField(max_length=8)
    file = models.FileField(upload_to=modify_filename)
    last_modified = models.DateTimeField()
    created_on = models.DateTimeField()
    detected_lang = models.CharField(max_length=4, default="")

    def save(self, *args, **kwargs):
        if self.is_processed:
            print("DELETE ALL FILES")
        super(FileRequest, self).save(*args, **kwargs)

    def __str__(self):
        return self.key

    def delete(self):
        # delete S3 handle correctly
        self.file.delete(save=False)
        super().delete()

    def toJSON(self):
        return {
            "lang": self.lang_codes,
            "detected_lang": self.detected_lang,
            "is_processed": self.is_processed,
            "last_modified": self.last_modified,
            "created_on": self.created_on,
            "key": self.key,
            "file": self.file.url
        }

    def get_captions(self):
        codes = self.lang_codes.split(",")
        expiration = 60 * 60 * 24
        captions = {}
        if self.detected_lang:
            captions[self.detected_lang] = s3.generate_presigned_url('get_object',
                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': f"/files/{self.key}/{self.key}.srt"},
                ExpiresIn=expiration)
        if self.detected_lang in codes:
            codes = [lang for lang in codes if lang != self.detected_lang]
        for code in codes:
            captions[code] = s3.generate_presigned_url('get_object',
                  Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                          'Key': f"/files/{self.key}/{self.key}-{code}.srt"},
                  ExpiresIn=expiration)
        return captions
