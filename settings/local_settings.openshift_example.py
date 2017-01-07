import os

SQLALCHEMY_DATABASE_URI = (
    'postgresql://{user}:{password}@{host}:{port}/esiclivre'
    .format(
        user=os.environ['OPENSHIFT_POSTGRESQL_DB_USERNAME'],
        password=os.environ['OPENSHIFT_POSTGRESQL_DB_PASSWORD'],
        host=os.environ['OPENSHIFT_POSTGRESQL_DB_HOST'],
        port=os.environ['OPENSHIFT_POSTGRESQL_DB_PORT']))

ESIC_EMAIL = "{email}"
ESIC_PASSWORD = "{esic_password}"
FIREFOX_PATH = "../firefox/firefox"
DOWNLOADS_PATH = "/path/where/to/store/ff/downloads"
ATTACHMENT_URL_PREFIX = '{prefix}'
