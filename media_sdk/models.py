from typing import Optional

from django.db import models

from .fields import GenericFileField


class MediaQuerySet(models.QuerySet):
    def get_media_url_or_none(self, file_pk: str) -> Optional[str]:
        try:
            return self.get(pk=file_pk).file.url
        except Media.DoesNotExist:
            return None


class MediaManager(models.Manager):
    def get_queryset(self):
        return MediaQuerySet(self.model, using=self._db)


class Media(models.Model):
    class Meta:
        abstract = True

    objects = MediaManager.from_queryset(MediaQuerySet)()

    def get_generic_file_field_by_tag(self, tag: str):
        for field in self._meta.fields:
            if isinstance(field, GenericFileField):
                if field.tag == tag:
                    return getattr(self, field.name)
        return None

    def get_generic_file_fields(self):
        generic_file_fields = []
        for field in self._meta.fields:
            if isinstance(field, GenericFileField):
                generic_file_fields.append(field)
        return generic_file_fields

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is not None:
            old_self = self.__class__.objects.get(pk=self.pk)
            for field in self.get_generic_file_fields():
                old_stored_file = getattr(old_self, field.name)
                new_storing_file = getattr(self, field.name)
                if old_stored_file and new_storing_file != old_stored_file and old_stored_file != field.default:
                    old_stored_file.delete(False)
        return super(Media, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    def delete(self, using=None, keep_parents=False):
        for file_field in self.get_generic_file_fields():
            field = getattr(self, file_field.name)
            if field.name != file_field.default:
                field.delete(save=False)
        super(Media, self).delete(using=None, keep_parents=False)

    def __str__(self):
        return f"Media #{self.pk}"
