"""Django settings for samaanaiapps project."""

from pathlib import Path
import os
import environ
import google.auth


print("settings.py loaded")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize the environment object
env = environ.Env()

# Load the .env file
env_file = os.path.join(BASE_DIR, '.env')
if os.path.isfile(env_file):
    env.read_env(env_file)  # Load the environment variables from the .env file
    print(".env file loaded successfully")
else:
    print("No .env file found")

# Print environment variable values for debugging
print(f"ENVIRONMENT: {env('ENVIRONMENT', default='Not Set')}")
print(f"SECRET_KEY: {env('SECRET_KEY', default='Not Set')}")
print(f"PROJECT_ID: {env('PROJECT_ID', default='Not Set')}")
print(f"DEBUG: {env.bool('DJANGO_DEBUG', default=False)}")
print(f"HOST: {env('DB_HOST', default='Not Set')}")
print(f"DB_NAME: {env('DB_NAME', default='Not Set')}")
print(f"DB_USER: {env('DB_USER', default='Not Set')}")
#print(f"DB_PASSWORD: {env('DB_PASSWORD', default="Not set")}")
print(f"HOST: {env('DB_HOST', default='Not Set')}")

GOOGLE_APPLICATION_CREDENTIALS = env('GOOGLE_APPLICATION_CREDENTIALS')  # Ensure this is set

try:
    credentials, project = google.auth.default()
    print(f"Google Cloud project: {project}")
except google.auth.exceptions.DefaultCredentialsError as e:
    print(f"Error: {str(e)}")

# Check for Google Application Credentials
if env('GOOGLE_APPLICATION_CREDENTIALS', default=None):
    print("Google Application Credentials detected.")
else:
    print("No Google Application Credentials found.")

# Determine the environment ('development' or 'production')
ENVIRONMENT = env('ENVIRONMENT', default='development')
print("Environment : " + env('ENVIRONMENT'))


SECRET_KEY = None
DB_PASSWORD = None
EMAIL_HOST_PASSWORD = None

if ENVIRONMENT == 'development':
    print('I am insideDevelopement Environment')
    # In development, read from the local .env file

    SECRET_KEY = env('SECRET_KEY', default='your-default-secret-key')
    
    DB_PASSWORD = env('DB_PASSWORD')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    PROJECT_ID = env('PROJECT_ID')
    print(f"PROJECT_ID: {env('PROJECT_ID', default=None)}")
    
    # In development, use local file storage
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
    print("setting css storage in local environment")
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    

else:
    print('This is PRODUCTION Environment')

    # In production, use environment variables and fetch secrets from Secret Manager
    # Assume environment variables are set in the deployment environment (e.g., Cloud Run)

    # Function to get secret from Google Secret Manager
    def get_secret(secret_name):
        """Retrieves the value of a secret from Google Secret Manager.
        Args:secret_name (str): The name of the secret.
        Returns:str: The value of the secret.
        """
        from google.cloud import secretmanager  # Import here to avoid dependency in development

        project_id = os.environ.get('PROJECT_ID')
        if not project_id:
            raise Exception('PROJECT_ID environment variable not set.')

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode('UTF-8')
        return secret_value

    # Fetch secrets from Google Secret Manager
    SECRET_KEY = get_secret('SECRET_KEY')
    DB_PASSWORD = get_secret('DB_PASSWORD')
    EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')
    GOOGLE_APPLICATION_CREDENTIALS = get_secret('GOOGLE_APPLICATION_CREDENTIALS')
    EMAIL_TRIGGER_SECRET_TOKEN=get_secret('EMAIL_TRIGGER_SECRET_TOKEN')

    EMAIL_HOST_USER = env('EMAIL_HOST_USER')  # Set via environment variable in Cloud Run
    
    # In production, use Google Cloud Storage

    GS_BUCKET_NAME = env('GS_BUCKET_NAME')
    
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'



# General settings
DEBUG = env.bool('DEBUG', default=(ENVIRONMENT == 'development'))

print("Before setting the Database settings:")


# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': DB_PASSWORD if ENVIRONMENT == 'production' else env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='db'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

print("Database settings:", DATABASES)



# [START cloudrun_django_csrf]
# SECURITY WARNING: It's recommended that you use this when
# running in production. The URL will be known once you first deploy
# to Cloud Run. This code takes the URL and converts it to both these settings formats.
CLOUDRUN_SERVICE_URL = env("CLOUDRUN_SERVICE_URL", default=None)

# Security settings
if ENVIRONMENT == 'production':
    allowed_hosts_str = env("DJANGO_ALLOWED_HOSTS", default=CLOUDRUN_SERVICE_URL)
    ALLOWED_HOSTS = allowed_hosts_str.split(',')  

    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    if CLOUDRUN_SERVICE_URL:
        CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
    else:
        CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'core',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'todos',
    'spreturn',
    'stocks',
    'travel',
    'my_chatgpt',
    'crispy_forms',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
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
SITE_ID = 2

ROOT_URLCONF = 'samaanaiapps.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')], 
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
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



#Login Management
# Where to go after logging in (defaults to '/accounts/profile/')
LOGIN_REDIRECT_URL = '/'
# Where to go after logging out (defaults to '/accounts/login/')
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
CACHE_TIMEOUT =  300 # 5 minutes

#Logging Framework
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING' if ENVIRONMENT == 'production' else 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO' if ENVIRONMENT == 'production' else 'DEBUG',
            'propagate': False,
        },
        'todos': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Add other app loggers if needed
    },
}


AUTH_USER_MODEL = 'core.CustomUser'  # Adjust 'core' if your app has a different name


#Email realted informmation 

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = EMAIL_HOST_USER  # Assigned earlier
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD  # Assigned earlier

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
