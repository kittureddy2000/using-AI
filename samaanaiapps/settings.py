"""
Django settings for samaanaiapps project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import io
import environ
from urllib.parse import urlparse
import google.auth
from google.cloud import secretmanager
from core.utils import access_secret


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

env = environ.Env()  # Initialize environ
environ.Env.read_env()  # Read .env file

env_file = os.path.join(BASE_DIR, ".env")

if os.path.isfile(env_file):
    # Use a local secret file, if provided
    env.read_env(env_file)
    print("Local file env exists")
else:
    print("Local file env doesnt exists")

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = 'django-insecure-+&^un(msi47ggou(0=u%39k9wpz*^e3tkoiy61#co4qetrmme('


#ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
ALLOWED_HOSTS = ['*']


try:
    _, os.environ["GOOGLE_CLOUD_PROJECT"] = google.auth.default()
except google.auth.exceptions.DefaultCredentialsError:
    pass

if os.path.isfile(env_file):
    # Use a local secret file, if provided
    env.read_env(env_file)
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", None)
    print("Getting Secret manage from local")
    print("Getting Secret manager for TEST_KEY")
    #print(access_secret (project_id,'TESTING_KEY'))
    print("Getting Secret manager for DJANGO_SETTINGS")
    #print(access_secret (project_id,'SETTINGS_NAME'))
elif os.environ.get("GOOGLE_CLOUD_PROJECT", None):
    # Pull secrets from Secret Manager
    print("Inside Google Cloud Project Environment")

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    print("project Id : " + project_id)
    payload = access_secret (project_id,'DJANGO_SETTINGS')
    GOOGLE_APPLICATION_CREDENTIALS = access_secret (project_id,'GOOGLE_APPLICATION_CREDENTIALS')

    env.read_env(io.StringIO(payload))
else:
    raise Exception("No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found.")
# [END cloudrun_django_secret_config]

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
DB_NAME= env("DB_NAME")
DB_USER= env("DB_USER")
DB_PASSWORD = env("DB_PASSWORD")
DB_HOST= env("DB_HOST")
DB_PORT= env("DB_PORT")

print( "DB_NAME  " + DB_NAME )
print( "DB_USER " + DB_USER )
#print( "DB_PASSWORD  " + DB_PASSWORD )
print( "DB_HOST  " + DB_HOST )
print( "DB_PORT  " + DB_PORT )
#print( "SECRET_KEY  " + SECRET_KEY )


# [START cloudrun_django_csrf]
# SECURITY WARNING: It's recommended that you use this when
# running in production. The URL will be known once you first deploy
# to Cloud Run. This code takes the URL and converts it to both these settings formats.
CLOUDRUN_SERVICE_URL = env("CLOUDRUN_SERVICE_URL", default=None)
print("Cloud Service URL")
print(CLOUDRUN_SERVICE_URL)
if CLOUDRUN_SERVICE_URL:
    print("Cloud Service URL")
    print(CLOUDRUN_SERVICE_URL)
    ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
    CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    ALLOWED_HOSTS = ["*"]

SITE_ID = 2

# Where to go after logging in (defaults to '/accounts/profile/')
LOGIN_REDIRECT_URL = '/'
# Where to go after logging out (defaults to '/accounts/login/')
LOGOUT_REDIRECT_URL = '/accounts/login/'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'todos',
    'core',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Add the providers you want to use
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    # ... more providers if needed ...
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'samaanaiapps.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],  # Add this line
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'samaanaiapps.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD, #DATABASE_PASSWORD,
        'HOST': DB_HOST, #'34.82.137.151' Use Cloud SQL Proxy address for local development
        'PORT': DB_PORT, # Default port for PostgreSQL
        }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'https://storage.googleapis.com/using-ai-samaan/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'core/static')]
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
MEDIA_URL = 'https://storage.googleapis.com/using-ai-samaan/media/'
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'using-ai-samaan'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTHENTICATION_BACKENDS = (
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
SOCIALACCOUNT_LOGIN_ON_GET = True


