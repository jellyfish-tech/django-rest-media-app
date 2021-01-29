from typing import Optional

from django.db import models


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

    def __str__(self):
        return f"Media #{self.pk}"
