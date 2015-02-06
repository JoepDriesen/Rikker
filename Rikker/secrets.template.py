"""
This file contains everything that should not be displayed in the
public source code repository.

"""
import os

# The directory containing the source code
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

# DATABASE SECTION
DATABASE_ENGINE = 'django.db.backends.sqlite3'
DATABASE_NAME = os.path.join(BASE_DIR, 'sqlite.db')
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

# SERVER DIRECTORIES
MEDIA_ROOT = '/tmp'
STATIC_ROOT = '/tmp'

# URLs that handles the files served from MEDIA_ROOT and STATIC_ROOT. Make sure to use a
# trailing slash.
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

SITE_ID = 1