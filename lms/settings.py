import logging
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/
SECRET_KEY = ''
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    # Koala applications
    'accounts',

    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Django learning applications
    'taggit',  # Manage tags on objects
    'learning',  # The learning application itself
    'markdownx',  # To render Markdown documents
    'django_bootstrap_breadcrumbs',  # Display breadcrumbs using bootstrap
    'django_countries',  # Mainly to display country flags

    # Theming
    'bootstrap',
    'fontawesome_5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',

    # Backend to automatically authenticate a demonstration user
    'lms.middleware.DemonstrationUserAuthentication',
]

ROOT_URLCONF = 'lms.urls'

AUTH_USER_MODEL = 'accounts.Person'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'lms.context_processors.running_in_demo',
                'lms.context_processors.applications_version',
            ]
        },
    },
]

BREADCRUMBS_TEMPLATE = "django_bootstrap_breadcrumbs/bootstrap4.html"

WSGI_APPLICATION = 'lms.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/2.0/topics/i18n/


def gettext(x): return x


LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('fr', gettext('French')),
    ('en', gettext('English')),
)

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]

# noinspection PyUnresolvedReferences
STATIC_ROOT = os.path.join(BASE_DIR, "prodstatic")
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

SECRET_KEY = "yj6o@&vrar6^l1u68!bxumj@xr4&5)zzk!h1qw&63^&@2d3w@#"

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

LOGGING_LEVEL = logging.INFO

TAGGIT_CASE_INSENSITIVE = True

try:
    from lms.local_settings import *
except ImportError:
    pass

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
