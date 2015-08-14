#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default

from extensions import db


class Orgao(db.Model):
    __tablename__ = 'orgao'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)


class Pedido(db.Model):
    __tablename__ = 'pedido'
    id = db.Column(db.Integer, primary_key=True)
    # Using name as string and not ID for orgao table, because I think the
    # orgaos may change at any moment...
    orgao = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'),
                          nullable=False)
    messages = db.relationship("Message", backref="pedido")
    protocolo = db.Column(db.Integer, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True, default=None)

    # State of this pedido
    # 0 - created, but not sent
    # 1 - sent, waiting reply from orgao
    state = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def get_new_pedidos(cls):
        return (db.session.query(cls).filter(cls.state == 0).all())

    def get_initial_message(self):
        # TODO: otimizar isso para carregar as msgs junto com o load do pedido?
        for message in self.messages:
            if message.order == 0:
                return message
        return None

    def initial_message_sent(self):
        self.state = 1


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    # Number of this message inside a pedido
    # 0 - the pedido itself (from user to orgao)
    # 1 - the first reply (from orgao to user)
    # 2 - the first appeal (from user to orgao)
    # 3 - the second reply (from orgao to user)
    # ...
    order = db.Column(db.Integer, nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'),
                          nullable=False)
    text = db.Column(db.Text, nullable=False)
    received = db.Column(db.DateTime, nullable=False)
    sent = db.Column(db.DateTime, nullable=True, default=None)
    attachment = db.Column(db.LargeBinary, nullable=True, default=None)


class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    comments = db.relationship("Pedido", backref="author")
