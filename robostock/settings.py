from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dj7+a9w=g+9y7_(iihn%1b5vqgkr_@2c5e!)6(lue7(_*e-#)4')

# Set DEBUG based on environment variable; default True locally, set DEBUG=False in Railway
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Allow hosts defined in environment variable, default to '*' for wide access if not specified
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# Required for Django 4+ when using HTTPS tunnels like ngrok or Railway
# Auto-prepend https:// to any origin that is missing a scheme
# (e.g. if the Railway variable is set without the prefix)
_raw_origins = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'https://*.ngrok-free.app,https://*.ngrok-free.dev,https://*.railway.app'
).split(',')
CSRF_TRUSTED_ORIGINS = [
    o.strip() if '://' in o else 'https://' + o.strip()
    for o in _raw_origins if o.strip()
]

# Proxy and Security settings for Railway/Production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG  # False in local dev (HTTP), True in production (HTTPS)
CSRF_COOKIE_SECURE = not DEBUG    # Same — avoids cookie issues over localhost HTTP


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'robostock.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'robostock.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- Cloudinary (persistent media storage for Railway) ---
# Set these three env vars in Railway's dashboard (Variables tab):
#   CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY':    os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

if all(CLOUDINARY_STORAGE.values()):
    # Production: store uploads on Cloudinary
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
# else: local dev keeps using MEDIA_ROOT on disk (no changes needed)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'dashboard'



# Email Configuration (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'bloombergairoboticslab@gmail.com'
EMAIL_HOST_PASSWORD = 'femeqwhipvsnftuv'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
