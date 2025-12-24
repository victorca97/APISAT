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
            case 'CVT':
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
            page.locator("#txtDesMarca").press_sequentially(variable_otras, delay=300)
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
                    page.locator("#txtDesMarcaReal").press_sequentially(marca_a_buscar, delay=300)
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
            page.locator("#txtDesMarcaV").press_sequentially(variable_otras, delay=500)
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

# ==============================================================================
# 1. HERRAMIENTAS DE PROCESAMIENTO DE TEXTO (CEREBRO)
# ==============================================================================

def separar_sufijos_conocidos(texto):
    """ Separa 'X70FL' -> 'X70 FL' """
    if not texto: return ""
    t = texto.upper()
    patron = r"([A-Z0-9]+)(FL|PLUS|PRO|MAX|SPORT|LIMITED)\b"
    t_separado = re.sub(patron, r"\1 \2", t)
    return t_separado

def fusionar_modelo_version(modelo, version):
    """ Une Modelo y Version, separa sufijos y elimina duplicados. """
    m_raw = (modelo or "").strip().upper().replace("-", " ")
    v_raw = (version or "").strip().upper().replace("-", " ")
    
    # Separamos sufijos pegados antes de nada
    m = separar_sufijos_conocidos(m_raw)
    v = separar_sufijos_conocidos(v_raw)
    
    if v in ["SIN VERSION", "S/V", "", "NO APLICA"]: return m

    palabras_brutas = m.split() + v.split()
    palabras_unicas = []
    vistos = set()
    
    for p in palabras_brutas:
        p_limpia = p.strip()
        if p_limpia not in vistos:
            palabras_unicas.append(p_limpia)
            vistos.add(p_limpia)       
    return " ".join(palabras_unicas)

def obtener_token_comparacion(palabra):
    """ Normaliza tokens (1.5L == 1.5). """
    p = palabra.upper().strip()
    if re.match(r"^\d+(\.\d+)?L$", p): return p[:-1] 
    if p in ["DLX", "DELUXE"]: return "TOKEN_DELUXE"
    if p in ["LTD", "LIMITED"]: return "TOKEN_LIMITED"
    if p in ["STD", "STANDARD"]: return "TOKEN_STANDARD"
    if p in ["AUT", "AUTOMATICO", "AT"]: return "TOKEN_AUTOMATICO"
    if p in ["MEC", "MECANICO", "MT"]: return "TOKEN_MECANICO"
    if p in ["4X2", "2WD", "SIMPLE", "S-AWD"]: return "TOKEN_TRACCION_SIMPLE"
    if p in ["4X4", "AWD", "4WD", "QUATTRO", "DOBLE"]: return "TOKEN_TRACCION_DOBLE"
    return p 

def normalizar_texto_lista(texto):
    """ Retorna lista de tokens para comparación estricta. """
    if not texto: return []
    texto_pre = separar_sufijos_conocidos(texto)
    texto_limpio = texto_pre.upper().replace("-", " ").strip()
    lista_tokens = []
    for palabra in texto_limpio.split():
        token = obtener_token_comparacion(palabra)
        match_sep = re.match(r"^([A-Z]+)(\d+)$", palabra)
        if token.startswith("TOKEN_"): lista_tokens.append(token)
        elif match_sep:
            lista_tokens.append(match_sep.group(1))
            lista_tokens.append(match_sep.group(2))
        else: lista_tokens.append(token)
    return lista_tokens

def limpiar_texto_para_input(texto):
    """ Prepara texto para escribir (sin duplicados, respeta L). """
    if not texto: return ""
    texto_upper = texto.upper().replace("-", " ").strip()
    palabras_prohibidas = ["DLX", "LTD", "STD", "AUT", "MEC", "GLP", "GNV"] 
    palabras_finales = []
    for p in texto_upper.split():
        if p not in palabras_prohibidas: palabras_finales.append(p)
    return " ".join(palabras_finales)

# ==============================================================================
# 2. MOTOR DE BÚSQUEDA
# ==============================================================================

def interactuar_y_buscar(page, texto_original, selector_input, selector_items_lista):
    texto_escribir = limpiar_texto_para_input(texto_original)
    print(f"✍️  Buscando: '{texto_escribir}'")
    
    try:
        page.locator(selector_input).fill("")
        page.locator(selector_input).press_sequentially(texto_escribir, delay=100)
    except: return False

    tiempo = 3 if "ui-autocomplete" in selector_items_lista else 4
    print(f"⏳ Esperando resultados ({tiempo}s)...")
    time.sleep(tiempo)
    
    try:
        if not page.is_visible(selector_items_lista): return False
    except: return False

    try:
        opciones = page.query_selector_all(selector_items_lista)
        lista_buscada = normalizar_texto_lista(texto_original)
        print(f"🧩 Patrón buscado: {lista_buscada}")

        for op in opciones:
            texto_opcion = op.inner_text().strip()
            lista_opcion = normalizar_texto_lista(texto_opcion)

            if lista_buscada == lista_opcion:
                print(f"✅ Coincidencia EXACTA: '{texto_opcion}'")
                time.sleep(0.5)
                op.click()
                return True
                
        print(f"⚠️ Ninguna opción coincide exactamente.")
        return False
    except Exception as e:
        print(f"⚠️ Error comparando: {e}")
        return False

def detectar_tipo_otros_modelos(page):
    try:
        val_clase = page.locator("#ddlClase").input_value()
        if val_clase == "1": return "OTROS MODELOS"
        elif val_clase == "11": 
            txt = ""
            try: txt = page.locator("#ddlTraccion option:checked").inner_text().upper()
            except: pass
            if any(k in txt for k in ["4X4", "AWD", "4WD", "QUATTRO", "DOBLE"]):
                return "OTROS MODELOS TRACCIÓN DOBLE"
            else:
                return "OTROS MODELOS TRACCIÓN SIMPLE"
        return "OTROS MODELOS"
    except: return "OTROS MODELOS"

def flujo_seleccionar_otros(page, tipo_otros, nombre_completo, selectores):
    print(f"🔄 Usando '{tipo_otros}' para llenado manual...")
    if not interactuar_y_buscar(page, tipo_otros, selectores['input'], selectores['lista_items']):
        return None
    time.sleep(1)
    if selectores.get('input_real'):
        lista_secundaria = "ul.ui-autocomplete:visible > li"
        if interactuar_y_buscar(page, nombre_completo, selectores['input_real'], lista_secundaria):
            return tipo_otros 
    if selectores.get('check'):
        try:
            chk = page.locator(selectores['check'])
            if chk.is_visible() and not chk.is_checked(): chk.check()
        except: pass
    if selectores.get('input_real'):
        try:
            real_inp = page.locator(selectores['input_real'])
            real_inp.fill("")
            texto_manual = limpiar_texto_para_input(nombre_completo)
            real_inp.press_sequentially(texto_manual, delay=100)
            print(f"📝 Escrito manualmente: {texto_manual}")
        except: pass
    return tipo_otros # Retorna "OTROS MODELOS..." para que lo sepa la siguiente función

# ==============================================================================
# 3. FUNCIONES PRINCIPALES (CON LÓGICA DE MEMORIA)
# ==============================================================================

def encontrar_modelo(page, modelo, version):
    """
    Retorna el nombre del modelo encontrado O la categoría de 'Otros Modelos'.
    """
    sel = {
        'input': "#txtDesModelo", 
        'lista_items': "#ui-id-2 > li",
        'check': "#chkNueModelo",       
        'input_real': "#txtDesModeloReal" 
    }
    nombre_busqueda = fusionar_modelo_version(modelo, version)
    
    # 1. Búsqueda normal
    if interactuar_y_buscar(page, nombre_busqueda, sel['input'], sel['lista_items']):
        return nombre_busqueda # Retorna "TOYOTA YARIS" (éxito)
    
    # 2. Si falla, detecta qué tipo de 'Otros' es y lo selecciona
    print("⚠️ Pasando a manual...")
    tipo_otros = detectar_tipo_otros_modelos(page)
    
    # Retorna "OTROS MODELOS TRACCIÓN SIMPLE", etc.
    return flujo_seleccionar_otros(page, tipo_otros, nombre_busqueda, sel)

def agregarcompradores(page):

    page.go_back()
    page.locator("#btnRegresar").click()
    page.locator("#btnRegresar").click()
    page.locator("#dgDeclaraciones_lnkPorcentaje_0 > img").click()


def encontrar_modelo2(page, modelo, version, seleccion_previa=None):
    """
    AHORA RECIBE 'seleccion_previa'.
    Si seleccion_previa es 'OTROS MODELOS...', se salta la búsqueda y va directo al grano.
    """
    sel = {
        'input': "#txtDesModeloV", 
        'lista_items': "#ui-id-6 > li",
        'check': None,      
        'input_real': None  
    }
    nombre_busqueda = fusionar_modelo_version(modelo, version)

    # ========================================================================
    # 1. ATAJO INTELIGENTE (LA VALIDACIÓN QUE PEDISTE)
    # ========================================================================
    if seleccion_previa and "OTROS MODELOS" in seleccion_previa.upper():
        print(f"⏩ ATAJO ACTIVADO: La selección previa fue '{seleccion_previa}'.")
        print("   -> No buscaré el modelo. Seleccionaré 'Otros' directamente.")
        
        # Saltamos directo a la función manual pasándole la categoría exacta que usamos antes
        return flujo_seleccionar_otros(page, seleccion_previa, nombre_busqueda, sel)

    # ========================================================================
    # 2. BÚSQUEDA NORMAL (Solo si en el paso 1 encontramos el modelo real)
    # ========================================================================
    print(f"🔎 [Popup] Buscando: '{nombre_busqueda}'")
    if interactuar_y_buscar(page, nombre_busqueda, sel['input'], sel['lista_items']):
        return nombre_busqueda
    
    print("⚠️ Pasando a manual en Popup...")
    tipo_otros = detectar_tipo_otros_modelos(page) 
    return flujo_seleccionar_otros(page, tipo_otros, nombre_busqueda, sel)


def enviar_inmatriculacion(inmatriculacion, dni, archivo_domicilio, archivo_declaracionJurada):
    url_evniarDocumentos = os.getenv('URL_ENVIA_DOCUMENTOS')
    url = url_evniarDocumentos
    
    # Determinar si se envió archivo de domicilio o está vacío
    tiene_domicilio = bool(archivo_domicilio and archivo_domicilio.strip())
    
    if tiene_domicilio:
        estructura = {
            "TramitId": inmatriculacion,
            "cliente": dni,
            "file": archivo_domicilio,
            "file2": archivo_declaracionJurada
        }
        Registrador.info(f"Enviando inmatriculación con ambos archivos: cambio domicilio y declaración jurada")
    else:
        estructura = {
            "TramitId": inmatriculacion,
            "cliente": dni,
            "file": "",
            "file2": archivo_declaracionJurada
        }
        Registrador.info(f"Enviando inmatriculación solo con declaración jurada (sin cambio de domicilio)")

    try:
        Registrador.info(f"Enviando correo electrónico a la API: {url}")
        Registrador.debug(f"Estructura de la inmatriculacion: {estructura}")

        response = requests.post(url, json=estructura)
        
        if response.status_code == 200:
            Registrador.info(f"Inmatriculacion enviado exitosamente. Código de estado: {response.status_code}")
            Registrador.debug(f"Respuesta de la API: {response.json()}")
            
            # Email de éxito
            destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
            if tiene_domicilio:
                asunto = f"TEST BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Ambos archivos"
                mensaje = f"<p>Se envió la inmatriculación N°{inmatriculacion} por el APISAT con ambos archivos (cambio domicilio y declaración jurada).</p>"
            else:
                asunto = f"TEST BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Solo declaración"
                mensaje = f"<p>Se envió la inmatriculación N°{inmatriculacion} por el APISAT solo con declaración jurada (sin cambio de domicilio).</p>"
            
            enviar_email_Api(destinos, asunto, mensaje)
            return response
            
        elif response.status_code == 400:
            Registrador.error(f"Error al enviar la inmatriculacion. Código de estado: {response.status_code}. Verifique los datos enviados.")
            Registrador.debug(f"Respuesta de la API (error 400): {response.text}")
            
            # Email de error 400
            destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Error 400"
            error_message = f"<p>Error 400 al enviar la inmatriculación N°{inmatriculacion} por el APISAT.</p><p>Respuesta: {response.text}</p>"
            enviar_email_Api(destinos, asunto, error_message)
            return response
            
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        Registrador.error(f"Error al enviar la inmatriculacion a la API: {e}")
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
        
        if tiene_domicilio:
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Ambos archivos"
            error_message = f"<p>Hubo un error al enviar la inmatriculación con ambos archivos por el APISAT.</p><p>Error: {e}</p>"
        else:
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Solo declaración"
            error_message = f"<p>Hubo un error al enviar la inmatriculación solo con declaración jurada por el APISAT.</p><p>Error: {e}</p>"
        
        Registrador.error(f"Hubo un error al enviar la inmatriculacion por el APISAT. Error: {e}")
        print(traceback.format_exc())
        enviar_email_Api(destinos, asunto, error_message)
        return None

    except Exception as e:
        Registrador.error(f"Error inesperado al enviar la inmatriculacion a la API: {e}")
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
        
        if tiene_domicilio:
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Error inesperado"
        else:
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Error inesperado (solo declaración)"
            
        error_message = f"<p>Hubo un error inesperado al enviar la inmatriculación.</p><p>Error: {e}</p>"
        Registrador.error(f"Hubo un error inesperado. Error: {e}")
        print(traceback.format_exc())
        enviar_email_Api(destinos, asunto, error_message)
        return None



def Guardar_Archivos(page, browser, inmatriculacion, dni): 
    carpeta_base_proyecto = "./downloads"
    carpeta_inmatriculacion = os.path.join(carpeta_base_proyecto, str(inmatriculacion))
    os.makedirs(carpeta_inmatriculacion, exist_ok=True)

    # Define las rutas de los archivos
    archivo_delcaracion = os.path.join(carpeta_inmatriculacion, f"ArchivoDeclaracion_{inmatriculacion}_{dni}.pdf")
    archivo_cambioDomicilio = os.path.join(carpeta_inmatriculacion, f"ArchivoCambioDomicilio_{inmatriculacion}_{dni}.pdf")
    
    # Variable para controlar si existe el botón de cambio de domicilio
    existe_boton_cambio_domicilio = False
    
    # Validar si existe el botón btnImpDJCamDom
    try:
        print("Validando existencia del botón btnImpDJCamDom...")
        boton_cambio_domicilio = page.locator("input[id='btnImpDJCamDom']")
        
        if boton_cambio_domicilio.is_visible(timeout=5000):
            existe_boton_cambio_domicilio = True
            print(" Botón btnImpDJCamDom encontrado y visible")
        else:
            existe_boton_cambio_domicilio = False
            print(" Botón btnImpDJCamDom no visible")
        
    except Exception as e:
        print(f" Botón btnImpDJCamDom no encontrado: {e}")
        existe_boton_cambio_domicilio = False

    # Procesar cambio de domicilio solo si el botón existe
    if existe_boton_cambio_domicilio:
        try:
            print("Procesando cambio de domicilio...")
            
            # Solo pide ver el botón si existe
            input("ver boton - Presiona Enter para continuar con cambio de domicilio...")
            
            with page.expect_navigation(wait_until='load'):
                page.locator("input[id='btnImpDJCamDom']").click()

            # Obtener HTML y generar PDF de cambio de domicilio
            html_cambioDomicilio = page.inner_html("#form1 > div:nth-child(4)")

            with open(archivo_cambioDomicilio, "wb") as pdf:
                pisa_status = pisa.CreatePDF(html_cambioDomicilio, dest=pdf)
                if pisa_status.err:
                    print("Error al generar el PDF CAMBIODOMICILIO")

            print(f"PDF del cambio domicilio guardado en: {archivo_cambioDomicilio}")
            Registrador.info(f"PDF del cambio domicilio guardado en: {archivo_cambioDomicilio}")

            # Regresar a la página anterior
            with page.expect_navigation(wait_until='load'):
                page.locator("#btnRegresar").click()
                
        except Exception as e:
            print(f" Error al procesar cambio de domicilio: {e}")
            existe_boton_cambio_domicilio = False  # Marcar como fallido
    else:
        print(" Saltando proceso de cambio de domicilio - botón no encontrado")

    # Procesar declaración jurada (siempre se ejecuta)
    try:
        print("Procesando declaración jurada...")
        input("ver boton - Presiona Enter para continuar con declaración jurada...")
        parte1 = page.inner_html("#DivImpresion > table > tbody > tr > td > table:nth-child(1)")
        parte2 = page.inner_html("#DivImpresion > table > tbody > tr > td > table:nth-child(2)")
        parte3 = page.inner_html("#DivImpresion > table > tbody > tr > td > table:nth-child(3)")
        
        ruta_temporal_html = "temp_declaracion.html"

        # Crear HTML minimalista
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

        # Guardar HTML temporal (para depuración)
        with open(ruta_temporal_html, "w", encoding="utf-8") as f:
            f.write(html_minimal)

        # Crear nueva página y generar PDF
        nueva_pagina = browser.new_page()
        nueva_pagina.set_content(html_minimal)
        nueva_pagina.pdf(path=archivo_delcaracion, format="A4", print_background=False)
        nueva_pagina.close()
        
        print(f" PDF de declaración guardado en: {archivo_delcaracion}")
        Registrador.info(f"PDF de declaración guardado en: {archivo_delcaracion}")
        
    except Exception as e:
        print(f" Error al procesar declaración jurada: {e}")
        raise  # Si falla la declaración jurada, sí detenemos el proceso

    # Leer archivos y codificar en base64
    archivo_delcaracion_base64 = ""
    archivo_cambioDomicilio_base64 = ""

    # Leer archivo de declaración (siempre debe existir)
    try:
        with open(archivo_delcaracion, 'rb') as archivo_delcaracion_file:
            archivo_delcaracion_bytes = archivo_delcaracion_file.read()
            archivo_delcaracion_base64 = base64.b64encode(archivo_delcaracion_bytes).decode('utf-8')
    except FileNotFoundError:
        print(f" Error: No se encontró el archivo de declaración en: {archivo_delcaracion}")
    except Exception as e:
        print(f" Error al leer el archivo de declaración: {e}")

    # Leer archivo de cambio de domicilio solo si se procesó correctamente
    if existe_boton_cambio_domicilio:
        try:
            with open(archivo_cambioDomicilio, 'rb') as archivo_cambioDomicilio_file:
                archivo_cambioDomicilio_bytes = archivo_cambioDomicilio_file.read()
                archivo_cambioDomicilio_base64 = base64.b64encode(archivo_cambioDomicilio_bytes).decode('utf-8')
        except FileNotFoundError:
            print(f" Error: No se encontró el archivo de cambio de domicilio en: {archivo_cambioDomicilio}")
        except Exception as e:
            print(f" Error al leer el archivo de cambio de domicilio: {e}")

    # Preparar datos según si existe o no el botón
    if existe_boton_cambio_domicilio:
        data = {
            "inmatriculacion": inmatriculacion,
            "cliente": dni,
            "file_cambio_domicilio": archivo_cambioDomicilio_base64,
            "file_declaracion_jurada": archivo_delcaracion_base64
        }
        print("Preparando datos con ambos archivos (cambio domicilio y declaración)")
    else:
        data = {
            "inmatriculacion": inmatriculacion,
            "cliente": dni,
            "file_cambio_domicilio": "",  # vacío
            "file_declaracion_jurada": archivo_delcaracion_base64
        }
        print("Preparando datos solo con declaración jurada (sin cambio de domicilio)")

    # Guardar JSON
    json_output = json.dumps(data, indent=4)
    Namejson = f"DATOS_DEL_VEHICULO{inmatriculacion}_{dni}.json"
    ruta_archivo_json = os.path.join(carpeta_inmatriculacion, Namejson)
    
    with open(ruta_archivo_json, "w") as Namejson:
        Namejson.write(json_output)

    print(f"JSON guardado en: {ruta_archivo_json}")

    # Enviar inmatriculación
    enviar_inmatriculacion(inmatriculacion, dni, archivo_cambioDomicilio_base64, archivo_delcaracion_base64)
    
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