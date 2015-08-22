#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default
from datetime import datetime
from multiprocessing import Process

from sqlalchemy.orm.exc import NoResultFound
from flask.ext.restplus import Resource, Api

from viralata.utils import decode_token

from models import Orgao, Author, Pedido, Message, Keyword
from extensions import db, sv


api = Api(version='1.0',
          title='EsicLivre',
          description='A microservice for eSIC interaction. All non-get '
          'operations require a micro token.')


@api.route('/orgaos')
class ListOrgaos(Resource):

    def get(self):
        '''List orgaos.'''
        return {
            "orgaos": [i[0] for i in db.session.query(Orgao.name).all()]
        }


@api.route('/captcha/<string:value>')
class SetCaptcha(Resource):

    def get(self, value):
        '''Sets a captcha to be tried by the browser.'''
        process = Process(target=set_captcha_func, args=(value,))
        process.start()
        return {}


@api.route('/pedidos/new')
class NewPedido(Resource):

    parser = api.parser()
    parser.add_argument('token', location='json')
    parser.add_argument('text', location='json')
    parser.add_argument('orgao', location='json')
    parser.add_argument('keywords', location='json', type=list)

    def post(self):
        '''Adds a new pedido to be submited to eSIC.'''
        args = self.parser.parse_args()
        decoded = decode_token(args['token'], sv, api)
        author_name = decoded['username']

        # TODO: validar text (XSS)
        text = args['text']
        # Size limit enforced by eSIC
        if len(text) > 6000:
            api.abort(400, "Text size limit exceeded")

        # Validate 'orgao'
        if args['orgao']:
            try:
                orgao = (db.session.query(Orgao.name)
                         .filter_by(name=args['orgao']).one())
            except NoResultFound:
                api.abort(400, "Orgao not found")
        else:
            api.abort(400, "No Orgao specified")

        # Get author (add if needed)
        try:
            author_id = (db.session.query(Author.id)
                         .filter_by(name=author_name).one())
        except NoResultFound:
            author = Author(name=author_name)
            db.session.add(author)
            db.session.commit()
            author_id = author.id

        now = datetime.now()
        pedido = Pedido(author_id=author_id, orgao=orgao)

        # Set keywords
        for keyword_name in args['keywords']:
            try:
                keyword = (db.session.query(Keyword)
                           .filter_by(name=keyword_name).one())
            except NoResultFound:
                keyword = Keyword(keyword_name)
                db.session.add(keyword)
                db.session.commit()
            pedido.keywords.append(keyword)

        db.session.add(pedido)
        db.session.commit()
        message = Message(pedido_id=pedido.id, received=now, text=text,
                          order=0)
        db.session.add(message)
        db.session.commit()
        return {}


@api.route('/pedidos/protocolo/<int:protocolo>')
class GetPedidoProtocolo(Resource):

    def get(self, protocolo):
        '''Returns a pedido by its protocolo.'''
        try:
            pedido = (db.session.query(Pedido)
                      .filter_by(protocolo=protocolo).one())
        except NoResultFound:
            api.abort(404)
        return pedido_to_json(pedido)


@api.route('/pedidos/id/<int:id_number>')
class GetPedidoId(Resource):

    def get(self, id_number):
        '''Returns a pedido by its id.'''
        try:
            pedido = db.session.query(Pedido).filter_by(id=id_number).one()
        except NoResultFound:
            api.abort(404)
        return pedido_to_json(pedido)


@api.route('/pedidos/keyword/<string:keyword_name>')
class GetPedidoKeyword(Resource):

    def get(self, keyword_name):
        ''' Returns a pedido by its keyword name '''
        try:
            pedido = db.session.query(Pedido).filter_by(kw=keyword_name).one()
        except NoResultFound:
            api.abort(404)
        return pedido_to_json(pedido)


@api.route('/pedidos/orgao/<string:orgao>')
class GetPedidoOrgao(Resource):

    def get(self, orgao):

        try:
            pedido = db.session.query(Pedido).filter_by(orgao=orgao).one()
        except NoResultFound:
            api.abort(404)
        return pedido_to_json(pedido)


@api.route('/keywords/<string:keyword_name>')
class GetKeyword(Resource):

    def get(self, keyword_name):
        '''Returns pedidos marked with a specific keyword.'''
        try:
            keyword = (db.session.query(Keyword)
                       .filter_by(name=keyword_name).one())
        except NoResultFound:
            api.abort(404)
        return {
            'name': keyword.name,
            'pedidos': [
                {
                    'id': pedido.id,
                    'protoloco': pedido.protocolo,
                }
                for pedido in keyword.pedidos
            ]
        }


@api.route('/keywords')
class ListKeywords(Resource):

    def get(self):
        '''List keywords.'''
        keywords = db.session.query(Keyword.name).all()

        return {
            "keywords": [k[0] for k in keywords]
        }


@api.route('/authors/<string:name>')
class GetAuthor(Resource):

    def get(self, name):
        '''Returns pedidos marked with a specific keyword.'''
        try:
            author = (db.session.query(Author)
                      .filter_by(name=name).one())
        except NoResultFound:
            api.abort(404)
        return {
            'name': author.name,
            'pedidos': [
                {
                    'id': p.id,
                    'protocolo': p.protocolo,
                    'orgao': p.orgao,
                    'state': p.get_state(),
                    'deadline': format_date(p.deadline),
                    'keywords': list(p.kw),
                }
                for p in author.pedidos
            ]
        }


@api.route('/authors')
class ListAuthors(Resource):

    def get(self):
        '''List authors.'''
        authors = db.session.query(Author.name).all()

        return {
            "authors": [a[0] for a in authors]
        }


def set_captcha_func(value):
    '''Sets a captcha to be tried by the browser.'''
    api.browser.set_captcha(value)


def format_date(date):
    '''Helper to format dates.'''
    if date:
        return date.strftime("%d/%m/%Y")
    else:
        return None


def pedido_to_json(pedido):
    '''Returns detailed information about a pedido.'''
    return {
        'id': pedido.id,
        'protocolo': pedido.protocolo,
        'orgao': pedido.orgao,
        'autor': pedido.author.name,
        'state': pedido.get_state(),
        'deadline': format_date(pedido.deadline),
        'keywords': pedido.kw,
        'messages': [
            {
                'text': m.text,
                'order': m.order,
                'received': format_date(m.received),
                'sent': format_date(m.sent),
                # TODO: como colocar o anexo aqui? link para download?
            }
            # TODO: precisa dar sort?
            for m in pedido.messages
        ]
    }
