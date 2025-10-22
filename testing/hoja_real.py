# si quiero que en caso cuando entre a algun  tipo de comprador salga error pase al siguiente y al final lo vuelva a hacer

import os
import time
import json

from playwright.sync_api import sync_playwright
from playwright.sync_api import Page
import traceback
import re

from datetime import datetime


#importar carpetas
from middleware.api_sat import obtener_datos_sat
from middleware.re_email import enviar_email_Api
from BOT.Scrapping.SAT_login import SatScraper 
from utils.loggers import Registrador
from utils.common import *
from BOT.Scrapping.tipos_persona import *
from dotenv import load_dotenv
load_dotenv()



def SAT():

    usuario = os.getenv('USER_SAT')
    contra = os.getenv('PASSWORD_SAT')
    enlace = os.getenv('URL_SAT')

    api_response_list = obtener_datos_sat()
    data_list = api_response_list


    with sync_playwright() as p:
        rutaDirUser = "\\Default"
        browser = p.chromium.launch_persistent_context(rutaDirUser, headless=False, accept_downloads=True)
        page = browser.new_page()
        satScrapper = SatScraper(page)

        try:
            page.goto(enlace)
            Registrador.info("BOT SAT-AUTOHUB INICIADO...........") 
            satScrapper.login(usuario, contra)
            Registrador.info("Logeado en SAT")

            for item in data_list:
                inmatriculaciones = item.get('inmatriculaciones', 'N/A')
                placa = item.get('placa', 'N/A')  # Asumiendo que también hay 'placa' en cada item
                print(f"Se va a procesar la inmatriculacion:{inmatriculaciones} con la placa:{placa}")
                Registrador.info(F"Se esta procesando la inmatriculacion {inmatriculaciones}, placa {placa}")
                
                VerificarPlaca=satScrapper.iniciar_inscripcion(placa, inmatriculaciones)
                if VerificarPlaca == 1:
                    Registrador.info(f"La placa: {placa} ya ha sido registrada anteriormente pasaremos a la siguiente inmatriculacion")
                    continue
                else:
                    
                    Registrador.info(f"inscripcion de la placa: {placa}")

                    try:
                        compradores_array = item.get('compradores', [])
                        print(compradores_array)
                        cantidad_compradores = len(compradores_array)
                        print(cantidad_compradores)
                        nombres_compradores_procesados = []
                        nombres_persona_socioconyugal =[]

                        procesado_compradores = False
                        
                        print(f"Valor predeterminado de procesado_compradores: {procesado_compradores}")

                        for comprador_info in compradores_array:
                            tipo_persona = comprador_info.get('tipoPersona')
                            print(f"Tipo de persona :{tipo_persona}" )
                            tieneRepresentante = comprador_info.get('tieneRepresentante')

                            if not procesado_compradores:
                                if tipo_persona == "1" and cantidad_compradores > 1:
                                    print(f"Iniciando procesamiento de {cantidad_compradores} compradores.")
                                    for i, comprador_info in enumerate(compradores_array):
                                        num_documento = comprador_info.get('numDocumento', None)
                                        nombres = comprador_info.get('nombres', '')
                                        apellido_paterno = comprador_info.get('apellidoPaterno', '')
                                        apellido_materno = comprador_info.get('apellidoMaterno', '')
                                        apellidos = f" {apellido_paterno} {apellido_materno}".strip()
                                        nombre_completo = f"{nombres}{apellidos}"

                                        print(f"Procesando comprador {i+1}: {nombre_completo} con documento: {num_documento}")

                                        if i == 0:
                                            inicio_comprador = True
                                        else:
                                            inicio_comprador = False

                                        if i > 0:
                                            agregarcompradores(page)
                                            
                                        print("Coompradores")
                                        Registrador.info("Es una persona con coompradores")
                                        natural_coocomprador(comprador_info, inicio_comprador,item,page,browser,inmatriculaciones,compradores_array)
                                        nombres_compradores_procesados.append(nombre_completo)

                                    procesado_compradores = True
                                    Registrador.info("Se acabo el proceso de coocmpradores")
                                    print(f"Terminado el procesamiento. Se procesaron {len(nombres_compradores_procesados)} compradores: {', '.join(nombres_compradores_procesados)}")
                                    break

                                elif tipo_persona == "1"  and cantidad_compradores == 1:
                                    Registrador.info("Es una persona Natural sin representate")
                                    for comprador_info in compradores_array:
                                        natural_sin_representante(comprador_info,item,page,browser,inmatriculaciones,compradores_array)
                                    procesado_compradores = True
                                    print(f"Cambie el bool: {procesado_compradores}")
                                    Registrador.info("Se acabo el proceso de la persona natural")
                                    break
                                    
                                elif tipo_persona == "2" and tieneRepresentante=="1":
                                    Registrador.info("Es una persona Juridica con representate")
                                    juridica_con_representante(comprador_info,item,page,browser,inmatriculaciones,compradores_array)
                                    procesado_compradores = True
                                    Registrador.info("Se acabo el proceso de la persona juridica con representate")
                                    break

                                elif tipo_persona == "3" and cantidad_compradores > 1:
                                    sociedadconyugal(comprador_info,item,page,browser,inmatriculaciones,compradores_array)
                                    procesado_compradores = True
                                    print(f"Cambie el bool: {procesado_compradores}")
                                    Registrador.info("Se acabo el proceso de la persona casada")
                                    break

                                elif tipo_persona == "6":
                                    Registrador.info("Es una persona con Patrimonio autonomo")
                                    patrimonioAutonomo(compradores_array)
                                    break
                                else:
                                    Registrador.error(f"No se encontró un caso para tipo_persona: {tipo_persona}, cantidad_compradores: {cantidad_compradores}, tieneRepresentante: {tieneRepresentante}")
                                    print(f"No se encontró un caso para tipo_persona: {tipo_persona}, cantidad_compradores: {cantidad_compradores}, tieneRepresentante: {tieneRepresentante}")
                                    break


                    except Exception as e:
                        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
                        asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones}"
                        error_message = f"<p>Hubo un error al procesar las inmatriculación. </p><p>Error: {e}</p><pre>{traceback.format_exc()}</pre>"
                        Registrador.error(f"Hubo un error al procesar la inmatriculación N°{inmatriculaciones}.")
                        print(traceback.format_exc())
                        #enviar_email_Api(destinos, asunto, error_message)
                    
                volver_a_inscripcion(page)

   
            
        except Exception as e:
            destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones}"
            error_message = f"<p>Hubo un error al iniciar sesión o navegar a la sección de trámites en el SAT.</p><p>Error: {e}</p>"
            #enviar_email_Api(destinos, asunto, error_message)
            print(e)
            Registrador.error(f"Hubo un error al iniciar sesión o navegar a la sección de trámites en el SAT. Error:{e}")   
        finally:
            browser.close()
            Registrador.info("Navegador cerrado.")  


SAT()