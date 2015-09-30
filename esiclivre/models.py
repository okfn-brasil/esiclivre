#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default

from sqlalchemy.ext.associationproxy import association_proxy

from extensions import db


pedido_keyword = db.Table(
    'pedido_keyword',
    db.metadata,
    db.Column('pedido_id', db.Integer, db.ForeignKey('pedido.id')),
    db.Column('keyword_id', db.Integer, db.ForeignKey('keyword.id'))
)


class PedidosUpdate(db.Model):

    __tablename__ = 'pedidos_update'
    id = db.Column(db.Integer, primary_key=True)

    last_update = db.Column(db.DateTime, nullable=False)
    total_of_updated = db.Column(db.Integer, nullable=True, default=0)


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
    author_id = db.Column(
        db.Integer, db.ForeignKey('author.id'), nullable=False)
    messages = db.relationship("Message", backref="pedido")
    protocolo = db.Column(db.Integer, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True, default=None)
    kw = association_proxy('keywords', 'name')
    # keywords = db.relationship("Keyword",
    #                           secondary=pedido_keyword,
    #                           backref="pedidos")

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

    def get_state(self):
        if self.state == 0:
            return "Waiting to be send"
        elif self.state == 1:
            return "Waiting reply"

        return "Unknown"


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
    attachment = db.Column(db.String(255), nullable=True, default='')


class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    pedidos = db.relationship("Pedido", backref="author")


class Keyword(db.Model):
    __tablename__ = 'keyword'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    pedidos = db.relationship("Pedido",
                              secondary=pedido_keyword,
                              backref="keywords")

    def __init__(self, name):
        self.name = name

    # def _find_or_create_tag(self, tag):
    #     q = Keyword.query.filter_by(name=tag)
    #     t = q.first()
    #     if not(t):
    #         t = Keyword(tag)
    #     return t

    # def _get_tags(self):
    #     return [x.name for x in self.tags]

    # def _set_tags(self, value):
    #     # clear the list first
    #     while self.tags:
    #         del self.tags[0]
    #     # add new tags
    #     for tag in value:
    #         self.tags.append(self._find_or_create_tag(tag))

    # str_tags = property(_get_tags,
    #                     _set_tags,
    #                     "Property str_tags is a simple wrapper for tags relation")
