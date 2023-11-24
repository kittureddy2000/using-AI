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
import environ
from google.cloud import secretmanager

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

env = environ.Env()  # Initialize environ
environ.Env.read_env()  # Read .env file

#Google Secret Manager Helper fuction
def access_secret_version(project_id, secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = 'django-insecure-+&^un(msi47ggou(0=u%39k9wpz*^e3tkoiy61#co4qetrmme('


#ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
ALLOWED_HOSTS = ['*']


RUNNING_ON_CLOUD_RUN = os.getenv('GOOGLE_CLOUD_RUN') == 'True'

if RUNNING_ON_CLOUD_RUN:
    project_id = os.getenv('PROJECT_ID',default='111')
    DEBUG = env.bool('DJANGO_DEBUG', default=False)

    SECRET_KEY = access_secret_version(project_id, 'PROD_SECRET_KEY')
    DB_NAME = access_secret_version(project_id,'DB_NAME')
    DB_USER = access_secret_version(project_id,'DB_USER')
    DB_PASSWORD = access_secret_version(project_id,'DB_PASSWORD')
    DB_HOST = access_secret_version(project_id,'DB_HOST')
    DB_PORT = access_secret_version(project_id,'DB_PORT')

else :
    SECRET_KEY = env('DJANGO_SECRET_KEY', default='Default Testkey')
    DEBUG = env.bool('DJANGO_DEBUG', default=False)
    DB_NAME=env('samaan-db', default='Default_db')
    DB_USER=env('mypostgres', default='Default_user')
    DB_PASSWORD=env('Vtnkpv55!@#', default='password') #DATABASE_PASSWORD,
    DB_HOST=env('127.0.0.1' , default='localhost')#'34.82.137.151' Use Cloud SQL Proxy address for local development
    DB_PORT=env('5432', default='0000') # Default port for PostgreSQL

SITE_ID = 2

# Where to go after logging in (defaults to '/accounts/profile/')
LOGIN_REDIRECT_URL = '/todos/'
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Add this line
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

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME
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
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'using-ai-samaan>'


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


