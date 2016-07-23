from .base import *
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.local'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'protocol',
        'USER': 'protocol',
        'PASSWORD': 'protocol',
        'HOST': '',
        'PORT': '',
    }
}

