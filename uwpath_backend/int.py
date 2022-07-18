"""
Django settings for uwpath_backend project.

Generated by 'django-admin startproject' using Django 3.0.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""


import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



# HTTPS Settings
#SESSION_COOKIE_SECURE = True 
#CSRF_COOKIE_SECURE = True
#SECURE_SSL_REDIRECT = True 

# HSTS Settings
#SECURE_HSTS_SECONDS = 31536000 # 1 year
#SECURE_HSTS_PRELOAD = True
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True 


#STATIC_URL = '/static/'
#STATIC_ROOT = '/code/static/'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY") 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1', 'localhost', 'backend', 'uwpath.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app.apps.UwpathConfig',
    'rest_framework',
    'corsheaders'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'uwpath_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'uwpath_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres' if os.getenv("DB_NAME") is None else os.getenv("DB_NAME"),
        'USER': 'postgres' if os.getenv("DB_USER") is None else os.getenv("DB_USER"),
        'PASSWORD': '1234' if os.getenv("DB_PASS") is None else os.getenv("DB_PASS"),
        'HOST': 'db' if os.getenv("DB_HOST") is None else os.getenv("DB_HOST"),
        'PORT': '5432' if os.getenv("DB_PORT") is None else os.getenv("DB_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'


STATICFILES_DIRS = [
    'app/static/',
]


STATIC_ROOT = os.path.join(BASE_DIR, "static/")

# Note for emails to work please set up env variables. Note: You might need to restart your computer

# For sending emails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('UWPath_Email_Account')
SERVER_EMAIL = os.environ.get('UWPath_Email_Account')
EMAIL_HOST = os.environ.get('UWPath_Host')
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('UWPath_Email_Account')
EMAIL_HOST_PASSWORD = os.environ.get('UWPath_Email_Password')
EMAIL_USE_TLS = True

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

CORS_ORIGIN_ALLOW_ALL=True

CORS_ORIGIN_WHITELIST = [
    'http://localhost:8000',
    'http://localhost:8080',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
]
