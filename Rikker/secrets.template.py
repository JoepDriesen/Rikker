"""
This file contains everything that should not be displayed in the
public source code repository.

"""
import os

# The directory containing the source code
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = False

# DATABASE SECTION
DATABASE_ENGINE = ''
DATABASE_NAME = ''
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

# SERVER DIRECTORIES
MEDIA_ROOT = ''
STATIC_ROOT = ''

# URLs that handles the files served from MEDIA_ROOT and STATIC_ROOT. Make sure to use a
# trailing slash.
MEDIA_URL = ''
STATIC_URL = ''

SITE_ID = 0