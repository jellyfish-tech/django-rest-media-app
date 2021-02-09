import io
import os
import posixpath
import uuid
from enum import Enum
from gzip import GzipFile
from urllib.parse import parse_qsl, urlsplit

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_bytes
from tusclient import client
from tusclient.exceptions import TusCommunicationError, TusUploadFailed
from tusclient.storage.filestorage import FileStorage


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
        dirname, name = posixpath.split(name)
        name = ''.join([str(uuid.uuid4().hex[:max_length]), name])
        return posixpath.join(dirname, name)


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
        dir_name, file_name = os.path.split(name)
        name = DriverUtils.create_file_name(file_name, self.name_uuid_len)
        name = posixpath.join(dir_name, name)
        name = self.location(name)
        name = DriverUtils.clean_name(name)
        return self.fs.get_available_name(name)

    def _save(self, name, content):
        name = self.fs._save(name, content)
        return name

    def url(self, name):
        return self.fs.url(name)

    def delete(self, name):
        try:
            os.remove(posixpath.join(settings.MEDIA_ROOT, name))
        except OSError as ose:
            print(f'File "{ose.filename}" does not exist')


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
            self.get_available_name(start_name)
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

    def delete(self, name):
        self.s3_resource.Object(self.bucket_name, name).delete()


@deconstructible
class TusStorage(Storage):

    def __init__(self, configs):
        self.sets = configs
        self.name_uuid_len = self.sets.get('name_uuid_len', 5)
        self.my_client = client.TusClient(url=self.sets['url'],
                                          headers=self.sets.get('headers', {}))

        self.uploader = None

        self.rename_tries = self.sets.get('rename_tries', 5)
        self.storing_file = self.sets.get('storing_file', 'tus_url_storage')

        self.opt_conf = dict(chunk_size=self.sets.get('chunk_size', 500),
                             retries=self.sets.get('retries', 5),
                             retry_delay=self.sets.get('retry_delay', 10),
                             upload_checksum=self.sets.get('upload_checksum', True)
                             )

    def url(self, name):
        return name

    def get_available_name(self, name, max_length=None):
        name = DriverUtils.create_file_name(name, self.name_uuid_len)
        return name

    def save(self, name, content, max_length=None):
        metadata = {'filename': name}
        if self.storing_file:
            storing = FileStorage(self.storing_file)
            store_url = True
        else:
            storing = None
            store_url = False

        rename_tries = self.rename_tries

        while True:
            try:
                rename_tries -= 1
                self.uploader = self.my_client.uploader(file_stream=content,
                                                        metadata=metadata,
                                                        store_url=store_url,
                                                        url_storage=storing,
                                                        **self.opt_conf)
                break
            except TusCommunicationError as tus_comm:
                if tus_comm.status_code == 409:
                    if rename_tries <= 0:
                        self.name_uuid_len += 1
                        rename_tries = self.rename_tries
                    metadata['filename'] = self.get_available_name(name)

        try:
            self.uploader.upload()
        except TusUploadFailed as tus_upl:
            pass
        else:
            if self.uploader.store_url:
                self.uploader.url_storage.remove_item(
                    self.uploader.fingerprinter.get_fingerprint(
                        self.uploader.get_file_stream()
                    )
                )
            return metadata['filename']

    def delete(self, name):
        pass


class SaveDrivers(Enum):
    local = SaveLocal
    s3 = SaveS3
    tus = TusStorage


class CustomStorage:
    def __new__(cls, tag):
        option = settings.STORAGE_OPTIONS.get(tag)
        if not option:
            option = {'driver': 'local',
                      'configs': {}
                      }
        return SaveDrivers[option['driver']].value(option['configs'])
