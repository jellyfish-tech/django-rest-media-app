from ..models import Media


def save_file(model, file, filename: str, tag: str, upload_to=None, save=True):
    """
        Method for saving files in case of one GenericFileField.
        ::params
            model - your model class for creating or instance for updating
            file - content
            filename - name of the file
            tag - tag of the GenericFileField in your model
            upload_to - path for uploading to
            save - bool. If True - model will be saved, else - not.
        ::returns
            Model instance
    """

    if isinstance(model, Media):
        model_instance = model
    else:
        model_instance = model()

    result_field = model_instance.get_generic_file_field_by_tag(tag)
    if result_field is not None:
        result_field.save(name=filename, content=file, upload_to=upload_to)
    if save:
        model_instance.save()
    return model_instance


def save_multy_files(model, fields_data: dict, save=True):
    """
        Method for saving files in case of multiple GenericFileField.
        ::params
            model - your model class for creating or instance for updating
            fields_data - dict with the next structure:
                fields_data = {
                    '<field tag>': {
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
        model_instance = model
    else:
        model_instance = model()

    for field_tag in fields_data:
        result_field = model_instance.get_generic_file_field_by_tag(field_tag)
        if result_field is None:
            continue
        result_field.save(**fields_data[field_tag])
    if save:
        model_instance.save()
    return model_instance
