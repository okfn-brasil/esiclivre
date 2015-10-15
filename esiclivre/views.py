#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default

from multiprocessing import Process

import arrow
import bleach
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from flask.ext.restplus import Resource

from viralata.utils import decode_token
from cutils import date_to_json, paginate, ExtraApi

from models import Orgao, Author, PrePedido, Pedido, Message, Keyword
from extensions import db, sv


api = ExtraApi(version='1.0',
               title='EsicLivre',
               description='A microservice for eSIC interaction. All non-get '
               'operations require a micro token.')

api.update_parser_arguments({
    'text': {
        'location': 'json',
        'help': 'The text for the pedido.',
    },
    'orgao': {
        'location': 'json',
        'help': 'Orgao that should receive the pedido.',
    },
    'keywords': {
        'location': 'json',
        'type': list,
        'help': 'Keywords to tag the pedido.',
    },
})


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


@api.route('/messages')
class MessageApi(Resource):

    @api.doc(parser=api.create_parser('page', 'per_page_num'))
    def get(self):
        '''List messages by decrescent time.'''
        args = api.general_parse()
        page = args['page']
        per_page_num = args['per_page_num']
        messages = (db.session.query(Pedido, Message)
                    .options(joinedload('keywords'))
                    .filter(Message.pedido_id == Pedido.id)
                    .order_by(desc(Message.date)))
        # Limit que number of results per page
        messages, total = paginate(messages, page, per_page_num)
        return {
            'messages': [
                dict(msg_to_json(msg),
                     keywords=[kw.name for kw in pedido.keywords])
                for pedido, msg in messages
            ],
            'total': total,
        }


@api.route('/pedidos')
class PedidoApi(Resource):

    # @api.doc(parser=api.create_parser('page', 'per_page_num'))
    # def get(self):
    #     '''List pedidos by decrescent time.'''
    #     args = api.general_parse()
    #     page = args['page']
    #     per_page_num = args['per_page_num']
    #     pedidos = (db.session.query(Message, Pedido)
    #                .filter(Message.pedido_id == Pedido.id)
    #                .order_by(desc(Message.received)))
    #                # .distinct(Message.pedido_id))
    #     # Limit que number of results per page
    #     pedidos, total = paginate(pedidos, page, per_page_num)
    #     return {
    #         'pedidos': [pedido_to_json(pedido) for m, pedido in pedidos],
    #         'total': total,
    #     }

    @api.doc(parser=api.create_parser('token', 'text', 'orgao', 'keywords'))
    def post(self):
        '''Adds a new pedido to be submited to eSIC.'''
        args = api.general_parse()
        decoded = decode_token(args['token'], sv, api)
        author_name = decoded['username']

        text = bleach.clean(args['text'], strip=True)

        # Size limit enforced by eSIC
        if len(text) > 6000:
            api.abort_with_msg(400, 'Text size limit exceeded.', ['text'])

        # Validate 'orgao'
        if args['orgao']:
            orgao_exists = db.session.query(Orgao).filter_by(
                name=args['orgao']).count() == 1
            if not orgao_exists:
                api.abort_with_msg(400, 'Orgao not found.', ['orgao'])
        else:
            api.abort_with_msg(400, 'No Orgao specified.', ['orgao'])

        # Get author (add if needed)
        try:
            author_id = db.session.query(
                Author.id).filter_by(name=author_name).one()
        except NoResultFound:
            author = Author(name=author_name)
            db.session.add(author)
            db.session.commit()
            author_id = author.id

        pre_pedido = PrePedido(author_id=author_id, orgao_name=args['orgao'])

        # Set keywords
        for keyword_name in args['keywords']:
            # pedido.add_keyword(keyword_name)
            try:
                keyword = (db.session.query(Keyword)
                           .filter_by(name=keyword_name).one())
            except NoResultFound:
                keyword = Keyword(name=keyword_name)
                db.session.add(keyword)
                db.session.commit()
        pre_pedido.keywords = ','.join(k for k in args['keywords'])
        pre_pedido.text = text
        pre_pedido.state = 'WAITING'
        pre_pedido.created_at = arrow.now()

        db.session.add(pre_pedido)
        db.session.commit()
        # TODO: o que retornar aqui?
        # return pedido_to_json(pedido)
        return {'status': 'ok'}


@api.route('/pedidos/protocolo/<int:protocolo>')
class GetPedidoProtocolo(Resource):

    def get(self, protocolo):
        '''Returns a pedido by its protocolo.'''
        try:
            pedido = (db.session.query(Pedido)
                      .options(joinedload('history'))
                      .options(joinedload('keywords'))
                      # .order_by('Message.date')
                      .filter_by(protocol=protocolo).one())
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


@api.route('/keywords/<string:keyword_name>')
class GetPedidoKeyword(Resource):

    def get(self, keyword_name):
        '''Returns pedidos marked with a specific keyword.'''
        try:
            pedidos = (db.session.query(Keyword)
                       .options(joinedload('pedidos'))
                       .options(joinedload('pedidos.history'))
                       .filter_by(name=keyword_name).one()).pedidos
            # pedidos = (db.session.query(Pedido)
            #            .filter(Pedido.kw.contains(keyword_name)).all())
        except NoResultFound:
            pedidos = []
        return {
            'keyword': keyword_name,
            # 'pedidos': [pedido_to_json(pedido) for pedido in pedidos],
            # 'pedidos': sorted([pedido_to_json(pedido)
            #                    for pedido in pedidos],
            #                   key=lambda p: p['messages'][0]['received'],
            #                   reverse=True)
            'pedidos': [pedido_to_json(pedido)
                        for pedido in sorted(pedidos,
                        key=lambda p: p.request_date,
                        reverse=True)],
        }


@api.route('/pedidos/orgao/<string:orgao>')
class GetPedidoOrgao(Resource):

    def get(self, orgao):
        try:
            pedido = db.session.query(Pedido).filter_by(orgao=orgao).one()
        except NoResultFound:
            api.abort(404)
        return pedido_to_json(pedido)


# @api.route('/keywords/<string:keyword_name>')
# class GetKeyword(Resource):

#     def get(self, keyword_name):
#         '''Returns pedidos marked with a specific keyword.'''
#         try:
#             keyword = (db.session.query(Keyword)
#                        .filter_by(name=keyword_name).one())
#         except NoResultFound:
#             api.abort(404)
#         return {
#             'name': keyword.name,
#             'pedidos': [
#                 {
#                     'id': pedido.id,
#                     'protoloco': pedido.protocolo,
#                 }
#                 for pedido in keyword.pedidos
#             ]
#         }


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
                      .options(joinedload('pedidos'))
                      .filter_by(name=name).one())
        except NoResultFound:
            api.abort(404)
        return {
            'name': author.name,
            'pedidos': [
                {
                    'id': p.id,
                    'protocolo': p.protocol,
                    'orgao': p.orgao,
                    'situacao': p.situation(),
                    'deadline': date_to_json(p.deadline),
                    'keywords': [kw.name for kw in p.keywords],
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


@api.route('/prepedidos')
class PrePedidoAPI(Resource):

    def get(self):
        '''List PrePedidos.'''
        q = db.session.query(PrePedido, Author).filter_by(state='WAITING')
        q = q.filter(PrePedido.author_id == Author.id)

        return {
            'prepedidos': [{
                'text': p.text,
                'orgao': p.orgao_name,
                'created': date_to_json(p.created_at),
                'keywords': p.keywords,
                'author': a.name,
            } for p, a in q.all()]
        }


def set_captcha_func(value):
    '''Sets a captcha to be tried by the browser.'''
    api.browser.set_captcha(value)


def msg_to_json(msg):
    return {
        'text': msg.justification,
        'situacao': msg.situation,
        'responsavel': msg.responsible,
        # 'order': msg.order,
        'received': date_to_json(msg.date),
        # 'sent': date_to_json(msg.sent),
        # TODO: como colocar o anexo aqui? link para download?
    }


def pedido_to_json(pedido):
    '''Returns detailed information about a pedido.'''
    return {
        'id': pedido.id,
        'protocolo': pedido.protocol,
        'orgao': pedido.orgao.name,
        'author': pedido.author.name,
        'situacao': pedido.situation,
        'description': pedido.description,
        'date': date_to_json(pedido.request_date),
        'deadline': date_to_json(pedido.deadline),
        'keywords': [k.name for k in pedido.keywords],
        'messages': [msg_to_json(m)
                     for m in sorted(pedido.history, key=lambda m: m.date)],
    }
