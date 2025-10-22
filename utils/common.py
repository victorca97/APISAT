import os
import re
import base64
import json
from xhtml2pdf import pisa
from datetime import datetime
import time
from difflib import SequenceMatcher
from utils.loggers import Registrador
import requests
import traceback
from middleware.re_email import enviar_email_Api

def limpiar_iden(tipo_documento):
    #dni = tipo_documento.replace("D", "").strip()
    dni = re.sub(r'[^0-9]', '', tipo_documento).strip()
    return dni


def categoria(categoriaMtc):
    try:
        print(categoriaMtc)
        match categoriaMtc:
            case 'M1':
                return 1
            case 'M2':
                return 2
            case 'M3':
                return 3
            case 'N1' :
                return 4
            case 'N2':
                return 5
            case 'N3':
                return 6
            case _: return 1
    except Exception as e:
        print(e)


def value_moneda(moneda):

    print(moneda)
    if moneda == "USD":
        moneda=2
    elif moneda == "PEN":
        moneda=1

    return str(moneda)



def encontrar_combustible(combustible_code):
    try:
        print(combustible_code)
        match combustible_code:
            case 'ACE':
                return 18
            case 'BIL':
                return 6
            case 'BIE':
                return 8
            case 'BIN':
                return 7
            case 'BDS':
                return 17
            case 'CCO':
                return 13
            case 'DSL':
                return 2
            case 'DUL':
                return 9
            case 'DUE':
                return 11
            case 'DUN':
                return 10
            case 'ELT':
                return 22
            case 'ETA':
                return 15
            case 'FLX':
                return 16
            case 'GSL':
                return 1
            case 'GLP':
                return 14
            case 'GNL':
                return 13
            case 'GNV':
                return 12
            case 'HDB':
                return 20
            case 'HID':
                return 21
            case 'HGB':
                return 19
            case 'SOL':
                return 24
            case _:
                return 0 
    except Exception as e:
        print(e)

def encontrar_formulaRodante(formula_rodante_code):
    try:
        print(formula_rodante_code)
        match formula_rodante_code:
            case '4X2':
                return 1
            case '2WD':
                return 2
            case '4WD':
                return 3
            case '4X4':
                return 5
            case 'AWD':
                return 4
            case 'Quattro':
                return 6
            case _:
                return 99
    except Exception as e:
        print(e)


def encontrar_transmision(transmision):
    try:
        print(transmision)
        match transmision:
            case 'AUT':
                return 2
            case 'MEC':
                return 1
            case 'SMA':
                return 5
            case 'VC':
                return 6
            case _:
                return 4
    except Exception as e:
        print(e)



#Cambio de funcion encontrar_marca

def encontrar_marca(page, marca_usuario):
    # Mapeo personalizado de marcas
    MAPEO_MARCAS = {
        "MG": "MG",
        "LINXYS": "LINXYS"
    }

    try:
        # Aplicar mapeo si la marca está en el diccionario
        marca_a_buscar = MAPEO_MARCAS.get(marca_usuario.upper(), marca_usuario)
        print(f"Buscando marca: {marca_a_buscar}")

        time.sleep(2)

        # Verificar si existe la lista de marcas
        try:
            page.wait_for_selector("#ui-id-1 > li", timeout=6000)
            time.sleep(2)
            hay_lista = True
        except:
            print("❌ No se encontró la lista de marcas. Procediendo con 'OTRAS MARCAS'...")
            hay_lista = False

        # Si hay lista, hacer la búsqueda normal
        if hay_lista:
            opciones = page.query_selector_all("#ui-id-1 > li")
            lista_locator = [opcion.inner_text().strip() for opcion in opciones]
            print("Lista marcas disponibles:", lista_locator)
            print("Marca a buscar:", marca_a_buscar)

            best_match_ratio = -1
            best_match_index = -1
            best_match_value = None

            # Buscar mejor coincidencia
            for i, valor_marca in enumerate(lista_locator):
                matcher = SequenceMatcher(None, marca_a_buscar.upper(), valor_marca.upper())
                ratio = matcher.ratio()
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_index = i
                    best_match_value = valor_marca

            if best_match_value:
                if best_match_ratio >= 0.99:
                    print(f"✅ Coincidencia alta encontrada: '{best_match_value}' con ratio {best_match_ratio:.2f}")
                    indice_css = best_match_index + 1
                    page.click(f"#ui-id-1 > li:nth-child({indice_css})")
                    return best_match_value
                else:
                    print("⚠️ Baja coincidencia. Buscando 'OTRAS MARCAS'...")
            else:
                print("❌ Sin coincidencias. Forzando 'OTRAS MARCAS'...")
        else:
            print("⚠️ Lista no disponible. Forzando 'OTRAS MARCAS'...")

        # Bloque común para cuando hay que usar "OTRAS MARCAS"
        max_reintentos = 3
        encontrado = False
        intento = 0

        while not encontrado and intento < max_reintentos:
            intento += 1
            print(f"🔄 Reintento {intento} para encontrar 'OTRAS MARCAS'")
            variable_otras = "OTRAS MARCAS"

            # Limpiar y escribir en el campo de marca
            page.locator("#txtDesMarca").fill("")
            time.sleep(1)
            page.locator("#txtDesMarca").press_sequentially(variable_otras, delay=100)
            time.sleep(3)

            # Actualizar lista después de escribir
            try:
                opciones2 = page.query_selector_all("#ui-id-1 > li")
                lista_locator2 = [opcion.inner_text().strip() for opcion in opciones2]

                # Buscar "OTRAS MARCAS"
                for i, opcion in enumerate(opciones2):
                    texto = opcion.inner_text().strip()
                    if texto.upper() == "OTRAS MARCAS":
                        print("✅ Opción encontrada: OTRAS MARCAS")
                        indice_css = i + 1
                        page.click(f"#ui-id-1 > li:nth-child({indice_css})")
                        encontrado = True
                        break
            except Exception as e:
                print(f"⚠️ Error al buscar opciones: {e}")

            if not encontrado:
                print("No encontrado aún. Reintentando...")
                time.sleep(2)

        if encontrado:
            print("✅ 'OTRAS MARCAS' seleccionado correctamente.")
            
            # Marcar el checkbox #chkNueMarca si existe
            try:
                if page.locator("#chkNueMarca").is_visible():
                    page.locator("#chkNueMarca").check()
                    print("✅ Checkbox #chkNueMarca marcado")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ No se pudo marcar #chkNueMarca: {e}")
            
            # Llenar el campo de marca real si existe
            try:
                if page.locator("#txtDesMarcaReal").is_visible():
                    page.locator("#txtDesMarcaReal").fill("")
                    page.locator("#txtDesMarcaReal").press_sequentially(marca_a_buscar, delay=100)
                    print(f"✅ Campo #txtDesMarcaReal llenado con: {marca_a_buscar}")
            except Exception as e:
                print(f"⚠️ No se pudo llenar #txtDesMarcaReal: {e}")
            
            return variable_otras
        else:
            print("❌ No se pudo seleccionar 'OTRAS MARCAS' después de varios intentos.")
            return None

    except Exception as e:
        print(f"⚠️ Error al buscar marcas: {e}")
        return None
    

def encontrar_marca1(page, marca_usuario):
    # Mapeo personalizado de marcas
    MAPEO_MARCAS = {
        "MG": "MG",
        "LINXYS": "LINXYS"
    }

    try:
        # Aplicar mapeo si la marca está en el diccionario
        marca_a_buscar = MAPEO_MARCAS.get(marca_usuario.upper(), marca_usuario)
        print(f"Buscando marca: {marca_a_buscar}")

        time.sleep(2)

        # Verificar si existe la lista de marcas
        try:
            page.wait_for_selector("#ui-id-5 > li", timeout=6000)
            time.sleep(2)
            hay_lista = True
        except:
            print("❌ No se encontró la lista '#ui-id-5 > li'. Procediendo con 'OTRAS MARCAS'...")
            hay_lista = False

        # Si hay lista, hacer búsqueda normal
        if hay_lista:
            opciones = page.query_selector_all("#ui-id-5 > li")
            lista_locator = [opcion.inner_text().strip() for opcion in opciones]
            print("Lista marcas:", lista_locator)
            print("Marca a buscar:", marca_a_buscar)

            best_match_ratio = -1
            best_match_index = -1
            best_match_value = None

            # Buscar mejor coincidencia
            for i, valor_marca in enumerate(lista_locator):
                matcher = SequenceMatcher(None, marca_a_buscar.upper(), valor_marca.upper())
                ratio = matcher.ratio()
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_index = i
                    best_match_value = valor_marca

            if best_match_value:
                if best_match_ratio >= 0.99:
                    print(f"✅ Coincidencia alta encontrada: '{best_match_value}' con ratio {best_match_ratio:.2f}")
                    indice_css = best_match_index + 1
                    page.click(f"#ui-id-5 > li:nth-child({indice_css})")
                    return best_match_value
                else:
                    print("⚠️ Baja coincidencia. Forzando 'OTRAS MARCAS'...")
            else:
                print("❌ Sin coincidencias. Forzando 'OTRAS MARCAS'...")

        else:
            print("⚠️ Lista no disponible. Forzando 'OTRAS MARCAS'.")

        # Bloque común para cuando hay que usar "OTRAS MARCAS"
        max_reintentos = 5
        encontrado = False
        intento = 0

        while not encontrado and intento < max_reintentos:
            intento += 1
            print(f"🔄 Reintento {intento} para encontrar 'OTRAS MARCAS'")
            variable_otras = "OTRAS MARCAS"

            page.locator("#txtDesMarcaV").fill("")
            time.sleep(2)
            page.locator("#txtDesMarcaV").press_sequentially(variable_otras, delay=100)
            time.sleep(3)

            # Actualizar lista después de escribir
            opciones2 = page.query_selector_all("#ui-id-5 > li")
            lista_locator2 = [opcion.inner_text().strip() for opcion in opciones2]

            # Buscar "OTRAS MARCAS"
            for i, opcion in enumerate(opciones2):
                texto = opcion.inner_text().strip()
                if texto.upper() == "OTRAS MARCAS":
                    print("✅ Opción encontrada: OTRAS MARCAS")
                    indice_css = i + 1
                    page.click(f"#ui-id-5 > li:nth-child({indice_css})")
                    encontrado = True
                    break

            if not encontrado:
                print("⏳ No encontrado aún. Reintentando...")
                time.sleep(3)

        if encontrado:
            print("✅ 'OTRAS MARCAS' seleccionado correctamente.")
            return variable_otras
        else:
            print("❌ No se pudo seleccionar 'OTRAS MARCAS' después de varios intentos.")
            return None

    except Exception as e:
        print(f"⚠️ Error al buscar marcas: {e}")
        return None
    

def encontrar_carroceria(page,carroceria_buscada):

    page.wait_for_selector("#ddlCarroceria")
    page.locator("#ddlCarroceria").click()
    lista_carroceria = page.evaluate('Array.from(document.querySelectorAll("#ddlCarroceria > option")).map(option => option.text)')

    carroceria_mapping = {
        "ARE": "Arenero",
        "ART": "Articulado",
        "AMB": "Ambulancia",
        "BOM": "Bombero",
        "CAB": "Camión Grúa",
        "CAU": "Cañero",
        "CEL": "Celular",
        "CHM": "Chasis Motorizado",
        "CIG": "Cisterna",
        "COM": "Cisterna Combustibles",
        "COB": "Compactador",
        "CPT": "Competencia",
        "CMP": "Compresor",
        "RTV": "Comunicaciones",
        "CNV": "Convertible",
        "CPE": "Coupé",
        "CUA": "Cuatrimoto",
        "DOL": "Dolly",
        "ELV": "Elevador",
        "ASF": "Espaciador de Asfalto",
        "ORG": "Espaciador de Materia Orgánica",
        "EXP": "Explosivos",
        "FAC": "Factoría",
        "FUN": "Funerario",
        "FUR": "Furgón",
        "FRG": "Furgón Frigorífico",
        "TER": "Furgón Isotérmico",
        "GRA": "Granelero",
        "GEL": "Grupo Electrógeno",
        "GRU": "Grúa",
        "HBK": "Hatchback",
        "HOR": "Hormigonera",
        "HOS": "Hospital",
        "ILM": "Iluminador",
        "INS": "Instructor",
        "INT": "Intercambiador",
        "LIM": "Limusina",
        "LUB": "Lubricador",
        "MAD": "Madrina",
        "MEZ": "Mezclador",
        "MIC": "Microbús",
        "MIN": "Minibús",
        "MSD": "Moto Sidecar",
        "MTT": "Moto Todo Terreno",
        "MTO": "Motocicleta",
        "MUL": "Multifunción",
        "MPO": "Multipropósito",
        "OMI": "Omnibus Interurbano",
        "OMP": "Omnibus Panorámico",
        "OMN": "Omnibus Urbano",
        "OTR": "Otros Usos Especiales",
        "PAN": "Panel",
        "PER": "Perforador",
        "PUP": "Pick Up",
        "PLA": "Plataforma",
        "PCO": "Porta Contenedor",
        "POR": "Porta Tropas",
        "QUI": "Quilla",
        "REM": "Remolcador",
        "REG": "Remolcador Grúa",
        "RPV": "Reparaciones",
        "ROM": "Rompemetal",
        "SAN": "Sanitario",
        "SED": "Sedán",
        "SMG": "Station Wagon",
        "SUV": "Suv",
        "TCA": "Tanque Calorífico",
        "TCO": "Tanque Corrosivo",
        "CRI": "Tanque Criogénico",
        "TRF": "Tanque Frigorífico",
        "GLP": "Tanque GLP",
        "GNC": "Tanque GNC",
        "TIS": "Tanque Isotérmico",
        "TRA": "Transformador",
        "NAV": "Transporte de Naves",
        "TRM": "Triciclo Carga",
        "TRI": "Triciclo Pasajeros",
        "TRO": "Trolebús",
        "TUB": "Tubular",
        "VAL": "Valores",
        "FER": "Vehículo de Ferias",
        "VOL": "Volquete",
        "VFC": "Volquete Fuera de Carretera"
        # Agrega aquí más mapeos si es necesario
    }

    # Aplicar el mapeo si la carrocería buscada está en el diccionario
    if carroceria_buscada.upper() in carroceria_mapping:
        carroceria_buscada = carroceria_mapping[carroceria_buscada.upper()]



    cleaned_lista_carroceria = [op.strip().lower() for op in lista_carroceria]
    print("Lista carroceria original:", cleaned_lista_carroceria)
    best_match_ratio = -1
    best_match_index = -1
    best_match_value = None

    for i, opcion_limpia in enumerate(lista_carroceria):
        matcher = SequenceMatcher(None, carroceria_buscada, opcion_limpia)
        ratio = matcher.ratio()
        if ratio > best_match_ratio:
            best_match_ratio = ratio
            best_match_index = i
            best_match_value = lista_carroceria[i]  # Guardar el valor original

    if best_match_index != -1:
        opcion_a_seleccionar = lista_carroceria[best_match_index]
        print(f"Mejor coincidencia encontrada: {opcion_a_seleccionar} con ratio: {best_match_ratio}")
        return opcion_a_seleccionar
    else:
        print(f"No se encontró una coincidencia cercana para '{carroceria_buscada}'.")
        return None



def encontrar_modelo(page, modelos_buscado):
    """
    Busca y selecciona un modelo en una lista desplegable web (#ui-id-2).
    Usa `SequenceMatcher` para encontrar la mejor coincidencia:
    - Si el ratio ≥ 0.95 → Selecciona directamente
    - Si no hay ratio ≥ 0.95 pero hay alguna coincidencia → Muestra advertencia y selecciona la mejor
    - Si no hay coincidencias → Devuelve None

    :param page: Objeto page de Playwright
    :param modelos_buscado: Nombre del modelo a buscar
    :return: Nombre del modelo coincidente o None si no hay coincidencias
    """
    try:
        time.sleep(2)

        # Verificar si existe la lista de modelos
        try:
            page.wait_for_selector("#ui-id-2 > li", timeout=6000)
            time.sleep(10)
            hay_lista = True
        except:
            print("❌ No se encontró la lista de modelos. Procediendo con 'OTROS MODELOS'...")
            hay_lista = False

        # Si hay lista, hacer la búsqueda normal
        if hay_lista:
            opciones = page.query_selector_all("#ui-id-2 > li")
            lista_locator = [opcion.inner_text().strip() for opcion in opciones]
            print("Lista modelo:", lista_locator)
            print("Modelo a buscar:", modelos_buscado)

            best_match_ratio = -1
            best_match_index = -1
            best_match_value = None

            # Buscar mejor coincidencia
            for i, valor_modelo in enumerate(lista_locator):
                matcher = SequenceMatcher(None, modelos_buscado.upper(), valor_modelo.upper())
                ratio = matcher.ratio()
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_index = i
                    best_match_value = valor_modelo

            if best_match_value:
                if best_match_ratio >= 0.99:
                    print(f"✅ Coincidencia alta encontrada: '{best_match_value}' con ratio {best_match_ratio:.2f}")
                    indice_css = best_match_index + 1
                    page.click(f"#ui-id-2 > li:nth-child({indice_css})")
                    page.keyboard.press("Enter")
                    return best_match_value
                else:
                    print("⚠️ Baja coincidencia. Buscando 'OTROS MODELOS'...")
            else:
                print("❌ Sin coincidencias. Forzando 'OTROS MODELOS'...")
        else:
            print("⚠️ Lista no disponible. Forzando 'OTROS MODELOS'...")

        # Bloque común para cuando hay que usar "OTROS MODELOS"
        max_reintentos = 5
        encontrado = False
        intento = 0

        while not encontrado and intento < max_reintentos:
            intento += 1
            print(f"🔄 Reintento {intento} para encontrar 'OTROS MODELOS'")
            variableotros = "OTROS MODELOS"

            page.locator("#txtDesModelo").fill("")
            time.sleep(2)
            page.locator("#txtDesModelo").press_sequentially(variableotros, delay=700)
            time.sleep(5)

            # Actualizar lista después de escribir
            opciones2 = page.query_selector_all("#ui-id-2 > li")
            lista_locator2 = [opcion.inner_text().strip() for opcion in opciones2]

            # Buscar "OTROS MODELOS"
            for i, opcion in enumerate(opciones2):
                texto = opcion.inner_text().strip()
                if texto.upper() == "OTROS MODELOS":
                    print("✅ Opción encontrada: OTROS MODELOS")
                    indice_css = i + 1
                    page.click(f"#ui-id-2 > li:nth-child({indice_css})")
                    encontrado = True
                    break

            if not encontrado:
                print("No encontrado aún. Reintentando...")
                time.sleep(3)

        if encontrado:
            print("✅ 'OTROS MODELOS' seleccionado correctamente.")
            page.locator("#chkNueModelo").check()
            time.sleep(1)
            page.locator("#txtDesModeloReal").fill("")
            page.locator("#txtDesModeloReal").press_sequentially(modelos_buscado, delay=500)
            return variableotros
        else:
            print("❌ No se pudo seleccionar 'OTROS MODELOS' después de varios intentos.")
            return None

    except Exception as e:
        print(f"⚠️ Error al buscar modelos: {e}")
        return None

def agregarcompradores(page):

    page.go_back()
    page.locator("#btnRegresar").click()
    page.locator("#btnRegresar").click()
    page.locator("#dgDeclaraciones_lnkPorcentaje_0 > img").click()


def encontrar_modelo2(page, modelo_buscado):
    try:
        time.sleep(2)

        # Verificar si existe la lista de modelos
        try:
            page.wait_for_selector("#ui-id-6 > li", timeout=6000)
            time.sleep(10)
            hay_lista = True
        except:
            print("❌ No se encontró la lista '#ui-id-6 > li'. Procediendo con 'OTROS MODELOS'...")
            hay_lista = False

        # Si hay lista, hacer búsqueda normal
        if hay_lista:
            opciones = page.query_selector_all("#ui-id-6 > li")
            lista_locator = [opcion.inner_text().strip() for opcion in opciones]
            print("Lista modelo:", lista_locator)
            print("Modelo a buscar:", modelo_buscado)

            best_match_ratio = -1
            best_match_index = -1
            best_match_value = None

            # Buscar mejor coincidencia
            for i, valor_modelo in enumerate(lista_locator):
                matcher = SequenceMatcher(None, modelo_buscado.upper(), valor_modelo.upper())
                ratio = matcher.ratio()
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_index = i
                    best_match_value = valor_modelo

            if best_match_value:
                if best_match_ratio >= 0.99:
                    print(f"✅ Coincidencia alta encontrada: '{best_match_value}' con ratio {best_match_ratio:.2f}")
                    indice_css = best_match_index + 1
                    page.click(f"#ui-id-6 > li:nth-child({indice_css})")
                    return best_match_value
                else:
                    print("⚠️ Baja coincidencia. Forzando 'OTROS MODELOS'...")
            else:
                print("❌ Sin coincidencias. Forzando 'OTROS MODELOS'...")

        else:
            print("⚠️ Lista no disponible. Forzando 'OTROS MODELOS'.")

        # Bloque común para cuando hay que usar "OTROS MODELOS"
        max_reintentos = 5
        encontrado = False
        intento = 0

        while not encontrado and intento < max_reintentos:
            intento += 1
            print(f"🔄 Reintento {intento} para encontrar 'OTROS MODELOS'")
            variableotros = "OTROS MODELOS"

            page.locator("#txtDesModeloV").fill("")
            time.sleep(2)
            page.locator("#txtDesModeloV").press_sequentially(variableotros, delay=700)
            time.sleep(5)

            # Actualizar lista después de escribir
            opciones2 = page.query_selector_all("#ui-id-6 > li")
            lista_locator2 = [opcion.inner_text().strip() for opcion in opciones2]

            # Buscar "OTROS MODELOS"
            for i, opcion in enumerate(opciones2):
                texto = opcion.inner_text().strip()
                if texto.upper() == "OTROS MODELOS":
                    print("✅ Opción encontrada: OTROS MODELOS")
                    indice_css = i + 1
                    page.click(f"#ui-id-6 > li:nth-child({indice_css})")
                    encontrado = True
                    break

            if not encontrado:
                print("⏳ No encontrado aún. Reintentando...")
                time.sleep(3)

        if encontrado:
            print("✅ 'OTROS MODELOS' seleccionado correctamente.")
            return variableotros
        else:
            print("❌ No se pudo seleccionar 'OTROS MODELOS' después de varios intentos.")
            return None

    except Exception as e:
        print(f"⚠️ Error al buscar modelos: {e}")
        return None
    


def enviar_inmatriculacion(inmatriculacion,dni,archivo_domicilio,archivo_declaracionJurada):


    url_evniarDocumentos= os.getenv('URL_ENVIA_DOCUMENTOS')
    url= url_evniarDocumentos
    
    estructura= {
        "TramitId" : inmatriculacion,
        "cliente" : dni,
        "file" : archivo_domicilio,
        "file2" : archivo_declaracionJurada
    }

    try:

        Registrador.info(f"Enviando correo electrónico a la API: {url}")
        Registrador.debug(f"Estructura de la inmatriculacion : {estructura}")

        response = requests.post(url, json=estructura)
        if response.status_code == 200:
            Registrador.info(f"Inmatriculacion enviado exitosamente. Código de estado: {response.status_code}")
            Registrador.debug(f"Respuesta de la API: {response.json()}")
            return response
        elif response.status_code == 400:
            Registrador.error(f"Error al enviar la inmatriculacion. Código de estado: {response.status_code}. Verifique los datos enviados.")
            Registrador.debug(f"Respuesta de la API (error 400): {response.text}") # Imprime el cuerpo de la respuesta para más detalles
            return response
        else:
            response.raise_for_status()  # Lanza una excepción para otros códigos de estado HTTP erróneos (no 200 ni 400)

        Registrador.error(f"Se envio la inmatricualcionla N°{inmatriculacion} por el APISAT.")
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
        asunto = f"TEST BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion}"
        error_message = f"<p>Se envio la inmatricualcion N°{inmatriculacion} por el APISAT.</p>"
        enviar_email_Api(destinos,asunto,error_message)        
        
    except requests.exceptions.RequestException as e:
        Registrador.error(f"Error al enviar la inmatriculacion a la API: {e}")
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
        asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion}"
        error_message = f"<p>Hubo un error al enviar la inmatriculacion por el APISAT.</p><p>Error: {e}</p>"
        Registrador.error(f"Hubo un error al enviar la inmatriculacion por el APISAT. Error: {e}")
        print(traceback.format_exc())
        enviar_email_Api(destinos,asunto,error_message)
        return None  # Retornar None para indicar que hubo un error

    except Exception as e:
        Registrador.error(f"Error al enviar la inmatriculacion a la API: {e}")
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
        asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion}"
        error_message = f"<p>Hubo un error inesperado.</p><p>Error: {e}</p>"
        Registrador.error(f"Hubo un error inesperado. Error: {e}")
        print(traceback.format_exc())
        enviar_email_Api(destinos,asunto,error_message)
        Registrador.error(f"Error inesperado : {e}")
        return None




def Guardar_Archivos(page,browser,inmatriculacion,dni): 

    carpeta_base_proyecto = "./downloads"
    carpeta_inmatriculacion = os.path.join(carpeta_base_proyecto, str(inmatriculacion))
    os.makedirs(carpeta_inmatriculacion, exist_ok=True)

    # Define las rutas de los archivos de captura de pantalla
    archivo_delcaracion = os.path.join(carpeta_inmatriculacion, f"ArchivoDeclaracion_{inmatriculacion}_{dni}.pdf")
    archivo_cambioDomicilio = os.path.join(carpeta_inmatriculacion, f"ArchivoCambioDomicilio_{inmatriculacion}_{dni}.pdf")
    input("ver boton")
    with page.expect_navigation(wait_until='load'):
        page.locator("input[id='btnImpDJCamDom']").click()

    html_cambioDomicilio=page.inner_html("#form1 > div:nth-child(4)")

    with open(archivo_cambioDomicilio, "wb") as pdf:
        pisa_status = pisa.CreatePDF(html_cambioDomicilio, dest=pdf)
        if pisa_status.err:
            print("Error al generar el PDF CAMBIODOMICILIO")

    print(f"PDF del cambio domicilio guardado en: {archivo_cambioDomicilio}")
    Registrador.info(f"PDF del cambio domicilio guardado en: {archivo_cambioDomicilio}")


    with page.expect_navigation(wait_until='load'):
        page.locator("#btnRegresar").click()


    parte1=page.inner_html("#DivImpresion > table > tbody > tr > td > table:nth-child(1)")
    parte2=page.inner_html("#DivImpresion > table > tbody > tr > td > table:nth-child(2)")
    parte3=page.inner_html("#DivImpresion > table > tbody > tr > td > table:nth-child(3)")
    print()
    ruta_temporal_html = "temp_declaracion.html"
    ruta_pdf_declaracion = archivo_delcaracion  # Usar la ruta de archivo original

    # Crear un HTML minimalista con solo el contenido del div
                #<div style="padding: 40px;"></div>
    html_minimal = f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
    <html>

    <head>
        <style type="text/css">
            body {{
                margin-top: 30px;
                background-repeat: repeat;
                font-family: Verdana, Arial, Helvetica;
                font-size: 10px;
                background-color: lightgrey;
            }}
            tr{{
                FONT-SIZE: 10px;
                FONT-FAMILY: Arial;
            }}

            td{{
                FONT-SIZE: 10px;
                FONT-FAMILY: Arial;
            }}

            .style1{{
                width: 586px;
            }}

            .auto-style1{{
                width: 177px;
            }}

            .auto-style2{{
                height: 10px;
            }}

            .auto-style3{{
                width: 177px;
                height: 10px;
            }}
        </style>

    </head>

    <body>
        <form id="Form1">
            <table cellspacing="0" cellpadding="0" width="780" align="center" bgcolor="white" border="0">
                <tr>
                    <td>
                        <div id="DivImpresion" align="center">
                            <table width="750" bgcolor="White">
                                <tr>
                                    <td>
                                        <table width="98%">
                                            {parte1}
                                        </table>
                                        <table width="98%">
                                            {parte2}
                                        </table>
                                        <table width="98%">
                                            {parte3}
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        <br>
                    </td>
                </tr>
                <tr>
                    <td></td>
                </tr>
            </table>
        </form>
    </body>

    </html>"""

    # Guardar el HTML temporalmente (opcional, pero útil para depurar)
    with open(ruta_temporal_html, "w", encoding="utf-8") as f:
        f.write(html_minimal)

    # Crear una nueva página y establecer el contenido
    nueva_pagina = browser.new_page()
    nueva_pagina.set_content(html_minimal)

    # Guardar la nueva página como PDF
    nueva_pagina.pdf(path=ruta_pdf_declaracion, format="A4", print_background=False)
    #print(f"PDF de declaracion guardado (solo #DivImpresion) en: {ruta_pdf_declaracion}")


    nueva_pagina.close()
    print(f"PDF de declaracion guardado en: {archivo_delcaracion}")
    Registrador.info(f"PDF de declaracion guardado en: {archivo_delcaracion}")


    try:
        with open(archivo_delcaracion, 'rb') as archivo_delcaracion_file:
            archivo_delcaracion_bytes = archivo_delcaracion_file.read()
            archivo_delcaracion_base64 = base64.b64encode(archivo_delcaracion_bytes).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de declaración en: {archivo_delcaracion}")
    except Exception as e:
        print(f"Error al leer el archivo de declaración: {e}")

    try:
        with open(archivo_cambioDomicilio, 'rb') as archivo_cambioDomicilio_file:
            archivo_cambioDomicilio_bytes = archivo_cambioDomicilio_file.read()
            archivo_cambioDomicilio_base64 = base64.b64encode(archivo_cambioDomicilio_bytes).decode('utf-8')

            # Aquí puedes hacer lo que necesites con archivo_cambioDomicilio_base64
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de cambio de domicilio en: {archivo_cambioDomicilio}")
    except Exception as e:
        print(f"Error al leer el archivo de cambio de domicilio: {e}")

    data = {
        "inmatriculacion": inmatriculacion,
        "cliente": dni,
        "file_cambio_domicilio" : archivo_cambioDomicilio_base64,
        "file_declaracion_jurada" : archivo_delcaracion_base64
    }
    
    json_output = json.dumps(data, indent=4)

    Namejson=f"DATOS_DEL_VEHICULO{inmatriculacion}_{dni}.json"
    ruta_archivo_json = os.path.join(carpeta_inmatriculacion, Namejson)
    with open(ruta_archivo_json, "w") as Namejson:
        Namejson.write(json_output)


    enviar_inmatriculacion(inmatriculacion,dni,archivo_cambioDomicilio_base64,archivo_delcaracion_base64)
    
    time.sleep(5)


# def volver_a_inscripcion(page):
#     """Función para volver al menú de inscripción de placa."""
#     try:
#         page.locator("#btnRegresar").click()
#         time.sleep(5)
#         Registrador.info("Se regresó al menú de inscripción de placa.")
#     except Exception as e:
#         Registrador.error(f"Error al intentar regresar al menú de inscripción: {e}")
#         print(f"Error al intentar regresar al menú de inscripción: {e}")

def volver_a_inscripcion(page):
    """Función para volver al menú de inscripción de placa."""
    try:
        page.wait_for_selector("#btnRegresar", timeout=60000)
        page.locator("#btnRegresar").scroll_into_view_if_needed()
        page.locator("#btnRegresar").click()
        time.sleep(5)
        Registrador.info("Se regresó al menú de inscripción de placa.")
    except Exception as e:
        Registrador.error(f"Error al intentar regresar al menú de inscripción: {e}")
        print(f"Error al intentar regresar al menú de inscripción: {e}")

    

def combinar_modelo_version(modelo, version):
    if modelo and version:  # Evitar errores si alguno está vacío
        if modelo.lower() in version.lower():
            return version.strip()
        else:
            return f"{modelo} {version}".strip()
    return version or modelo or "" 