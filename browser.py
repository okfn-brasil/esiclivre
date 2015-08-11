#!/usr/bin/env python
# coding: utf-8

# -----------------------------------------------------------------------------
# Copyright 2014 Andrés Mantecon Ribeiro Martano
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

# from __future__ import unicode_literals  # unicode by default

import os
import requests
import shutil
import random
import time
from multiprocessing import Process, Manager
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import speech_recognition as sr

from extensions import db
from models import Entidades, Pedidos


class LoginNeeded(Exception):
    pass


class ESicLivre(object):

    def __init__(self, firefox=None, email=None, senha=None, pasta=None):
        """'firefox' é o caminho para o binário do Firefox a ser usado.
        'pasta' é o caminho para a pasta onde salvar os downloads."""
        self.firefox = firefox
        self.pasta = pasta
        self.email = email
        self.senha = senha

        self.navegador = None
        self.app = None

        manager = Manager()
        self.safe_dict = manager.dict()
        self.clear_captcha()
        self.stop()

        self.try_break_audio_captcha = True
        self.nome_audio_captcha = "somCaptcha.wav"
        self.recognizer = sr.Recognizer("pt-BR")

        self.user_agent = (
            "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:28.0)"
            " Gecko/20100101  Firefox/28.0"
        )
        self.base_url = 'http://esic.prefeitura.sp.gov.br'
        self.login_url = self.base_url + '/Account/Login.aspx'

    def config(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def esta_em_login(self):
        # Verifica se está na página de login
        return self.navegador.current_url == self.login_url

    def criar_navegador(self):
        """Retorna um navegador firefox configurado para salvar arquivos
        baixados em 'pasta'."""
        print("Configurando e iniciando navegador")
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference("browser.download.manager.showWhenStarting", False)
        fp.set_preference("browser.download.dir", self.pasta)
        tipos = "text/csv,audio/wav,audio/x-wav,image/jpeg"
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", tipos)
        # fp.set_preference("plugin.disable_full_page_plugin_for_types",
        #                   "image/jpeg")
        fp.set_preference("general.useragent.override", self.user_agent)
        # fp.set_preference('permissions.default.image', 1)
        # O binário do navegador deve estar na pasta firefox
        binary = FirefoxBinary(self.firefox)
        self.navegador = webdriver.Firefox(
            firefox_binary=binary, firefox_profile=fp
        )
        self.navegador.implicitly_wait(20)

    def ir_para_registrar_pedido(self):
        self.navegador.get(self.base_url + "/registrar_pedido_v2.aspx")

    def ir_para_consultar_pedido(self):
        self.navegador.get(self.base_url + "/consultar_pedido_v2.aspx")

    def ir_para_login(self):
        self.navegador.get(self.base_url + "/Account/Login.aspx")

    def transcribe_audio_captcha(self):
        print("Transcribing audio captcha...")
        audio_path = os.path.join(self.pasta, self.nome_audio_captcha)
        with sr.WavFile(audio_path) as source:
            audio = self.recognizer.record(source)
        try:
            return self.recognizer.recognize(audio)
        except LookupError:
            return None

    def baixar_audio_captcha(self):
        # Removes the last downloaded audio file, avoiding adding (1) to
        # the end of the file name
        cam_audio = os.path.join(self.pasta, self.nome_audio_captcha)
        try:
            os.remove(cam_audio)
        except (OSError, IOError):
            pass
        print("Downloading audio captcha...")
        # Esse número deve ser usado para evitar problemas com a cache
        n = random.randint(1, 400)
        link = self.base_url + "/Account/pgAudio.ashx?%s" % n
        self.navegador.get(link)
        time.sleep(3)
        while self.nome_audio_captcha + ".part" in os.listdir(self.pasta):
            time.sleep(1)

        # c = "ffmpeg -i {e} -ar 16000 {s} -y".format(e=cam_audio,
        #                                             s=cam_audio[:-4] + "2.wav")
        # os.system(c)

    def baixar_imagem_captcha(self):
        # Removes the last downloaded audio file, avoiding adding (1) to
        # the end of the file name
        cam_imagem = os.path.join(self.pasta, self.nome_audio_captcha)
        try:
            os.remove(cam_imagem)
        except (OSError, IOError):
            pass
        link = self.base_url + "/Account/pgImagem.ashx"
        # self.navegador.get(link)
        # time.sleep(3)
        # while self.nome_audio_captcha + ".part" in os.listdir(self.pasta):
        #     time.sleep(1)

        nome = 'ASP.NET_SessionId'
        cookie = self.navegador.get_cookie(nome)
        # cookie.pop('httpOnly')
        # cookie.pop('secure')
        # cookie.pop('expiry')
        headers = {
            'User-Agent': self.user_agent,
            # 'Host': 'esic.prefeitura.sp.gov.br',
            # Accept-Language: pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3
            # Accept-Encoding: gzip, deflate
            # 'Referer': self.base_url + '/Account/Login.aspx',
            # 'Connection': keep-alive

            # 'Cookie': 'ASP.NET_SessionId=dgsonyd4zczcipg2vs3xgn0l'
            'Cookie': '{0}={1}'.format(nome, cookie['value'])
        }

        r = requests.get(link, stream=True, headers=headers)
        r.raw.decode_content = True
        with open(os.path.join('static', 'captcha.jpg'), 'wb') as out_file:
            shutil.copyfileobj(r.raw, out_file)
        # return requests.get(link, stream=True, headers=headers)
        # return requests.get(link, stream=True, headers=headers,
        # cookies=cookie)

    def gerar_novo_captcha(self):
        self.navegador.find_element_by_id(
            "ctl00_MainContent_btnAtualiza").click()

    def clicar_login_entrar(self):
        self.navegador.find_element_by_id(
            "ctl00_MainContent_btnEnviar").click()

    def clicar_recorrer(self):
        self.navegador.find_element_by_id(
            "ctl00_MainContent_btnSolicitarEsclarecimento").click()

    def entrar_dados_login(self, captcha):
        params = {
            "ctl00_MainContent_txt_email": self.email,
            "ctl00_MainContent_txt_senha": self.senha,
            "ctl00_MainContent_txtValorCaptcha": captcha,
        }
        for k, v in params.items():
            element = self.navegador.find_element_by_id(k)
            element.clear()
            element.send_keys(v)

    def entrar_no_sistema(self, captcha):
        if not self.esta_em_login():
            self.ir_para_login()
        self.entrar_dados_login(captcha)
        self.clicar_login_entrar()

    def preparar_receber_captcha(self):
        self.ir_para_login()
        self.baixar_imagem_captcha()
        self.clear_captcha()

    def criar_dicio_entidades(self):
        """Cria o dicionário com as entidades e botões para selecioná-las.
        Precisa estar na página de 'Registrar Pedido'."""
        # Pega todos os elementos "options" dentro do seletor
        select = self.navegador.find_element_by_id(
            "ctl00_MainContent_ddl_orgao")
        options = select.find_elements_by_tag_name("option")
        # Cria dicionário (nome da entidade: elemento da interface que pode ser
        # clicado para selecioná-la). Exclui o primeiro item que é "Selecione".
        return dict([(i.text, i) for i in options[1:]])

    def entrar_com_texto_pedido(self, texto):
        textarea = self.navegador.find_element_by_id(
            "ctl00_MainContent_txt_descricao_solicitacao")
        textarea.clear()
        textarea.send_keys(texto)
        # Autorizar divulgação da pergunta
        self.navegador.find_element_by_id("ctl00_MainContent_rbdSim").click()

    def clicar_enviar_pedido(self):
        # Enviar pedido de informação
        # self.navegador.find_element_by_id("ctl00_MainContent_btnEnviarAntes").click()
        pass

    def check_login_needed(self):
        if self.esta_em_login():
            raise LoginNeeded

    # Funções Gerais

    def postar_pedido(self, entidade, texto):
        print("A")
        self.ir_para_registrar_pedido()
        print("B")
        self.check_login_needed()
        print("C")
        # TODO: testar se está na página de fazer pedido
        entidades = self.criar_dicio_entidades()
        print("D")
        # TODO: testar se entidade existe
        entidades[entidade].click()
        self.entrar_com_texto_pedido(texto)
        self.clicar_enviar_pedido()
        print("E")

        # Returns protocolo
        protocolo = self.navegador.find_element_by_id(
            "ctl00_MainContent_lbl_protocolo_confirmar"
        ).text
        # TODO: retornar prazo também!
        return protocolo

    def lista_de_entidades(self):
        self.ir_para_registrar_pedido()
        # TODO: ver se realmente está na página
        return self.criar_dicio_entidades().keys()

    def set_captcha(self, value):
        self.safe_dict['captcha'] = value

    def get_captcha(self):
        return self.safe_dict['captcha']

    def clear_captcha(self):
        self.safe_dict['captcha'] = ''

    def stop(self):
        process = Process(target=self.__stop_func__)
        process.start()

    def start(self):
        process = Process(target=self.__run__)
        process.start()

    def take_care_of_captcha(self):
        if not self.esta_em_login():
            self.ir_para_login()
        f = True
        while f:
            self.baixar_audio_captcha()
            captcha = self.transcribe_audio_captcha()
            captcha = captcha.replace("ver ", "v")
            captcha = captcha.replace(" ", "")
            print(captcha)
            if len(captcha) == 4:
                break
            else:
                self.gerar_novo_captcha()
        return captcha

    def __run__(self):
        if not self.safe_dict['running']:
            with self.app.app_context():
                print("STATE", self.safe_dict['running'])
                self.safe_dict['running'] = True
                self.criar_navegador()

                try:
                    self.preparar_receber_captcha()
                    # Main loop
                    while self.safe_dict['running']:
                        self.main_loop()
                        time.sleep(5)
                except:
                    raise
                finally:
                    self.navegador.quit()

    def __stop_func__(self):
        self.safe_dict['running'] = False

    # Subprocess Functions

    def main_loop(self):
        if self.try_break_audio_captcha:
            captcha = self.take_care_of_captcha()
        else:
            captcha = self.get_captcha()

        print("ZzzzZZzzzZZz", captcha)
        # If captcha is unset, needs to wait someone to set it
        # If is set, login
        if captcha:
            self.entrar_no_sistema(captcha)
            if not self.esta_em_login():
                try:
                    # Loads entidades list if empty
                    if not db.session.query(Entidades.name).all():
                        self.update_entidades_list()

                    counter = 0
                    while self.safe_dict['running']:
                        # Keep alive; for how long? ...
                        if counter == 120:
                            self.ir_para_registrar_pedido()
                            self.ir_para_consultar_pedido()
                            counter = 0

                        # Main function
                        self.active_loop()

                        counter += 1
                        time.sleep(5)

                except LoginNeeded:
                    pass
            self.preparar_receber_captcha()

    def active_loop(self):
        """Does routine stuff inside eSIC, like posting pedidos."""
        not_sent = db.session.query(Pedidos).filter(Pedidos.sent == None).all()
        for pedido in not_sent:
            print(pedido)
            protocolo, prazo = self.postar_pedido(pedido.entidade, pedido.text)
            pedido.protocolo = int(protocolo)
            pedido.sent = datetime.now()
            db.session.commit()
        # TODO: ver se quem quer recorrer
        # TODO: ver precisa olhar respostas aos pedidos
        print("Feito")

    def update_entidades_list(self):
        # Clear table
        db.session.query(Entidades).delete()
        # Add entidades from site
        for ent in self.lista_de_entidades():
            model_ent = Entidades(name=ent)
            db.session.add(model_ent)
        db.session.commit()
