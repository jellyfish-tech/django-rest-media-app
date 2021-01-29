from typing import IO, Union

from django.core.files.base import ContentFile

from ..models import Media


def save_file(
    file: Union[IO, ContentFile], filepath: Union[callable, str], filename: str
) -> Media:
    file_instance = Media()
    file_instance.file.save(name=filename, content=file, upload_to=filepath)
    file_instance.save()
    return file_instance
