#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default
import os

from flask.ext.script import Server, Manager, Shell

from esiclivre.app import create_app, db, sv


manager = Manager(create_app)

# manager.add_command('run', Server(port=5004))
manager.add_command('shell', Shell(make_context=lambda: {
    'app': manager.app,
    'db': db,
    'sv': sv,
    'browser': manager.app.browser
}))


@manager.command
def run(browserless=False):
    '''Run in local machine.'''
    # Allows disable browser by parameter
    if not browserless:
        # Avoids starting the browser when manager loads
        if (not manager.app.debug or
           os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
            # Starts browser
            manager.app.browser.start()
    manager.app.run(port=5004)


@manager.command
def initdb():
    from esiclivre.models import Orgao
    db.drop_all()
    db.create_all()

    db.session.add(Orgao(name='A test'))
    db.session.add(Orgao(name='B test'))
    db.session.commit()


if __name__ == '__main__':
    manager.run()
