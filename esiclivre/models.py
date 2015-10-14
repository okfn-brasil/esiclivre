# coding: utf-8

from __future__ import unicode_literals  # unicode by default

import arrow
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils
from sqlalchemy.orm.exc import NoResultFound

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


class PrePedido(db.Model):

    __tablename__ = 'pre_pedido'

    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer)

    orgao_name = db.Column(db.String(255))

    text = db.Column(sa.UnicodeText())

    keywords = db.Column(db.String(255))  # separated by commas

    state = db.Column(db.String(255))  # WAITING or PROCESSED

    created_at = db.Column(sa_utils.ArrowType)

    updated_at = db.Column(sa_utils.ArrowType)

    @classmethod
    def get_all_pending(self):
        return self.query.filter_by(state='WAITING')

    @property
    def orgao(self):
        return Orgao.query.filter_by(name=self.orgao_name).one()

    @property
    def author(self):
        return Author.query.filter_by(id=self.author_id).one()

    @property
    def all_keywords(self):
        return [
            Keyword.query.filter_by(name=k).one()
            for k in self.keywords.split(',')  # noqa
        ]

    def create_pedido(self, protocolo, deadline):

        pedido = Pedido()

        pedido.protocol = protocolo
        pedido.deadline = deadline

        pedido.orgao = self.orgao
        pedido.author = self.author
        pedido.keywords = self.all_keywords

        pedido.description = self.text
        # pedido.request_date = datetime.datetime.today()
        pedido.request_date = arrow.utcnow()

        db.session.add(pedido)
        db.session.commit()

        # self.updated_at = datetime.datetime.today()
        self.updated_at = arrow.utcnow()
        self.state = 'PROCESSED'

        db.session.add(self)
        db.session.commit()


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
        "Message", secondary=pedido_messages, backref="pedido"
    )

    author = db.relationship(
        'Author', secondary=pedido_author, backref='pedidos', uselist=False
    )

    keywords = db.relationship(
        'Keyword', secondary=pedido_keyword, backref='pedidos'
    )

    attachments = db.relationship(
        'Attachment', secondary=pedido_attachments, backref='pedido'
    )

    def add_keyword(self, keyword_name):
        try:
            keyword = (db.session.query(Keyword)
                       .filter_by(name=keyword_name).one())
        except NoResultFound:
            keyword = Keyword(name=keyword_name)
            db.session.add(keyword)
            db.session.commit()
        self.keywords.append(keyword)


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

    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'),
                          nullable=False)


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
