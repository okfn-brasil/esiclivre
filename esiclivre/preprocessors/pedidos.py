# coding: utf-8
from __future__ import print_function

import collections
from pprint import pprint
import time

from bs4 import BeautifulSoup

from esiclivre import models


class Pedido(object):

    def __init__(self, raw_data, browser):

        self._browser = browser
        self._raw_data = raw_data
        self._main_data = self._get_main_data()

        if self._main_data:

            self._details = self._get_details()
            self.attachemnts = self._get_attachments()
            self.situation = self._get_situation()
            self.history = self._get_history()

    def _get_main_data(self):
        return self._raw_data.form

    def _get_details(self):
        return self._main_data.select('#ctl00_MainContent_dtv_pedido')[0]

    @property
    def protocol(self):
        data = self._details.tbody.select('tr')[0]
        _, protocolo = data.select('td')
        return protocolo.text.strip()

    @property
    def interessado(self):
        data = self._details.tbody.select('tr')[1]
        _, interessado = data.select('td')
        return interessado.text.strip()

    @property
    def opened_at(self):
        data = self._details.tbody.select('tr')[2]
        _, opened_at = data.select('td')
        return opened_at.text.strip()

    @property
    def orgao(self):
        data = self._details.tbody.select('tr')[3]
        _, orgao = data.select('td')
        return orgao.text.strip()

    @property
    def contact_option(self):
        data = self._details.tbody.select('tr')[4]
        _, option = data.select('td')
        return option.text.strip()

    @property
    def description(self):
        data = self._details.tbody.select('tr')[5]
        _, desc = data.select('td')
        return desc.text.strip()

    def _get_attachments(self):

        grid = self._main_data.select('#ctl00_MainContent_grid_anexos_resposta')
        if not grid:
            return ()  # 'Sem anexos.'
        else:
            grid = grid[0]

        data = grid.tbody.select('tr')[1:]
        if not data or not any([i.text.split() for i in data]):
            return ()  # 'Sem anexos.'

        result = ()
        for item in data:

            filename, created_at, fileid = item.select('td')

            attachment = collections.namedtuple(
                'PedidoAttachment', ['filename', 'created_at'])
            attachment.filename = filename.text.strip().lower()
            attachment.created_at = created_at.text.strip()

            upload_attachment_to_internet_archive(attachment.filename)

            result += (attachment,)
        return result

    def _get_situation(self):
        fieldset =  self._main_data.select('#fildSetSituacao')[0]
        data = fieldset.tbody.select('tr')[0]
        _, situation = data.select('td')[:2]
        return situation.text.strip()

    def _get_history(self):

        grid =  self._main_data.select('#ctl00_MainContent_grid_historico')[0]

        # get the 2th to skip header...
        data = grid.tbody.select('tr')[1:]

        result = ()
        for item in data:
            situation, justification, responsible = item.select('td')[1:]
            date = item.span

            history = collections.namedtuple(
                'PedidoHistory',
                ['situation', 'justification', 'responsible', 'date']
            )
            history.situation = situation.text.strip()
            history.justification = justification.text.strip()
            history.responsible = responsible.text.strip()
            history.date = date.text.strip()

            result += (history,)

        try:
            result = sorted(result, key=lambda h: h.date)
        except:
            pass

        return result


class Pedidos(object):

    _pedidos = []
    _pedido_pagesource = []

    def __init__(self, browser):

        self.set_full_data(browser)
        self.get_all_pages_source(browser)
        self.process_pedidos(browser)

    def set_full_data(self, browser):
        self._full_data = browser.navegador.find_element_by_id(
            'ctl00_MainContent_grid_pedido')

    def get_all_pages_source(self, browser):

        total_of_pedidos = len(self._full_data.find_elements_by_tag_name('a'))
        for pos in range(total_of_pedidos):

            self.set_full_data(browser)
            self._full_data.find_elements_by_tag_name('a')[pos].click()

            pagesource = BeautifulSoup(browser.navegador.page_source)
            self._pedido_pagesource.append(pagesource)

            if not pagesource.select('#ctl00_MainContent_grid_anexos_resposta'):
                browser.navegador.back()
                continue

            # a ideia era baixar os anexo apenas durante o processo de parsear
            # o codigo fonte, mas ainda estou com dificuldades para fazer
            # uma requisição valida para o servidor sem usar o selenium
            # Em um proximo refactoring esse processo pode ser feito em
            # durante o parsing do page source, background ou não.
            attachments = browser.navegador.find_element_by_id(
                'ctl00_MainContent_grid_anexos_resposta'
            )
            for attachment in attachments.find_elements_by_tag_name('input'):
                attachment.click()
            browser.navegador.back()


    def process_pedidos(self, browser, page_source=None):

        # Existe a possibilidade da pagina não retornar um codigo fonte valido
        # a classe que estrutura o pedido retornará None se o código
        # font não for valido...
        if page_source:
            pedido = Pedido(page_source, browser)
            self._pedidos.append(pedido) if pedido else None
        else:
            self._pedidos = list(filter(
                lambda p: p._main_data,
                map(lambda pp: Pedido(pp, browser), self._pedido_pagesource)
            ))

        return self._pedidos


def save_pedido_into_db(pre_pedido):

    # check if there is a object with the same protocol
    pedido = models.Pedido.query.filter(
        models.Pedido.protocolo == pre_pedido.protocol).first()
    if not pedido:
        pedido = models.Pedido()

    # TODO: O que fazer se o orgão não existir no DB?
    # por enquanto, nós vamos salvar o valor parseado
    orgao = models.Orgao.query.filter(
        models.Orgao.name == pre_pedido.orgao).first()
    if not orgao:
        orgao = pre_pedido.orgao
    pedido.orgao = orgao

    pedido.protocolo = int(pre_predido.protocol)
    # TODO: Como preencher o autor_id?
    # TODO: Como preencher o deadline?
    # TODO: Como preencher o kw (keyword)?

    # TODO: Confirmar se essa é a melhor maneira de tratar o estado
    # do pedido.
    pedido.state = 0 if pre_predido.situation == "recebido" else 1

    # TODO: mover o processo do pedido para uma segunda função
    # algo como: create_pedido_messages
    # nesse processo é necessário considerar o histórico do pedido.

    message = models.Message.query.filter(
        models.Message.pedido_id == pedido.id).first()
    if not message:
        message = models.Message()

    message.pedido_id = pedido.id
    message.received = pedido.created_at
    # TODO: Como preencher o sent?

    message.attachment = ','.join([a.filename for a in pre_pedido.attachemnts])

    pedido.messages = message

    db.session.add(message)
    db.session.add(pedido)
    db.session.commit()


def upload_attachment_to_internet_archive():
    pass


def update_pedidos_list(browser):
    pedidos = Pedidos(browser)
    for pedido in pedidos:
        save_pedido_into_db(pedido)
