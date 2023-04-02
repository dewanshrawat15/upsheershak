import random
import string
import boto3

from mysite import settings

import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
    verify=False
)

def gen_uuid(k):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(k))