import json,boto3
from typing import Any
from botocore.client import Config
from apps.core.config import get_settings
class ObjectStorage:
    def __init__(self):
        s=get_settings();self.bucket=s.s3_bucket;self.client=boto3.client("s3",endpoint_url=s.s3_endpoint_url,aws_access_key_id=s.s3_access_key_id,aws_secret_access_key=s.s3_secret_access_key,region_name=s.s3_region,config=Config(signature_version="s3v4"))
    def ensure_bucket(self):
        try:self.client.head_bucket(Bucket=self.bucket)
        except Exception:self.client.create_bucket(Bucket=self.bucket)
    def put_json(self,key:str,payload:dict[str,Any]):self.ensure_bucket();self.client.put_object(Bucket=self.bucket,Key=key,Body=json.dumps(payload,separators=(",",":"),default=str).encode(),ContentType="application/json");return key
    def healthcheck(self):
        try:self.ensure_bucket();return True
        except Exception:return False
