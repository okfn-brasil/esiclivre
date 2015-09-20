# coding: utf-8
from __future__ import print_function

import collections
from pprint import pprint
import time

from bs4 import BeautifulSoup


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
        return protocolo.text

    @property
    def interessado(self):
        data = self._details.tbody.select('tr')[1]
        _, interessado = data.select('td')
        return interessado.text

    @property
    def opened_at(self):
        data = self._details.tbody.select('tr')[2]
        _, opened_at = data.select('td')
        return opened_at.text

    @property
    def orgao(self):
        data = self._details.tbody.select('tr')[3]
        _, orgao = data.select('td')
        return orgao.text

    @property
    def contact_option(self):
        data = self._details.tbody.select('tr')[4]
        _, option = data.select('td')
        return option.text

    @property
    def description(self):
        data = self._details.tbody.select('tr')[5]
        _, desc = data.select('td')
        return desc.text

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
            attachment.filename = filename.text
            attachment.created_at = created_at.text

            result += (attachment,)
        return result

    def _get_situation(self):
        fieldset =  self._main_data.select('#fildSetSituacao')[0]
        data = fieldset.tbody.select('tr')[0]
        _, situation = data.select('td')[:2]
        return situation.text

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
            history.situation = situation.text
            history.justification = justification.text
            history.responsible = responsible.text
            history.date = date.text

            result += (history,)

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

