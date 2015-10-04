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
        'Flask',
        'Flask-Script',
        'Flask-Restplus',
        'Flask-CORS',
        'Flask-SQLAlchemy',
        'viratoken',
        'viralata',
        'selenium',
        'requests',
        'speechrecognition==2.2.0',
        'beautifulsoup4',
        'bleach'
        'sqlalchemy-utils',
        'arrow',
        # psycopg2, # for Postgres support
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
