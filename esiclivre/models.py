# coding: utf-8

from __future__ import unicode_literals  # unicode by default

import sqlalchemy as sa
import sqlalchemy_utils as sa_utils

from extensions import db


pedido_orgao = sa.Table(
    'pedido_orgao', db.metadata,
    db.Column('pedido_id', db.Integer, db.ForeignKey('pedido.id')),
    db.Column('orgao_id', db.Integer, db.ForeignKey('orgao.id'))
)

pedido_attachments = sa.Table(
    'pedido_attachments', db.metadata,
    db.Column('pedido_id', db.Integer, db.ForeignKey('pedido.id')),
    db.Column('attachment_id', db.Integer, db.ForeignKey('attachment.id'))
)

pedido_messages = sa.Table(
    'pedido_messages', db.metadata,
    db.Column('pedido_id', db.Integer, db.ForeignKey('pedido.id')),
    db.Column('message_id', db.Integer, db.ForeignKey('message.id'))
)

pedido_keyword = sa.Table(
    'pedido_keyword', db.metadata,
    db.Column('pedido_id', db.Integer, db.ForeignKey('pedido.id')),
    db.Column('keyword_id', db.Integer, db.ForeignKey('keyword.id'))
)

pedido_author = sa.Table(
    'pedido_author', db.metadata,
    db.Column('pedido_id', db.Integer, db.ForeignKey('pedido.id')),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'))
)


class PedidosUpdate(db.Model):

    __tablename__ = 'pedidos_update'

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(sa_utils.ArrowType, index=True)


class Pedido(db.Model):

    __tablename__ = 'pedido'

    id = db.Column(db.Integer, primary_key=True)

    protocol = db.Column(db.Integer, index=True, unique=True)

    interessado = db.Column(db.String(255))

    situation = db.Column(db.String(255), index=True)

    request_date = db.Column(sa_utils.ArrowType, index=True)

    contact_option = db.Column(db.String(255), nullable=True)

    description = db.Column(sa.UnicodeText())

    deadline = db.Column(sa_utils.ArrowType, index=True)

    orgao = db.relationship(
        'Orgao', secondary=pedido_orgao, backref='pedido', uselist=False
    )

    history = db.relationship(
        'Message', secondary=pedido_messages, backref='pedido'
    )

    author = db.relationship(
        'Author', secondary=pedido_author, backref='pedidos', uselist=False
    )

    keyword = db.relationship(
        'Keyword', secondary=pedido_keyword, backref='pedido', uselist=False
    )

    attachments = db.relationship(
        'Attachment', secondary=pedido_attachments, backref='pedido'
    )


class Orgao(db.Model):

    __tablename__ = 'orgao'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False, unique=True)


class Message(db.Model):

    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)

    situation = db.Column(db.String(255))

    justification = db.Column(sa.UnicodeText())

    responsible = db.Column(db.String(255))

    date = db.Column(sa_utils.ArrowType, index=True)


class Author(db.Model):

    __tablename__ = 'author'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False, unique=True)


class Keyword(db.Model):

    __tablename__ = 'keyword'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False, unique=True, index=True)


class Attachment(db.Model):

    __tablename__ = 'attachment'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)

    created_at = db.Column(sa_utils.ArrowType)

    ia_url = db.Column(sa_utils.URLType)
