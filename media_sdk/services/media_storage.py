from django.core.files.storage import FileSystemStorage
from django.core.exceptions import SuspiciousOperation
from django.utils.encoding import force_bytes
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.conf import settings
from urllib.parse import parse_qsl, urlsplit
import boto3
from botocore.exceptions import ClientError
from gzip import GzipFile
from enum import Enum
import posixpath
import uuid
import os
import io


class DriverUtils:

    @staticmethod
    def safe_join(base):
        base_path = base
        final_path = base_path.strip('/')
        return final_path

    @staticmethod
    def clean_name(name):
        clean_name = posixpath.normpath(name).replace('\\', '/')
        return clean_name

    @staticmethod
    def compress_content(content):
        """Gzip a given string content."""
        content.seek(0)
        zbuf = io.BytesIO()
        with GzipFile(mode='wb', fileobj=zbuf, mtime=0.0) as zfile:
            zfile.write(
                content.read() if isinstance(content, bytearray) else force_bytes(content.read())
            )
        zbuf.seek(0)
        return zbuf

    @staticmethod
    def create_file_name(name, max_length):
        if not max_length:
            max_length = 6
        if isinstance(name, tuple):
            name = ''.join(name)
        return ''.join([str(uuid.uuid4().hex[:max_length]), name])


@deconstructible
class SaveLocal(Storage):
    def __init__(self, configs):
        self.fs = FileSystemStorage()
        self.sets = configs
        self.location = self.sets.get('location', lambda name: name)
        self.name_uuid_len = self.sets.get('name_uuid_len', None)

    def get_alternative_name(self, file_root, file_ext):
        return DriverUtils.create_file_name((file_root, file_ext), self.name_uuid_len)

    def get_available_name(self, name, max_length=None):
        name = DriverUtils.create_file_name(name, self.name_uuid_len)
        name = self.location(name)
        name = DriverUtils.clean_name(name)
        return self.fs.get_available_name(name)

    def _save(self, name, content):
        name = self.fs._save(name, content)
        return name

    def url(self, name):
        return self.fs.url(name)


@deconstructible
class SaveS3(Storage):
    def __init__(self, configs):
        self.sets = configs
        self.bucket_name = self.sets['bucket']
        self.name_uuid_len = self.sets.get('name_uuid_len', None)
        self.location = self.sets.get('location', lambda name: name)
        self.s3_resource = boto3.resource('s3')
        self.s3_bucket = self.s3_resource.Bucket(self.bucket_name)

    def get_available_name(self, name, max_length=None):
        start_name = name
        name = DriverUtils.clean_name(name)
        name = DriverUtils.create_file_name(name, self.name_uuid_len)
        try:
            name = DriverUtils.safe_join(self.location(name))
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." %
                                      name)
        while self.exists(name):
            self.available_name(start_name)
        return name

    def exists(self, name):
        try:
            self.s3_resource.meta.client.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except ClientError:
            return False

    def _save(self, name, content):
        obj = self.s3_bucket.Object(name)
        content.seek(0, os.SEEK_SET)
        content = DriverUtils.compress_content(content)
        params = dict()
        params['ContentEncoding'] = 'gzip'
        obj.upload_fileobj(content, ExtraArgs=params)
        return name

    def url(self, name):
        name = DriverUtils.safe_join(name)
        params = dict()
        params['Bucket'] = self.s3_bucket.name
        params['Key'] = name
        url = self.s3_bucket.meta.client.generate_presigned_url('get_object', Params=params)
        split_url = urlsplit(url)
        qs = parse_qsl(split_url.query, keep_blank_values=True)
        blacklist = {
            'x-amz-algorithm', 'x-amz-credential', 'x-amz-date',
            'x-amz-expires', 'x-amz-signedheaders', 'x-amz-signature',
            'x-amz-security-token', 'awsaccesskeyid', 'expires', 'signature',
        }
        filtered_qs = ((key, val) for key, val in qs if key.lower() not in blacklist)
        joined_qs = ('='.join(keyval) for keyval in filtered_qs)
        split_url = split_url._replace(query="&".join(joined_qs))
        return split_url.geturl()


@deconstructible
class SaveCLoudFlare(Storage):
    pass


class SaveDrivers(Enum):
    local = SaveLocal
    s3 = SaveS3
    cf = SaveCLoudFlare


class CustomStorage:
    def __new__(cls, tag):
        option = settings.STORAGE_OPTIONS.get(tag)
        if not option:
            option = {'driver': 'local',
                      'configs': {}
                      }
        return SaveDrivers[option['driver']].value(option['configs'])
