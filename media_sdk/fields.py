import datetime
import posixpath
from typing import Union

from django.db import models
from django.db.models.fields.files import FieldFile
from .services.media_storage import CustomStorage


class GenericFile(FieldFile):
    def save(self, name, content, save=False, upload_to=None):
        if upload_to:
            name = self.generate_filename(self.instance, name, upload_to)
        self.name = self.storage.save(
            name, content, max_length=self.field.max_length
        )
        setattr(self.instance, self.field.name, self.name)
        self._committed = True

    def generate_filename(
        self, instance, filename, upload_to: Union[str, callable] = ""
    ):
        if callable(upload_to):
            filename = upload_to(instance, filename)
        else:
            filename = posixpath.join(upload_to, filename)
        return self.storage.generate_filename(filename)


class GenericFileField(models.FileField):
    attr_class = GenericFile

    def __init__(self, tag='', **kwargs):
        self.tag = tag
        self.storage = CustomStorage(tag=self.tag)
        kwargs['storage'] = self.storage
        super(GenericFileField, self).__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(GenericFileField, self).deconstruct()
        kwargs['tag'] = self.tag
        return name, path, args, kwargs
