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
            page.goto(enlace , timeout=500000)
            Registrador.info("BOT SAT-AUTOHUB INICIADO...........")
            
            # Buscamos el botón por su clase CSS ".close-btn" visible en tu captura
            # Le damos un timeout corto (ej. 5s) por si la web carga lento o el popup ya no sale
            if page.is_visible("button.close-btn"):
                page.click("button.close-btn")
                Registrador.info("Popup informativo cerrado correctamente.")
            else:
                Registrador.info("No se detectó el popup, continuando...")
            
            satScrapper.login(usuario, contra)
            Registrador.info("Logeado en SAT")

            # Bucle principal para reintento global
            max_reintentos = 2 # Número máximo de reintentos globales
            for intento_global in range(max_reintentos):
                Registrador.info(f"Iniciando intento global {intento_global + 1} de {max_reintentos}")
                errores_globales = []  
                inmatriculaciones_fallidas = []
                referencias_a_saltar = {100006404,100006419,100006434,100006434,100006519,100006522,100006553,100006554,100006562,
                                        100006586,100006587,100006623,100006654,100006654,100006662,100006768,100006768,100006772,100006790,100006800,
                                        100006817,100006820,100006886,100006958,100006958,100006998,100007008,100007019,100007185,100007324, 
                                        100007336,100007336,100007349,100007437,100007444, 100007035 ,10000659,
                                        #Procesado por el cliente
                                       100006767,

                                        #Error en conyugal - ITEM 1
                                        100006466, 100006609,


                                        100006650,
                                        100007198,
                                        100007488,
                                        
                                        #Rafa dice que no se hacen
                                        100007467,100007425,100007415,

                                        #AUTOLAND, RECIBOS ANTES DE DICIEMBRE DEL 2025 - ITEM 4
                                        100006947,100006951,100006972,100006972,100006958,100006982,100006986,100006991,100007001,
                                        100007008, 100007010,100007032,100007035,

                                        #AUTOLAND, RECIBOS ANTES DE DICIEMBRE DEL 2025 ITEM 6
                                        100007191,100007210,100007225,100007247,100007272,100007295,100007309,100007322,100007418,
                                        100007428,100007438,100007440,100007480
                                        

                                         }

                for item in data_list:
                    inmatriculaciones = item.get('inmatriculaciones', 'N/A')
                    referencia=item.get('referencia','')
                    placa = item.get('placa', 'N/A')  # Asumiendo que también hay 'placa' en cada item

                    if referencia in referencias_a_saltar:
                        Registrador.info(f"🔁 Referencia {referencia} está en la lista de exclusión. Saltando...")
                        continue

                    print(f"Se va a procesar la inmatriculacion: {inmatriculaciones} con la placa: {placa}")
                    Registrador.info(f"Se está procesando la inmatriculacion {inmatriculaciones}, placa {placa}")

                    VerificarPlaca = satScrapper.iniciar_inscripcion(placa, inmatriculaciones)
                    if VerificarPlaca == 1:
                        Registrador.info(f"La placa: {placa} ya ha sido registrada anteriormente, pasaremos a la siguiente inmatriculacion")
                        continue
                    else:
                            compradores_array = item.get('compradores', [])
                            print(compradores_array)
                            cantidad_compradores = len(compradores_array)
                            print(cantidad_compradores)
                            errores_locales = []  
                            nombres_compradores_procesados = []
                            nombres_persona_socioconyugal =[]

                            procesado_compradores = False
                            
                            print(f"Valor predeterminado de procesado_compradores: {procesado_compradores}")

                            for comprador_info in compradores_array:
                                tipo_persona = comprador_info.get('tipoPersona','1')
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
                                            natural_coocomprador(referencia,comprador_info, inicio_comprador,item,page,browser,inmatriculaciones,compradores_array)
                                            nombres_compradores_procesados.append(nombre_completo)

                                        procesado_compradores = True
                                        Registrador.info("Se acabo el proceso de coocmpradores")
                                        print(f"Terminado el procesamiento. Se procesaron {len(nombres_compradores_procesados)} compradores: {', '.join(nombres_compradores_procesados)}")
                                        break

                                    elif tipo_persona == "1"  and cantidad_compradores == 1:
                                        Registrador.info("Es una persona Natural sin representate")
                                        for comprador_info in compradores_array:
                                            natural_sin_representante(referencia,comprador_info,item,page,browser,inmatriculaciones,compradores_array)
                                        procesado_compradores = True
                                        print(f"Cambie el bool: {procesado_compradores}")
                                        Registrador.info("Se acabo el proceso de la persona natural")
                                        break
                                        
                                    elif tipo_persona == "2" and tieneRepresentante=="1":
                                        Registrador.info("Es una persona Juridica con representate")
                                        juridica_con_representante(referencia,comprador_info,item,page,browser,inmatriculaciones,compradores_array)
                                        procesado_compradores = True
                                        Registrador.info("Se acabo el proceso de la persona juridica con representate")
                                        break

                                    elif tipo_persona == "3" and cantidad_compradores > 1:
                                        sociedadconyugal(referencia,comprador_info,item,page,browser,inmatriculaciones,compradores_array)
                                        procesado_compradores = True
                                        print(f"Cambie el bool: {procesado_compradores}")
                                        Registrador.info("Se acabo el proceso de la persona casada")
                                        break

                                    elif tipo_persona == "6":
                                        Registrador.info("Es una persona con Patrimonio autonomo")
                                        #patrimonioAutonomo(compradores_array)
                                        break
                                    else:
                                        Registrador.error(f"No se encontró un caso para tipo_persona: {tipo_persona}, cantidad_compradores: {cantidad_compradores}, tieneRepresentante: {tieneRepresentante}")
                                        print(f"No se encontró un caso para tipo_persona: {tipo_persona}, cantidad_compradores: {cantidad_compradores}, tieneRepresentante: {tieneRepresentante}")
                                        break

                        
                            if errores_locales:
                                errores_globales.extend(errores_locales)
                                inmatriculaciones_fallidas.append(inmatriculaciones)
                                 # Construir el contenido del correo
                                destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
                                asunto = "ERROR BOT SAT-AUTOHUB: Inmatriculaciones no procesadas"
                                mensaje = """
                                <h1>Resumen de errores</h1>
                                <p>Se alcanzó el número máximo de reintentos. Algunas inmatriculaciones no se procesaron correctamente.</p>
                                """
                                # Agregar las inmatriculaciones no procesadas
                                if inmatriculaciones_fallidas:
                                    mensaje += "<h2>Inmatriculaciones no procesadas:</h2><ul>"
                                    for inmatriculacion in set(inmatriculaciones_fallidas):  # Usar `set` para evitar duplicados
                                        mensaje += f"<li>{inmatriculacion}</li>"
                                    mensaje += "</ul>"
                                else:
                                    mensaje += "<p>No se identificaron inmatriculaciones fallidas.</p>"

                                # Agregar los errores globales
                                if errores_globales:
                                    mensaje += "<h2>Errores globales:</h2><ul>"
                                    for error in errores_globales:
                                        mensaje += f"<li>{error}</li>"
                                    mensaje += "</ul>"
                                else:
                                    mensaje += "<p>No se registraron errores globales.</p>"
                                enviar_email_Api(destinos, asunto,mensaje)

                            # Volver a la pantalla de inscripción después de procesar todos los compradores
                            try:
                                volver_a_inscripcion(page)
                             
                                
                            except Exception as e:
                                Registrador.error(f"No se pudo regresar a la pantalla de inscripción. Error: {str(e)}")
                                errores_globales.append(f"Error al regresar a la pantalla de inscripción: {str(e)}")
                                inmatriculaciones_fallidas.append(inmatriculaciones)

               


                if errores_globales:
                    Registrador.error("Se alcanzó el número máximo de reintentos. Algunas inmatriculaciones no se procesaron correctamente.")
                    Registrador.error("Inmatriculaciones no procesadas:")
                    for inmatriculacion in set(inmatriculaciones_fallidas):  
                        Registrador.error(f"- Inmatriculación: {inmatriculacion}")
                    for error in errores_globales:
                        Registrador.error(error)

        except Exception as e:
            destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
            asunto = f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones}"
            error_message = f"<p>Hubo un error al iniciar sesión o navegar a la sección de trámites en el SAT.</p><p>Error: {e}</p>"
            Registrador.error(f"Hubo un error al iniciar sesión o navegar a la sección de trámites en el SAT. Error: {e}")
            print(traceback.format_exc())
            enviar_email_Api(destinos, asunto, error_message)
        

        finally:
            browser.close()
            Registrador.info("Navegador cerrado.")


SAT()