import os


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('UWPath_Email_Account')
SERVER_EMAIL = os.environ.get('UWPath_Email_Account')
EMAIL_HOST = os.environ.get('UWPath_Host')
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('UWPath_Email_Account')
EMAIL_HOST_PASSWORD = os.environ.get('UWPath_Email_Password')
EMAIL_USE_TLS = True