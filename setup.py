#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

setup(
    name="esiclivre",
    version='0.1',
    description='Micro serviço para interação com o eSIC municipal de São Paulo.',
    author='Andrés M. R. Martano',
    author_email='andres@inventati.org',
    url='https://gitlab.com/ok-br/esiclivre',
    packages=["esiclivre"],
    install_requires=[
        # Main deps:
        # 'Flask',
        # 'Flask-Script',
        # 'Flask-Restplus==0.7.2',
        # 'Flask-CORS',
        # 'Flask-SQLAlchemy',
        # 'viratoken',
        # 'viralata',
        # 'selenium',
        # 'requests',
        # 'speechrecognition==2.2.0',
        # 'beautifulsoup4',
        # 'bleach',
        # 'sqlalchemy-utils',
        # 'arrow',
        # 'internetarchive',
        # 'psycopg2',  # for Postgres support
        'aniso8601==1.0.0',
        'arrow==0.7.0',
        'beautifulsoup4==4.4.1',
        'bleach==1.4.2',
        'blinker==1.4',
        'cffi==1.2.1',
        'cryptography==1.0.1',
        'docopt==0.6.2',
        'enum34==1.0.4',
        'Flask==0.10.1',
        'Flask-Cors==2.1.0',
        'Flask-Mail==0.9.1',
        'Flask-RESTful==0.3.4',
        'flask-restplus==0.7.2',
        'Flask-Script==2.0.5',
        'Flask-SQLAlchemy==2.0',
        'Flask-Migrate==1.6.0',
        'html5lib==1.0b8',
        'idna==2.0',
        'ipaddress==1.0.14',
        'itsdangerous==0.24',
        'Jinja2==2.6',
        'jsonpatch==0.4',
        'MarkupSafe==0.11',
        'oauthlib==1.0.3',
        'passlib==1.6.5',
        'psycopg2==2.6.1',
        'pyasn1==0.1.8',
        'pycparser==2.14',
        'PyJWT==1.4.0',
        'python-dateutil==2.4.2',
        'python-openid==2.2.5',
        'python-social-auth==0.2.12',
        'pytz==2015.4',
        'PyYAML==3.11',
        'requests==2.7.0',
        'requests-oauthlib==0.5.0',
        'selenium==2.48.0',
        'six==1.7.3',
        'SpeechRecognition==2.2.0',
        'SQLAlchemy==1.0.8',
        'SQLAlchemy-Utils==0.31.0',
        'Werkzeug==0.10.4',
        'wheel==0.24.0',
        'viratoken',
        'viralata',
    ],
    keywords=['esic', 'microservice'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Environment :: Web Environment",
        "Topic :: Internet :: WWW/HTTP",
    ]
)
