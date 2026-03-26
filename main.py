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

                prioritarios_maquinarias = {100017827, 100018092}  # Set de inmatriculaciones prioritarias
                referencias_a_saltar = {100006404,100006419,100006434,100006434,100006519,100006522,100006553,100006554,100006562,
                                        100006586,100006587,100006623,100006654,100006654,100006662,100006768,100006768,100006772,100006790,100006800,
                                        100006817,100006820,100006886,100006958,100006958,100006998,100007008,100007019,100007185,100007324, 
                                        100007336,100007336,100007349,100007437,100007444,10000659,
                                        #Procesado por el cliente
                                       100006767,
                                       
                                       
                                       #Caso subsanado 100007035
                                        #Error en conyugal - ITEM 1
                                        100006466, 100006609,
                                        100006650,
                                        100007198,
                                        100007488,
                                        
                                        #Rafa dice que no se hacen
                                        100007467,100007425,100007415,

                                        #AUTOLAND, RECIBOS ANTES DE DICIEMBRE DEL 2025 - ITEM 4
                                        100006947,100006951,100006972,100006972,100006958,100006982,100006986,100006991,100007001,
                                        100007008, 100007010,100007032,

                                        #AUTOLAND, RECIBOS ANTES DE DICIEMBRE DEL 2025 ITEM 6
                                        100007191,100007210,100007225,100007247,100007272,100007295,100007309,100007322,100007418,
                                        100007428,100007438,100007440,100007480,
                                        
                                        #AUTOLAND COCOMPRADOR Y CASOS DE REVISAR RECIBOS JOSE REPORTARA MNN MELI
                                        100006797, 100006798, 100006800, 100006807, 100006810, 100006811,
                                        100006815, 100006816, 100006817, 100006818, 100006820,
                                        100006825, 100006832, 100006835, 100006846, 100006847, 100006851,
                                        100006852, 100006858, 100006861, 100006862, 100006873, 100006883,
                                        100006886, 100006892, 100006895, 100006897, 100006906, 100006913,
                                        100006926, 100006930, 100006865, 100006870, 100006877, 100006878, 100006879,
                                        100006880, 100006881, 100006888, 100006899, 100006905, 100006902,
                                        100006910, 100006912, 100006914, 100006919, 100007534, 100007538, 100007559,
                                        
                                        
                                        # AUTOLAND MES FEBRERO ITEM 1 cocomprador - casos con jose 100007532 como este que uno sea gran contribuyente y el otro no en conyugal
                                        100007500, 100007505, 100007517, 100007519, 100007521, 100007538, 100007559, 100007532,
                                        100007542, 100007558, 100007564, 100007577, 100007578, 100007625, 100007644,
                                        
                                        # Caso prueba TIGGO 2 PRO 1.5 CVT FULL FL 100007587
                                        # RECIBO ANTIGUO
                                        100007596, 100007611,
                                        
                                        
                                        # REVOSHOP ITEM 2/3 MALOS RECIBOS
                                        100003421, 100003423, 100003425, 100003426, 100003429, 100003430,
                                        100003434, 100003437, 100003438, 100003443, 100003444, 100003459,
                                        100003467, 100003470, 100003474, 100003477, 100003479, 100003480,
                                        100003484, 100003486, 100003487, 100003490, 100003491, 100003493,
                                        100003500, 
                                        
                                        # RECIBO ANTIGUO
                                        100003462, 100003463, 100003481,
                                        
                                        # CASOS REVISAR JOSE
                                        100003460, 100003472, 100003476,
                                        
                                        # MELI CONSULTA NOMBRE LARGO
                                        100003450,
                                
                                        # GRAN CONTRIBUYENTE - COBRANZA COACTIVA PERO SI COINCIDE CON EL RECIBO
                                        100003433, 100003448, 100003452, 100003454,
                                        
                                        # Correo invalido
                                        100003489,
                                        
                                        
                                        
                                        # NUEVO ITEM CASOS MAPEADOS
                                        # REVOSHOP ITEM 2/5 MALOS RECIBOS
                                        100003604, 100003611, 100003613, 100003621, 100003631, 100003634,
                                        100003646, 100003647, 100003648, 100003659, 100003632,                           
                                                         
                                                                                
                                        # RECIBO ANTIGUO
                                        100003605, 100003606, 100003618, 100003627, 100003630, 100003651,
                                        100003663, 100003665,                                   
                                                           
                                                                                
                                        # REVOSHOP COCOMPRADORS
                                        100003628,                           
                                                                                
                                        # CASOS REVISAR JOSE
                                       
                                        
                                        # GRAN CONTRIBUYENTE - COBRANZA COACTIVA PERO SI COINCIDE CON EL RECIBO
                                        
                                        
                                        
                                        # NUEVO ITEM CASOS MAPEADOS
                                        # EUROSHOP ITEM 1/3 MALOS RECIBOS
                                          100003806, 100003807,  100003808, 100003809, 100003811, 100003812, 100003814, 100003815,
                                          100003823, 100003824, 100003835,  100003838, 100003841, 100003843, 100003820, 100003836,
                                          100003842,    
                                                         
                                                                                
                                        # RECIBO ANTIGUO
                                        
                                                                                
                                        # REVOSHOP COCOMPRADORS
                                                                 
                                                                                
                                        # CASOS REVISAR JOSE
                                       
                                        
                                        # GRAN CONTRIBUYENTE - COBRANZA COACTIVA PERO SI COINCIDE CON EL RECIBO
                                        100003844,
                                        
                                        
                                        
                                        
                                        # NUEVO ITEM CASOS MAPEADOS
                                        # EUROSHOP ITEM 2/1 MALOS RECIBOS
                                        100004017, 100004024, 100004025, 100004029, 100004031, 100004032, 100004037,    
                                                         
                                                                                
                                        # RECIBO ANTIGUO
                                        
                                                                                
                                        # REVOSHOP COCOMPRADORS
                                                                 
                                                                                
                                        # CASOS REVISAR JOSE
                                       
                                        
                                        # GRAN CONTRIBUYENTE - COBRANZA COACTIVA PERO SI COINCIDE CON EL RECIBO
                                        100004020, 100004028,
                                        
                                        
                                        
                                        
                                        # NUEVO ITEM CASOS MAPEADOS
                                        # EUROSHOP ITEM 2/2 MALOS RECIBOS
                                        100004045, 100004049, 100004053, 100004057, 100004058,   
                                                         
                                                                                
                                        # RECIBO ANTIGUO
                                        100004041, 100004042, 100004043, 100004044, 100004055,
                                                                                
                                        # EUROSHOP COCOMPRADORS
                                                                 
                                                                                
                                        # CASOS REVISAR JOSE
                                       
                                        
                                        # GRAN CONTRIBUYENTE - COBRANZA COACTIVA PERO SI COINCIDE CON EL RECIBO
                                        100004052,
                                        
                                        
                                        
                                        
                                         # NUEVO ITEM CASOS MAPEADOS
                                        # EUROSHOP ITEM 2/5 MALOS RECIBOS
                                        100004158, 100004162, 100004165, 100004167, 100004168, 100004169, 100004173, 100004174,
                                        100004181, 100004183, 100004184, 100004186, 100004194, 100004196, 100004201,
                                        100004206, 100004212, 100004213, 100004214, 100004221, 100004211, 
                                                 
                                        # PRUEBA - 100004187     - 100004200        
                                                                                
                                        # RECIBO ANTIGUO
                                        100004161, 100004188, 100004189, 100004198, 100004202, 100004208, 100004215,
                                                                                
                                        # EUROSHOP COCOMPRADORS
                                        100004192,                         
                                                                                
                                        # CASOS REVISAR JOSE
                                        
                                        # PRUEBA LUNES 100017644 Q3 Dynamic TFSI 110 kW S tronic SI SE PUEDE HACER DICHO MODELO
                                        100004193,
                
                                        
                                        # GRAN CONTRIBUYENTE - COBRANZA COACTIVA PERO SI COINCIDE CON EL RECIBO
                                        100004176, 100004195, 100004207
                                        
                                        
                                        
                                        
                                        # MAQALFA
                                        
                                         }

                for item in data_list:
                    inmatriculaciones = item.get('inmatriculaciones', 'N/A')
                    referencia = item.get('referencia', '')
                    placa = item.get('placa', 'N/A')
                    
                    # A. Filtro de exclusión (Eliminamos los que no sirven)
                    if referencia in referencias_a_saltar:
                        Registrador.info(f"🔁 Referencia {referencia} está en la lista de exclusión. Saltando...")
                        continue
                    
                    # B. Filtro de prioridad (Solo procesamos los prioritarios)
                    if inmatriculaciones not in prioritarios_maquinarias:
                        print(f"Ignorando {inmatriculaciones} porque no es prioridad.")
                        continue
                    
                    # C. Procesamiento de prioridades
                    print(f"Procesando prioridad: {inmatriculaciones} con placa: {placa}")
                    Registrador.info(f"Se está procesando la inmatriculacion prioritaria {inmatriculaciones}, placa {placa}")
                    
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