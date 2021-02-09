import datetime
import posixpath
from typing import Union

from django.conf import settings
from django.db import models
from django.db.models.fields.files import FieldFile

from .services.media_storage import CustomStorage


def get_default_image(tag):
    model = settings.STORAGE_OPTIONS.get(tag)
    if model:
        confs = model.get('configs')
        if confs:
            return confs.get('default')
    return None


class GenericFile(FieldFile):
    def save(self, name, content, save=False, upload_to=None):
        if upload_to:
            name = self.generate_filename(self.instance, name, upload_to)

        if content:
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
        self.default_img_path = get_default_image(tag=self.tag)
        if self.default_img_path:
            kwargs['default'] = self.default_img_path
        kwargs['storage'] = self.storage
        super(GenericFileField, self).__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(GenericFileField, self).deconstruct()
        kwargs['tag'] = self.tag
        return name, path, args, kwargs
