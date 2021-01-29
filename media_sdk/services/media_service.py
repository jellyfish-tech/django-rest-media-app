from typing import IO, Union

from django.core.files.base import ContentFile

from django.db.models import Model

from ..models import Media


def save_file(model, file: Union[IO, ContentFile], filename: str, filepath=None) -> Model:
    file_instance = model()
    file_instance.file.save(name=filename, content=file, upload_to=filepath)
    file_instance.save()
    return file_instance


def save_multy_files(model, fields_data: dict, save=True):
    """
        Method for saving files in case of multiple GenericFileField.
        ::params
            model - your model class for saving or instance for updating
            fields_data - dict with the next structure:
                fields_data = {
                    '<field name>': {
                        'name': '<filename: str>', [required]
                        'content': <file: ContentFile, IO>, [required]
                        'upload_to': <path-like or callable function: str, callable> [optional]
                    }
                }
            save - bool. If True - model will be saved, else - not.
        ::returns
            Model instance
    """

    if isinstance(model, Media):
        file_instance = model
    else:
        file_instance = model()

    for field in fields_data:
        field_ins = getattr(file_instance, field, None)
        if field_ins is None:
            continue
        field_ins.save(**fields_data[field])
    if save:
        file_instance.save()
    return file_instance
