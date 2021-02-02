from typing import Optional

from django.db import models

from .fields import GenericFileField

from django.conf import settings


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

    def get_generic_file_field_by_tag(self, tag):
        for field in self._meta.fields:
            if isinstance(field, GenericFileField):
                if field.tag == tag:
                    return getattr(self, field.name)
        return None

    def get_generic_file_fields(self):
        gff = []
        for field in self._meta.fields:
            if isinstance(field, GenericFileField):
                gff.append(field.name)
        return gff

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is not None:
            old_self = self.__class__.objects.get(pk=self.pk)
            for field in self.get_generic_file_fields():
                old_file = getattr(old_self, field)
                new_file = getattr(self, field)
                if old_file and new_file != old_file:
                    old_file.delete(False)
        return super(Media, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    def delete(self, using=None, keep_parents=False):
        # FIXME make if no settings ('local' storage MEDIA_ROOT path by default)
        for field_tag in settings.STORAGE_OPTIONS:
            file_field = self.get_generic_file_field_by_tag(field_tag)
            if not file_field:
                continue
            file_field.delete()
        super(Media, self).delete(using=None, keep_parents=False)

    def __str__(self):
        return f"Media #{self.pk}"
