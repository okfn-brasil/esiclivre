#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default

from flask.ext.script import Server, Manager, Shell

from esiclivre.app import create_app, db, sv


# manager = Manager(app)
manager = Manager(create_app)

manager.add_command('run', Server(port=5004))
manager.add_command('shell', Shell(make_context=lambda: {
    'app': manager.app,
    'db': db,
    'sv': sv,
    # 'browser': browser
}))


# @manager.command
# def run():
#     """Run in local machine."""
#     manager.app.run(port=5004)


@manager.command
def initdb():
    from models import Orgao
    db.drop_all()
    db.create_all()

    db.session.add(Orgao(name="A test"))
    db.session.add(Orgao(name="B test"))
    db.session.commit()


if __name__ == '__main__':
    manager.run()
