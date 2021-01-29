from typing import IO, Union

from django.core.files.base import ContentFile

from django.db.models import Model


def save_file(
    model_name, file: Union[IO, ContentFile], filepath: Union[callable, str], filename: str
) -> Model:
    file_instance = model_name()
    file_instance.file.save(name=filename, content=file, upload_to=filepath)
    file_instance.save()
    return file_instance
