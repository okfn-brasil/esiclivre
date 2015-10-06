# coding: utf-8
from __future__ import print_function
import collections
import logging
import os
import string
import time

import bs4
import dateutil.parser
import flask
import internetarchive

from esiclivre import models, extensions


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
VALID_ATTACHMENTS_NAME_CHARS = string.lowercase + string.digits + '.-_'


class Pedido(object):

    def __init__(self, raw_data, browser):

        self._browser = browser
        self._raw_data = raw_data
        self._main_data = self._get_main_data()

        if self._main_data:

            self._details = self._get_details()
            self.attachemnts = self._get_attachments()
            self.situation = self._get_situation()
            self.request_date = self._get_request_date()
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

    def _get_request_date(self):
        data = self._details.tbody.select('tr')[2]
        _, opened_at = data.select('td')
        return dateutil.parser.parse(opened_at.text.strip(), dayfirst=True)

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

        grid = self._main_data.select(
            '#ctl00_MainContent_grid_anexos_resposta')

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
            attachment.filename = clear_attachment_name(filename.text)
            attachment.created_at = dateutil.parser.parse(
                created_at.text.strip(), dayfirst=True)

            upload_attachment_to_internet_archive(attachment.filename)

            print("anexo")
            print(attachment.filename)
            result += (attachment,)
        return result

    def _get_situation(self):
        fieldset = self._main_data.select('#fildSetSituacao')[0]
        data = fieldset.tbody.select('tr')[0]
        _, situation = data.select('td')[:2]
        return situation.text.strip()

    def _get_history(self):

        grid = self._main_data.select('#ctl00_MainContent_grid_historico')[0]

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

    def set_full_data(self, browser):
        self._full_data = browser.navegador.find_element_by_id(
            'ctl00_MainContent_grid_pedido')

    def get_all_pages_source(self, browser):

        total_of_pedidos = len(self._full_data.find_elements_by_tag_name('a'))
        for pos in range(total_of_pedidos):

            self.set_full_data(browser)
            self._full_data.find_elements_by_tag_name('a')[pos].click()

            pagesource = bs4.BeautifulSoup(browser.navegador.page_source)
            self._pedido_pagesource.append(pagesource)

            if not pagesource.select('#ctl00_MainContent_grid_anexos_resposta'):  # noqa
                browser.navegador.back()
                continue
            else:
                # a ideia era baixar os anexo apenas durante o processo de
                # parsear o codigo fonte, mas ainda estou com dificuldades
                # para fazer uma requisição valida para o servidor sem usar o
                # selenium. Em um proximo refactoring esse processo pode ser
                # feito em durante o parsing do page source, background ou não.
                attachments = browser.navegador.find_element_by_id(
                    'ctl00_MainContent_grid_anexos_resposta'
                )
                if attachments:
                    self.get_pedido_attachments(attachments)

            browser.navegador.back()
        fix_attachment_name_and_extension()

    def get_pedido_attachments(self, attachments):

        for attachment in attachments.find_elements_by_tag_name('input'):

            # baixar o arquivo
            # TODO: Ignorar arquivos que já existem? Como lidar com a
            # atualização de um anexo?
            attachment.click()

            # a ideia aqui é que se houver algum arquivo .part, ou seja, algum
            # download ainda não terminou, o processo aguarde até esses
            # arquivos serem baixados ou completar N tentativas

            max_retries = 0
            if '.part' in os.listdir(flask.current_app.config['DOWNLOADS_PATH']):  # noqa
                print("Existe algum download inacabado...")
                while max_retries != 10:

                    download_dir = os.listdir(
                        flask.current_app.config['DOWNLOADS_PATH']
                    )

                    uncomplete_download = next(
                        (arq for arq in download_dir if arq.endswith('.part')),
                        None
                    )

                    if not uncomplete_download:
                        print("Sem downloads inacabados...")
                        break
                    else:
                        print("Aguardar 1 segundo...")
                        time.sleep(1)
                        max_retries += 1

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

    def get_pedido(self, attribute, value):

        # obter o pedido atraves de um atributo
        # e.g. get_pedido(protocol, 12345)
        # pedido.protocol == 12345

        pedido = next(
            (p for p in self._pedidos if getattr(p, attribute, None) == value),
            None
        )

        return pedido

    def get_all_pedidos(self):
        return self._pedidos


def clear_attachment_name(name):

    name = name.strip().lower()

    return ''.join([l for l in name if l in VALID_ATTACHMENTS_NAME_CHARS])


def fix_attachment_name_and_extension():
    # remover caracter invalidos
    # mudar extensão para lowercase
    # apagar arquivos .part (nessa etapa, se um arquivo ainda é .part é porque
    # o download falhou).
    download_dir = flask.current_app.config['DOWNLOADS_PATH']
    for _file in os.listdir(download_dir):

        print("file: {}".format(_file))

        _file_fullpath = '{}/{}'.format(download_dir, _file)

        if _file.endswith('.part'):
            os.remove(_file_fullpath)
        else:
            os.rename(
                _file_fullpath,
                '{}/{}'.format(download_dir, clear_attachment_name(_file))
            )


def create_pedido_messages(pedido):
    pass


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

    # TODO: Como lidar se o author_id for nulo?
    if not pedido.author_id:
        pedido.author_id = models.Author.query.first().id

    pedido.protocolo = int(pre_pedido.protocol)
    # TODO: Como preencher o autor_id?
    # TODO: Como preencher o deadline?
    # TODO: Como preencher o kw (keyword)?

    # TODO: Confirmar se essa é a melhor maneira de tratar o estado
    # do pedido.
    pedido.state = 0 if pre_pedido.situation == "recebido" else 1

    pedido.messages = create_pedido_messages(pre_pedido)

    """
    for item in pre_pedido.history:
    message = models.Message.query.filter(
        models.Message.pedido_id == pedido.id).first()
    if not message:
        message = models.Message()

    message.pedido_id = pedido.id
    message.received = pre_pedido.request_date
    message.text = pre_pedido.description

    # TODO: Uma maneira mais racional para definir a ordem da mensagem
    # basicamente um historico com 1 item, contém apenas o item inicial
    # e , sendo assim, é de ordem 0

    order = len(pre_pedido.history)
    message.order = 0 if order < 2 else order

    # TODO: Como preencher o sent?

    message.attachment = ','.join([a.filename for a in pre_pedido.attachemnts])
    """

    extensions.db.session.add(message)
    extensions.db.session.add(pedido)
    extensions.db.session.commit()


def upload_attachment_to_internet_archive(filename):

    download_dir = flask.current_app.config['DOWNLOADS_PATH']
    downloaded_attachments = os.listdir(download_dir)

    if filename not in [a for a in downloaded_attachments]:
        print("Arquivo {!r} não existe!.".format(filename))
        # TODO: O que fazer se o arquivo não estiver disponivel?
        # Já temos um caso onde o download não completa, mas por falha no ser
        # vidor do esic.
    else:

        print("Enviar arquivo {!r} para o Internet Archive".format(filename))
        # TODO: implementar upload de arquivos para o IA
        """
        acces_key = flask.current_app.config['IA_ACCESS_KEY']
        secret_key = flask.current_app.config['IA_SECRET_KEY']

        item = internetarchive.Item('arquivos_esic')
        metada = dict(mediatype='pdf', creator='OKF')
        result = item.upload(
            '{}/{}'.format(download_dir, filename),
            metadata=metadata,
            acces_key=acces_key,
            secret_key=secret_key
        )

        if not result:
            print("Erro ao executar upload.")
        """



def update_pedidos_list(browser):

    # garantir que a tela inicial seja a de consulta de pedidos.
    browser.ir_para_consultar_pedido()

    pedidos = Pedidos()
    pedidos.set_full_data(browser)
    pedidos.get_all_pages_source(browser)
    pedidos.process_pedidos(browser)

    for pedido in pedidos.get_all_pedidos():
        save_pedido_into_db(pedido)
