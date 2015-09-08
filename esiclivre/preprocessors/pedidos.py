# coding: utf-8

import collections
import logging

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)


class DynamicLink(object):

    _request_headers = {
        "Host": "esic.prefeitura.sp.gov.br",
        "User-Agent": "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101  Firefox/28.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "http://esic.prefeitura.sp.gov.br/detalhes_pedido_v2.aspx",
        "Connection": "keep-alive",
        # "Content-Type": "application/x-www-form-urlencoded",
        # "Content-Length": 8836,
    }

    def __init__(self, request_url, cookies):

        self._request_url = request_url
        self._request_headers.update({
            "Referer": request_url,
            "Cookie": self.get_parsed_cookies(cookies)
        })

    def get_parsed_cookies(self, cookies):
        return u'{sessionid_key}={sessionid_value}; {aspxauth_key}={aspxauth_value}'.format(
            sessionid_key=cookies[0]['name'],
            sessionid_value=cookies[0]['value'],
            aspxauth_key=cookies[1]['name'],
            aspxauth_value=cookies[1]['value']
        )


class Attachment(DynamicLink):

    def __init__(self, bsoup_form, bsoup_input, request_url, cookies):

        self._bsoup_form = bsoup_form
        self._bsoup_input = bsoup_input
        super(Attachment, self).__init__(request_url, cookies)

    def get_action(self):
        return {self._bsoup_input.get('id'): self._bsoup_input.get('value')}

    def get_params(self):

        input_tags = filter(
            lambda i: i.get('type') == 'hidden',
            self._bsoup_form.select('input')
        )

        return {i.get('name'): i.get('value') for i in input_tags}


    def get_attachment(self):

        url = self._request_url
        headers = self._request_headers
        data = dict(
            list(self.get_action().items()) + list(self.get_params().items())
        )

        return requests.post(url=url, headers=headers, data=data, stream=True)


class Pedido(object):

    def __init__(self, raw_data, browser):

        # Webdriver
        self._browser = browser

        # full page source
        self._raw_data = BeautifulSoup(raw_data)

        # content of a 'pedido'
        self._main_data = self._raw_data.select('.pd_conteudo')[0]

        # the general information about a 'pedido'
        self._details = self._main_data.select(
            '#ctl00_MainContent_dtv_pedido')[0]

        # attachment (e.g. a detailed answer)
        self._attachemnt = self._main_data.select(
            '#ctl00_MainContent_grid_anexos_resposta')
        self._attachemnt = self._attachemnt[0] if self._attachemnt else None

        # the pedido's situation since the receivement until now
        self._situation = self._main_data.select('#fildSetSituacao')[0]

        # all the answers and/or updates.
        self._history = self._main_data.select(
            '#ctl00_MainContent_grid_historico')[0]

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

    @property
    def attachment(self):

        if self._attachemnt is None:
            return 'Sem anexos.'

        data = self._attachemnt.tbody.select('tr')[1:]
        if not data or not any([i.text.split() for i in data]):
            return 'Sem anexos.'

        result = ()
        for item in data:
            filename, created_at, fileid = item.select('td')
            attachment = collections.namedtuple(
                'PedidoAttachment', ['filename', 'created_at', 'fileid'])

            attachment.filename = filename.text
            attachment.created_at = created_at.text
            attachment.fileid = fileid.input.get('id')

            result += (attachment,)
        return result

    @property
    def situation(self):
        data = self._situation.tbody.select('tr')[0]
        _, situation = data.select('td')[:2]
        return situation.text

    @property
    def history(self):

        # get the 2th to skip header...
        data = self._history.tbody.select('tr')[1:]

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

        self._full_data = browser.navegador.find_element_by_id(
            'ctl00_MainContent_grid_pedido')

        total_of_pedidos = len(self._full_data.find_elements_by_tag_name('a'))
        for pos in range(total_of_pedidos):

            self._full_data = browser.navegador.find_element_by_id(
                'ctl00_MainContent_grid_pedido')

            self._full_data.find_elements_by_tag_name('a')[pos].click()

            self._pedido_pagesource.append(browser.navegador.page_source)

            browser.ir_para_consultar_pedido()

    def get_pedidos(self, browser):

        self._pedidos = [Pedido(pp, browser) for pp in self._pedido_pagesource]
        return self._pedidos
