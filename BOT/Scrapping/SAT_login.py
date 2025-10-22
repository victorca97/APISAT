import time
from playwright.sync_api import Page
from datetime import datetime
from difflib import SequenceMatcher
from utils.loggers import Registrador
from utils.common import *

from middleware.re_email import enviar_email_Api

class SatScraper:
    def __init__(self, page: Page):
        self.page = page


    def login(self, usuario, contrasenia):
        self.page.get_by_placeholder("Usuario").fill(usuario)
        self.page.get_by_placeholder("Contraseña").fill(contrasenia)
        with self.page.expect_navigation(wait_until='load'):
            self.page.locator("#form1 > div:nth-child(9) > div:nth-child(3) > button").click()
        time.sleep(2)

        with self.page.expect_navigation(wait_until='load'):
            self.page.locator("input[name='ImageButton2']").click()
        
        time.sleep(2)

    def iniciar_inscripcion(self, placa,inmatriculaciones):
        try:
            lista_placas=self.page.evaluate(f'Array.from(document.querySelectorAll("#dgDeclaraciones > tbody > tr > td:nth-child(4)")).map(li => li.innerText)')
            print(f"Listado de placas : {lista_placas}")
            if placa in  lista_placas:
                Registrador.info(f"La placa: {placa} ya ha sido registrada anteriormente")
                return 1
            else:
                print(f"La placa: {placa} no se ha registrado anteriormente. Iniciando proceso...")
                self.page.locator("input[name='txtPLaca']").fill(placa)

                with self.page.expect_navigation(wait_until='load'):
                    self.page.locator("input[name='btnNuevo']").click()
                time.sleep(2)

                if self.page.locator("#lblMensajeServer").inner_text() == "":
                    self.page.go_back()
                    self.page.wait_for_load_state('load')
                    Registrador.info(f"La placa: {placa} ya ha sido registrada anteriormente en la parte de inscripcion")
                    return 1


                with self.page.expect_navigation(wait_until='load'):
                    self.page.locator("input[name='btnInscripcion']").click()        
                time.sleep(2)

                return 0

        except Exception as e:
            destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
            asunto=f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones}"
            error_message = f"""
                <p>Hubo un error al momento de procesar los datos del usuario ,contraseña o inscripcino de vehiculo</p>
                <p>Error: {e} </p>"""
            enviar_email_Api(destinos, asunto, error_message)


    # def verificarInscripcion(self):
    #     try:
    #         placa=self.page.locator("#txtPlaca").get_attribute("value")
    #         self.page.locator("#lblMensajeCondomino").inner_text()
    #         print(f"Esta placa no ha sido registrada anteriormente {placa}")
    #         return 1

    #     except:
    #         print(f"Esta placa {placa} ya esta inscrita")
    #         return 0