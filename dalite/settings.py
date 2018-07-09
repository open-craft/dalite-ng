"""
Django settings for dalite project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = (
    'peerinst',
    'grappelli',
    'password_validation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_lti_tool_provider',
    'compressor',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # Minify html
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'htmlmin.middleware.MarkRequestMiddleware',
)

ROOT_URLCONF = 'dalite.urls'

CUSTOM_SETTINGS = os.environ.get('CUSTOM_SETTINGS', 'default')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'custom-settings/'+CUSTOM_SETTINGS+'/templates')],
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

WSGI_APPLICATION = 'dalite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DALITE_DB_NAME', 'dalite_ng'),
        'USER': os.environ.get('DALITE_DB_USER', 'dalite'),
        'PASSWORD': os.environ.get('DALITE_DB_PASSWORD', ''),
    }
}

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# Password validators through django-password-validation (backport from 1.9)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'custom-settings/'+CUSTOM_SETTINGS+'/static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_ENABLED = True
KEEP_COMMENTS_ON_MINIFYING = False
HTML_MINIFY = True

# LOGIN_URL = 'login'
LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = 'welcome'

GRAPPELLI_ADMIN_TITLE = 'Dalite NG administration'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file_debug_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log/debug.log'),
        },
        'file_student_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log/student.log'),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file_debug_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'peerinst.views': {
            'handlers': ['file_student_log'],
            'level': 'INFO',
            'propagate': True,
        },
        'django_lti_tool_provider.views': {
            'handlers': ['file_debug_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# LTI integration

# these are sensitive settings, so it is better to fail early than use some defaults visible on public repo
LTI_CLIENT_KEY = os.environ.get('LTI_CLIENT_KEY', None)
LTI_CLIENT_SECRET = os.environ.get('LTI_CLIENT_SECRET', None)

# hint: LTi passport in edX Studio should look like <arbitrary_label>:LTI_CLIENT_KEY:LTI_CLIENT_SECRET

# Used to automatically generate stable passwords from anonymous user ids coming from LTI requests - keep secret as well
# If compromised, attackers would be able to restore any student passwords knowing his anonymous user ID from LMS
PASSWORD_GENERATOR_NONCE = os.environ.get('PASSWORD_GENERATOR_NONCE', None)
# LTI Integration end

# Configureation file for the heartbeat view, should contain json file. See this url for file contents.
HEARTBEAT_REQUIRED_FREE_SPACE_PERCENTAGE = 20


try:
    from .local_settings import *
except ImportError:
    import warnings
    warnings.warn(
        'File local_settings.py not found.  You probably want to add it -- see README.md.'
    )
