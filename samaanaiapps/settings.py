"""Django settings for samaanaiapps project."""

from pathlib import Path
import os
import environ
import google.auth
import json
from google.oauth2 import service_account
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
from django.contrib.messages import constants as messages



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
    print('I am inside Developement Environment')
    # In development, read from the local .env file

    SECRET_KEY = env('SECRET_KEY', default='your-default-secret-key')
    GOOGLE_APPLICATION_CREDENTIALS = env('GOOGLE_APPLICATION_CREDENTIALS')  # Ensure this is set

    
    DB_PASSWORD = env('DB_PASSWORD')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('SENDGRID_API_KEY')
    PROJECT_ID = env('PROJECT_ID')

    print(f"DB_PASSWORD: {env('DB_PASSWORD', default=None)}")
    print(f"EMAIL_HOST_PASSWORD: {env('SENDGRID_API_KEY', default=None)}")
    print(f"EMAIL_HOST_USER: {env('EMAIL_HOST_USER', default=None)}")
    print(f"PROJECT_ID: {env('PROJECT_ID', default=None)}")
    
    # In development, use local file storage for everythig.
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
    print("setting css storage in local environment")
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    
 #Logging Framework
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
            },
            'verbose': {
                'format': '[%(asctime)s] %(levelname)s %(name)s %(pathname)s:%(lineno)d - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': os.path.join(BASE_DIR, 'logs/django_app.log'),
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'core': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'return': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'stocks': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'todos': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': True,
            },
            'travel': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }

else:
    print('I am inside PRODUCTION Environment')

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


    # Fetch the service account JSON from the environment variable (as injected from Secret Manager)
    service_account_info = json.loads(get_secret('GOOGLE_APPLICATION_CREDENTIALS'))

    GS_CREDENTIALS = service_account.Credentials.from_service_account_info(service_account_info)

    # Fetch secrets from Google Secret Managerd
    SECRET_KEY = get_secret('SECRET_KEY')
    DB_PASSWORD = get_secret('DB_PASSWORD')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')  # Set via environment variable in Cloud Run
    EMAIL_HOST_PASSWORD = get_secret('SENDGRID_API_KEY')
    
    # In production, use Google Cloud Storage
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

    GS_BUCKET_NAME = env('GS_BUCKET_NAME','using-ai-405105_using-ai-samaan')
    
    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

    client = google.cloud.logging.Client()
    client.setup_logging()

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
            },
        },
        'handlers': {
            'cloud': {
                'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
                'client': client,
                'formatter': 'standard',
            },
        },
        'root': {
            'handlers': ['cloud'],
            'level': 'INFO',  # Adjust level based on your needs
        },
    }


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


CLOUDRUN_SERVICE_URL = env("CLOUDRUN_SERVICE_URL", default=None)
print("CLOUDRUN_SERVICE_URL:", CLOUDRUN_SERVICE_URL)

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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'spreturn',
    'stocks',
    'todos',
    'travel',
    'widget_tweaks',
    'crispy_forms',
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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)


SITE_ID = 3

ROOT_URLCONF = 'samaanaiapps.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Required by Allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'samaanaiapps.wsgi.application'


# Password validation
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
LOGIN_URL = '/accounts/login/'  # This should match the URL for your custom login view
LOGIN_REDIRECT_URL = '/dashboard/'    # Where users go after login

# Redirect to homepage after logout
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'  # Redirect after logout
ACCOUNT_SIGNUP_REDIRECT_URL = '/profile/'  # Redirect after signup
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/dashboard/'  # For logged-in users
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/accounts/login/'  # For anonymous users

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Or as per your requirement
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Options: 'none', 'optional', 'mandatory'

# settings.py
ACCOUNT_FORMS = {
    'signup': 'core.forms.CustomSignupForm',
}


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '1074693546571-9g0hd309eq0j2b2hv788g9lkn65pdl1p.apps.googleusercontent.com',
            'secret': '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',
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
CACHE_TIMEOUT =  300 # 5 minutes


MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',  # Bootstrap uses 'danger' instead of 'error'
}

AUTH_USER_MODEL = 'core.CustomUser'  # Adjust 'core' if your app has a different name

# Email Backend Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587  # Use 465 for SSL
EMAIL_USE_TLS = True  # Use EMAIL_USE_SSL=True if using port 465
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='kittureddydeals@gmail.com')


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

print("EMAIL_BACKEND:", EMAIL_BACKEND)
print("EMAIL_HOST:", EMAIL_HOST)
print("EMAIL_USE_TLS:", EMAIL_USE_TLS)
print("EMAIL_PORT:", EMAIL_PORT)
print("EMAIL_HOST_USER:", EMAIL_HOST_USER)
print("EMAIL_HOST_PASSWORD:", EMAIL_HOST_PASSWORD)
print("DEFAULT_FROM_EMAIL:", DEFAULT_FROM_EMAIL)
# print("GS_BUCKET_NAME:", GS_BUCKET_NAME)
print("Static URL:", STATIC_URL)
print("Media URL:", MEDIA_URL)


print('I am the end of settings.py')
