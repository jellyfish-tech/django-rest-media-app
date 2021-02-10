from django.conf import settings
from django.http import JsonResponse
from django.utils.module_loading import import_string
from urllib.parse import urljoin


def make_media_url(origin, model, ff_tag, pk):
    return urljoin(origin, f'{model}/{ff_tag}/{pk}/')


def get_all_media(origin):
    models = settings.DOWNLOADS.items()
    response_dict = {}
    for path_model_name, model_path in models:
        model = import_string(model_path)
        instances = model.objects.all()
        model_response_dict = response_dict[path_model_name+'_model'] = {}
        model_file_fields = model().get_generic_file_fields()
        for file_field in model_file_fields:
            urls = model_response_dict[file_field.name+'_field'] = []
            for instance in instances:
                urls.append(make_media_url(origin, path_model_name, file_field.tag, instance.id))
    return response_dict


def get_model_media(origin, path_model_name):
    model = import_string(settings.DOWNLOADS[path_model_name])
    response_dict = {}
    instances = model.objects.all()
    model_response_dict = response_dict[path_model_name + '_model'] = {}
    for file_field in model().get_generic_file_fields():
        urls = model_response_dict[file_field.name + '_field'] = []
        for instance in instances:
            urls.append(make_media_url(origin, path_model_name, file_field.tag, instance.id))
    return response_dict


def get_model_field_media(origin, path_model_name, ff_tag):
    model = import_string(settings.DOWNLOADS[path_model_name])
    response_dict = {}
    instances = model.objects.all()
    model_response_dict = response_dict[path_model_name + '_model'] = {}
    urls = model_response_dict[ff_tag + '_field'] = []
    for instance in instances:
        urls.append(make_media_url(origin, path_model_name, ff_tag, instance.id))
    return response_dict


def get_field_field(model_name, ff_tag, pk):
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

