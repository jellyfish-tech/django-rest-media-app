media-sdk
====================

1. DO NOT add this to INSTALLED_APPS settings

         Use it just like common lib

2. Include the polls URLconf in your project urls.py like this

         Package includes few usefull urls:
            "media-url/" - get json for all exists models in DOWNLOADS [see below]
            "media-url/<str:model_name>/" - get json for choosen model in DOWNLOADS [see below]
            "media-url/<str:model_name>/<str:ff_tag>/"  - get json for choosen model and choosen file field in DOWNLOADS [see below]
            "media-url/<str:model_name>/<str:ff_name>/<int:pk>/" - allows to retrieve media url for this resource in 
               'media' and 'rest' forms
   
            "retrieve/<str:model_name>/<str:ff_name>/<int:pk>/" - allows to view media resource
            "download/<str:model_name>/<str:ff_name>/<int:pk>/" - allows to download media resource

3. In settings.py

    3.1. You should set up MEDIA_ROOT and MEDIA_URL to be able to retrieve files.

    3.2. STORAGE_OPTIONS - is your main settings dict for all your media models.
        It has next structure:
   
         STORAGE_OPTIONS = {
             <field tag>: {
                 'driver': <name of prefered driver>, ['local' #1, 's3' #2, 'tus' #3]
                 'configs': {
                     'location': <see explanation below>, [1,2]
                     'default': <path for default value>, [1]
                     'bucket': <your bucket name>, [2]
                     'name_uuid_len': <int. len of "coded" prefix of file>, [1,2,3]
                     'url': <server url>, [3]
                     'chunk_size': <int>, [3]
                     'headers': <headers dict to include in requests>, [3]
                     'rename_tries': <amount of tries to rename file before increasing uuid len int>, [3]
                     'storing_file': <name of the storing uploads urls str>, [3]
                     'retries': <amount of times to reconect int>, [3]
                     'retry_delay': <delay in ms between reconect tries int>, [3]
                     'upload_checksum': <turning the cheksum bool>, [3]
                 }
             },
             <field tag>: {...}
         }
   
   |
   
        EXPLANATIONS:

            location - is a callable object, get one pos arg (pure name of file) and it can get named args with default vals,
            and return path for storing this file e.g:
            
            def create_location(name, request=None):
                from datetime import datetime
                now = datetime.now()
                name = f"EXAMPLES/{now.year}/{now.month}/{now.day}/{"{request.user}/" if request}{name}"
                return name

   |

         3.3 DOWNLOADS - is your setting for models, that files are allowed to be downloaded
            It has next structure:
   
            DOWNLOADS = {
               <your model name, that will be used in urls>: <your model doted path>
            }
        
        
    

4. Request examples

         pass yet


5. Response examples

      All "media-url" responses have almost simmilar response, except specific request

      {
         "<model url name>_model":
            {
               "<field tag>_field": [<list of available specific urls>],
               "<<field tag_field>": [<list of available specific urls>]
            },
         "<model url name>_model":
            {
               "<field tag>_field": [<list of available specific urls>],
               "<<field tag>_field": [<list of available specific urls>]
            },
      }
   
      Depend on params, the response will be more specific e.g: specified model, specified field.
         


6. How to use

      In yoyr models.py
         
         from media_sdk import Media, GenericFileField

      In your model class
   
         1. Inherite from Media class
         2. Create field GenericFileField

         GenericFileField takes one special arg "tag" [<field tag> in configs see above]
         and all other args as common FileField class does.

      Functions:
      
      Each method has it's own doc string
   
         Module provides functions for comfortable saving:
         
            from media_sdk import save_file, save_multy_files

            save_file - will be usefull in case of saving only one file.
   
            save_multy_files - will be usefull in case of saving multiple files.
               It has a more complex argument structure and requires precise names.

7. Cautions

         Notice one thing. Methods presented above, have "upload_to" property. 
         Be careful using this property and admin panel.
         Admin panel - defines location for saving using "location" setting (see STORAGE_OPTIONS above).
         While using provided methods, you also use this setting, difference is adding "upload_to"
         property to the path.
         So, there are two ways to salve it:
            1) Not use "upload_to" property in this methods, and just add it in the "location" setting.
            2) Use only methods, and not admin panel.

   |

         Default imagese re protected from deleting and updating. Notice, in case you
         will change 'default' value in settings, if either deletion or updating occur, 
         previous default value - will be removed (physically).
   
   

8. EXAMPLES
   
   Normal save and update
   
   |
   
      'my_app/models.py'
   
         from media_sdk import Media, GenericFileField
   
         class MyModel(Media):
            my_file1 = GenericFileField(tag='file1_tag')  # let's consider this is for admin needs
            my_file2 = GenericFileField(tag='file2_tag')  # and this is for user, and admin do not have access (or have, but not change [Cautions])
            ...other fields are free for use...
   
   |
      
      'my_app/views.py'

         from media_sdk import save_file, save_multy_files
         from .models import MyModel

         def creating_my_model(request):
            # PART FOR STORING
            files = request.FILES
            file_for_my_file_field_1 = files['file1']
            file_for_my_file_field_2 = files['file2']
            
            fields_data = {
              'file1_tag': {
                  'name': file_for_my_file_field_1.name,
                  'content': file_for_my_file_field_1,
                  'upload_to': '' [carefully read Cautions part above]
              },
              'file2_tag': {
                  'name': file_for_my_file_field_2.name,
                  'content': file_for_my_file_field_2,
                  'upload_to': f'{request.user}' [carefully read Cautions part above]
              },
            }
            saved_model_instance = save_multy_files(MyModel, fields_data)  # [see func doc strings]
            # END

         def updating_my_model(request, pk):  # for example, updating will be only for user's file
            # PART FOR STORING 
            files = request.FILES
            file_for_my_file_field_2 = files['file2']
            data = {
               'filename': file_for_my_file_field_2.name,
               'content': file_for_my_file_field_2,
               'tag': 'file2_tag',
               'upload_to': f'{request.user}'
            }
            updated_and_saved_model_instance = save_file(Senen, **data)
            # END

   Creating with default value

         In case of providing empty 'content', field will consider use
         'default' field of <field tag>'s configs, if it exists, otherwise 
         behaviour will be common.
   
         