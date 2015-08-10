#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default

from datetime import datetime
from multiprocessing import Process

from sqlalchemy.orm.exc import NoResultFound
from flask.ext.restplus import Resource, Api, apidoc

from models import Entidades, Author, Pedidos
from extensions import db, sv


api = Api(version='1.0',
          title='esic',
          description='ESIC')


@api.route('/entidades')
class ListEntidades(Resource):

    def get(self):
        # a = [i[0] for i in db.session.query(Entidades.name).all()]
        # import IPython; IPython.embed()
        # return a
        return [i[0] for i in db.session.query(Entidades.name).all()]


@api.route('/captcha/<string:value>')
class SetCaptcha(Resource):

    def get(self, value):
        process = Process(target=set_captcha_func, args=(value,))
        process.start()
        return {}


@api.route('/pedidos/new')
class NewPedido(Resource):

    parser = api.parser()
    parser.add_argument('token', location='json')
    parser.add_argument('text', location='json')

    def post(self):
        args = self.parser.parse_args()
        try:
            decoded = sv.decode(args['token'])
        except:
            # TODO: tratar erros...
            raise
        author_name = decoded['username']

        # TODO: validar text (XSS)
        text = args['text']

        # Size limit enforced by eSIC
        if len(text) > 6000:
            api.abort(400, "Text size limit exceeded")

        # TODO: ver se é válida
        entidade = args['entidade']

        # author_name = "alguem"
        # text = """
        # """
        # entidade = u"CGM - Controladoria Geral do Município"

        # Get author (add if needed)
        try:
            author_id = (db.session.query(Author.id)
                         .filter(Author.name == author_name).one())
        except NoResultFound:
            author = Author(name=author_name)
            db.session.add(author)
            db.session.commit()
            author_id = author.id

        now = datetime.now()
        pedido = Pedidos(author_id=author_id, text=text,
                         entidade=entidade, received=now)
        db.session.add(pedido)
        db.session.commit()
        return {}


def set_captcha_func(value):
    api.browser.set_captcha(value)
