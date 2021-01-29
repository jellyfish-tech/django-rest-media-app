media-sdk
====================

1. DO NOT add this to INSTALLED_APPS settings

         Use it just like common lib

2. Include the polls URLconf in your project urls.py like this

         pass yet

3. In settings.py

    3.1. You should set up MEDIA_ROOT and MEDIA_URL to be able to retrieve files.

    3.2. STORAGE_OPTIONS - is your main settings dict for all your media models.
        It has next structure:
   
         STORAGE_OPTIONS = {
             <model tag>: {
                 'driver': <name of prefered driver>, ['local', 's3']
                 'configs': {
                     'location': <see explanation below>, [both]
                     'bucket': <your bucket name>, [s3]
                     'name_uuid_len': <int. len of "coded" prefix of file>, [both]
                 }
             },
             <model tag>: {...}
         }
   

        EXPLANATIONS:

            location - is a callable object, get one arg (pure name of file),
            and return path for storing this file e.g:
            
            def create_location(name):
                from datetime import datetime
                now = datetime.now()
                name = f"EXAMPLES/{now.year}/{now.month}/{now.day}/{name}"
                return name
        
        
    

4. Request examples

         pass yet


5. Response examples

         pass yet


6. How to use

      In yoyr models.py
         
         from media_sdk import Media, GenericFileField

      In your model class
   
         1. Inherite from Media class
         2. Create field GenericFileField and name it "file"

      GenericFileField takes one arg "tag" [<model tag> in configs see above]