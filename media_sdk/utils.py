from typing import Optional, Text, Tuple, Type, Union
from urllib.parse import urljoin

from django.conf import settings
from django.db.models import Model
from django.http import JsonResponse
from django.utils.module_loading import import_string

from .fields import GenericFileField


def make_media_url(origin: Text, model: Text, ff_tag: Text, pk: int) -> Text:
    return urljoin(origin, f'{model}/{ff_tag}/{pk}/')


def get_model_info(path_model_name: Optional[str] = None) -> Union[None, Type[Model]]:
    if not path_model_name:
        try:
            models = settings.DOWNLOADS.items()
        except AttributeError:
            return None
        return models
    try:
        model = import_string(settings.DOWNLOADS[path_model_name])
    except (AttributeError, KeyError):
        return None
    return model


def get_all_media(origin: Text) -> Tuple[dict, int]:
    models = get_model_info()
    if not models:
        return {'status': 'Nothing found'}, 404
    response_dict = {}
    for path_model_name, model_path in models:
        model = import_string(model_path)
        instances = model.objects.all()
        model_response_dict = response_dict[path_model_name+'_model'] = {}
        model_file_fields = model().get_generic_file_fields()
        for file_field in model_file_fields:
            urls = model_response_dict[file_field.tag+'_field'] = []
            for instance in instances:
                urls.append(make_media_url(origin, path_model_name, file_field.tag, instance.id))
    return response_dict, 200


def get_model_media(origin: Text, path_model_name: Text) -> Tuple[dict, int]:
    model = get_model_info(path_model_name)
    if not model:
        return {'status': 'Nothing found'}, 404
    response_dict = {}
    instances = model.objects.all()
    model_response_dict = response_dict[path_model_name + '_model'] = {}
    for file_field in model().get_generic_file_fields():
        urls = model_response_dict[file_field.tag + '_field'] = []
        for instance in instances:
            urls.append(make_media_url(origin, path_model_name, file_field.tag, instance.id))
    return response_dict, 200


def get_model_field_media(origin: Text, path_model_name: Text, ff_tag: Text) -> Tuple[dict, int]:
    model = get_model_info(path_model_name)
    if not model:
        return {'status': 'Nothing found'}, 404
    response_dict = {}
    instances = model.objects.all()
    model_response_dict = response_dict[path_model_name + '_model'] = {}
    if model().get_generic_file_field_by_tag(ff_tag) is None:
        return {'status': 'Nothing found'}, 404
    urls = model_response_dict[ff_tag + '_field'] = []
    for instance in instances:
        urls.append(make_media_url(origin, path_model_name, ff_tag, instance.id))
    return response_dict, 200


def get_field_field(model_name: Text, ff_tag: Text, pk: int) -> Union[JsonResponse, GenericFileField]:
    try:
        model = import_string(settings.DOWNLOADS[model_name])
    except ImportError:
        return JsonResponse({'status': 'No such model'}, status=400)
    try:
        instance = model.objects.get(id=pk)
    except model.DoesNotExist:
        return JsonResponse({'status': 'No such pk'}, status=400)

    file_field = instance.get_generic_file_field_by_tag(ff_tag)
    if not file_field:
        return JsonResponse({'status': 'No such field'}, status=400)
    return file_field

