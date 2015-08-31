import collections

from bs4 import BeautifulSoup


class Pedido(object):

    def __init__(self, raw_data):

        self._raw_data = BeautifulSoup(raw_data)
        self._main_data = self._raw_data.select('.pd_conteudo')[0]
        self._details = self._main_data.select(
            '#ctl00_MainContent_dtv_pedido')[0]
        self._attachemnt = self._main_data.select(
            '#ctl00_MainContent_pnlAnexosResposta')[0]
        self._situation = self._main_data.select('#fildSetSituacao')[0]
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
        data = self._attachemn.tbody.select('tr')[0]
        if not data.text.split():
            return 'Sem anexos.'
        _, attachment = data.select('td')
        return attachment.text


    @property
    def situation(self):
        data = self._situation.tbody.select('tr')[0]
        _, situation = data.select('td')[:2]
        return situation.text


    @property
    def history(self):

        # get the 2th to skip header...
        data = self._history.tbody.select('tr')[1]

        _, situation, justification = data.select('td')[1:3]
        date = data.span

        history = collections.namedtuple('PedidoHistory', ['situation', 'justification', 'date'])
        history.situation = situation.text
        history.justification = justification.text
        history.date = date.text

        return history


class Pedidos(object):

    def __init__(self, browser):

        self._full_data = browser.navegador.find_element_by_id(
            'ctl00_MainContent_grid_pedido')

        # total of 'pedidos'...
        total_of_pedidos = len(self._full_data.find_elements_by_tag_name('a'))

        pre_pedidos = []
        for pos in range(total_of_pedidos):

            self._full_data = browser.navegador.find_element_by_id(
                'ctl00_MainContent_grid_pedido')

            self._full_data.find_elements_by_tag_name('a')[pos].click()

            pre_pedidos.append(browser.navegador.page_source)

            browser.ir_para_consultar_pedido()

        self._pedidos = map(Pedido, pre_pedidos)
