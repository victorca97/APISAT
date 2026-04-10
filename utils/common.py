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
    # dni = tipo_documento.replace("D", "").strip()
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
            case 'N1':
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
        moneda = 2
    elif moneda == "PEN":
        moneda = 1

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


# Cambio de funcion encontrar_marca

def encontrar_marca(page, marca_usuario):
    # Mapeo personalizado de marcas
    MAPEO_MARCAS = {
        "MG": "MG",
        "LINXYS": "LINXYS",
        "SOUEAST": "SOUESAST",
        "DONG FENG": "DONGFENG",
        "TIANJIN FAW": " FAW",
        "BEIJING AUTO WORKS": "BAW",
        "BEIJING AUTOMOBILE WORKS": "BAW",
        "ZXAUTO": "ZX",
        "MARCOPOLO": "MARCOPOLO VOLARE",
        "AGRALE": "AGRALE-MODASA"
    }

    try:
        # Aplicar mapeo si la marca está en el diccionario
        marca_a_buscar = MAPEO_MARCAS.get(marca_usuario.upper(), marca_usuario)
        print(f"Buscando marca: {marca_a_buscar}")

        # 1. Limpiamos la caja de texto por completo
        page.locator("input[name='txtDesMarca']").press_sequentially(
            marca_a_buscar, delay=80)

        time.sleep(2)

        # Verificar si existe la lista de marcas
        try:
            page.wait_for_selector("#txtDesMarca", timeout=6000)
            time.sleep(2)

            hay_lista = True
        except:
            print(" No se encontró la lista de marcas. Procediendo con 'OTRAS MARCAS'...")
            hay_lista = False

        # Si hay lista, hacer la búsqueda normal
        if hay_lista:
            opciones = page.query_selector_all("#ui-id-1 > li")
            lista_locator = [opcion.inner_text().strip()
                             for opcion in opciones]
            print("Lista marcas disponibles:", lista_locator)
            print("Marca a buscar:", marca_a_buscar)

            best_match_ratio = -1
            best_match_index = -1
            best_match_value = None

            # Buscar mejor coincidencia
            for i, valor_marca in enumerate(lista_locator):
                matcher = SequenceMatcher(
                    None, marca_a_buscar.upper(), valor_marca.upper())
                ratio = matcher.ratio()
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_index = i
                    best_match_value = valor_marca

            if best_match_value:
                if best_match_ratio >= 0.99:
                    print(
                        f" Coincidencia alta encontrada: '{best_match_value}' con ratio {best_match_ratio:.2f}")
                    indice_css = best_match_index + 1
                    page.click(f"#ui-id-1 > li:nth-child({indice_css})")
                    return best_match_value
                else:
                    print(" Baja coincidencia. Buscando 'OTRAS MARCAS'...")
            else:
                print(" Sin coincidencias. Forzando 'OTRAS MARCAS'...")
        else:
            print(" Lista no disponible. Forzando 'OTRAS MARCAS'...")

        # Bloque común para cuando hay que usar "OTRAS MARCAS"
        max_reintentos = 3
        encontrado = False
        intento = 0

        while not encontrado and intento < max_reintentos:
            intento += 1
            print(f" Reintento {intento} para encontrar 'OTRAS MARCAS'")
            variable_otras = "OTRAS MARCAS"

            # Limpiar y escribir en el campo de marca
            page.locator("#txtDesMarca").fill("")
            time.sleep(1)
            page.locator("#txtDesMarca").press_sequentially(
                variable_otras, delay=0.10)
            time.sleep(3)

            # Actualizar lista después de escribir
            try:
                opciones2 = page.query_selector_all("#ui-id-1 > li")
                lista_locator2 = [opcion.inner_text().strip()
                                  for opcion in opciones2]

                # Buscar "OTRAS MARCAS"
                for i, opcion in enumerate(opciones2):
                    texto = opcion.inner_text().strip()
                    if texto.upper() == "OTRAS MARCAS":
                        print(" Opción encontrada: OTRAS MARCAS")
                        indice_css = i + 1
                        page.click(f"#ui-id-1 > li:nth-child({indice_css})")
                        encontrado = True
                        break
            except Exception as e:
                print(f" Error al buscar opciones: {e}")

            if not encontrado:
                print("No encontrado aún. Reintentando...")
                time.sleep(2)

        if encontrado:
            print("'OTRAS MARCAS' seleccionado correctamente. Buscando en la segunda lista...")
            time.sleep(1)

            try:
                # 1. Escribimos la marca en el segundo input SIN marcar el check todavía
                caja_secundaria = page.locator("#txtDesMarcaReal")

                if caja_secundaria.is_visible():
                    caja_secundaria.fill("")
                    caja_secundaria.press_sequentially(
                        marca_a_buscar, delay=0.10)
                    # Espera crucial para que el SAT cargue la segunda lista
                    time.sleep(2)

                    # 2. Leemos la lista autocompletable secundaria
                    # Usamos un selector genérico y robusto para las listas de autocompletado
                    lista_secundaria = page.locator(
                        "ul.ui-autocomplete:visible > li")
                    marca_encontrada_lista_2 = False

                    if lista_secundaria.count() > 0:
                        for i in range(lista_secundaria.count()):
                            op = lista_secundaria.nth(i)
                            if op.is_visible() and op.inner_text().strip().upper() == marca_a_buscar.upper():
                                print(
                                    f" ✅ Marca '{marca_a_buscar}' encontrada en la segunda lista. Haciendo clic...")
                                op.click()
                                marca_encontrada_lista_2 = True
                                time.sleep(1)
                                break

                    # 3. Si NO la encontró en la lista, RECIÉN marcamos el check y forzamos
                    if not marca_encontrada_lista_2:
                        print(
                            f" ⚠️ La marca no está en la segunda lista. Activando Checkbox para forzar...")
                        checkbox = page.locator("#chkNueMarca")

                        if checkbox.is_visible():
                            # Verificamos el estado real del check usando JS para no desmarcarlo por error
                            estado_check = checkbox.evaluate(
                                "node => node.checked")
                            if not estado_check:
                                checkbox.click()
                                print(" Checkbox #chkNueMarca marcado")
                                time.sleep(1)

                        # Escribimos a la fuerza (a veces el SAT borra la caja al hacer clic en el check)
                        caja_secundaria.fill("")
                        caja_secundaria.press_sequentially(
                            marca_a_buscar, delay=0.10)
                        print(
                            f" Campo #txtDesMarcaReal forzado con: {marca_a_buscar}")

            except Exception as e:
                print(
                    f" Error en el flujo del segundo selector de marca: {e}")

            return variable_otras
        else:
            print(" No se pudo seleccionar 'OTRAS MARCAS' después de varios intentos.")
            return None

    except Exception as e:
        print(f" Error al buscar marcas: {e}")
        return None


def encontrar_marca1(page, marca_usuario):
    # Mapeo personalizado de marcas
    MAPEO_MARCAS = {
        "MG": "MG",
        "LINXYS": "LINXYS",
        "SOUEAST": "SOUESAST",
        "DONG FENG": "DONGFENG",
        "TIANJIN FAW": " FAW",
        "BEIJING AUTO WORKS": "BAW",
        "BEIJING AUTOMOBILE WORKS": "BAW",
        "ZXAUTO": "ZX",
        "MARCOPOLO": "MARCOPOLO VOLARE",
        "AGRALE": "AGRALE-MODASA"
    }

    try:
        # Aplicar mapeo si la marca está en el diccionario
        marca_a_buscar = MAPEO_MARCAS.get(marca_usuario.upper(), marca_usuario)
        print(f"Buscando marca: {marca_a_buscar}")

        # 1. Limpiamos la caja de texto por completo
        # page.locator("input[name='txtDesMarcaV']").clear()
        page.locator("input[name='txtDesMarcaV']").press_sequentially(
            marca_a_buscar, delay=120)

        time.sleep(2)

        # Verificar si existe la lista de marcas
        try:
            page.wait_for_selector("#ui-id-5 > li", timeout=6000)
            time.sleep(2)
            hay_lista = True
        except:
            print(
                " No se encontró la lista '#ui-id-5 > li'. Procediendo con 'OTRAS MARCAS'...")
            hay_lista = False

        # Si hay lista, hacer búsqueda normal
        if hay_lista:
            opciones = page.query_selector_all("#ui-id-5 > li")
            lista_locator = [opcion.inner_text().strip()
                             for opcion in opciones]
            print("Lista marcas:", lista_locator)
            print("Marca a buscar:", marca_a_buscar)

            best_match_ratio = -1
            best_match_index = -1
            best_match_value = None

            # Buscar mejor coincidencia
            for i, valor_marca in enumerate(lista_locator):
                matcher = SequenceMatcher(
                    None, marca_a_buscar.upper(), valor_marca.upper())
                ratio = matcher.ratio()
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_index = i
                    best_match_value = valor_marca

            if best_match_value:
                if best_match_ratio >= 0.99:
                    print(
                        f" Coincidencia alta encontrada: '{best_match_value}' con ratio {best_match_ratio:.2f}")
                    indice_css = best_match_index + 1
                    page.click(f"#ui-id-5 > li:nth-child({indice_css})")
                    return best_match_value
                else:
                    print(" Baja coincidencia. Forzando 'OTRAS MARCAS'...")
            else:
                print(" Sin coincidencias. Forzando 'OTRAS MARCAS'...")

        else:
            print(" Lista no disponible. Forzando 'OTRAS MARCAS'.")

        # Bloque común para cuando hay que usar "OTRAS MARCAS"
        max_reintentos = 5
        encontrado = False
        intento = 0

        while not encontrado and intento < max_reintentos:
            intento += 1
            print(f" Reintento {intento} para encontrar 'OTRAS MARCAS'")
            variable_otras = "OTRAS MARCAS"

            page.locator("#txtDesMarcaV").fill("")
            time.sleep(2)
            page.locator("#txtDesMarcaV").press_sequentially(
                variable_otras, delay=0.10)
            time.sleep(3)

            # Actualizar lista después de escribir
            opciones2 = page.query_selector_all("#ui-id-5 > li")
            lista_locator2 = [opcion.inner_text().strip()
                              for opcion in opciones2]

            # Buscar "OTRAS MARCAS"
            for i, opcion in enumerate(opciones2):
                texto = opcion.inner_text().strip()
                if texto.upper() == "OTRAS MARCAS":
                    print(" Opción encontrada: OTRAS MARCAS")
                    indice_css = i + 1
                    page.click(f"#ui-id-5 > li:nth-child({indice_css})")
                    encontrado = True
                    break

            if not encontrado:
                print(" No encontrado aún. Reintentando...")
                time.sleep(3)

        if encontrado:
            print(" 'OTRAS MARCAS' seleccionado correctamente.")
            return variable_otras
        else:
            print(" No se pudo seleccionar 'OTRAS MARCAS' después de varios intentos.")
            return None

    except Exception as e:
        print(f" Error al buscar marcas: {e}")
        return None


def encontrar_carroceria(page, carroceria_buscada):

    page.wait_for_selector("#ddlCarroceria")
    page.locator("#ddlCarroceria").click()
    lista_carroceria = page.evaluate(
        'Array.from(document.querySelectorAll("#ddlCarroceria > option")).map(option => option.text)')

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
        print(
            f"Mejor coincidencia encontrada: {opcion_a_seleccionar} con ratio: {best_match_ratio}")
        return opcion_a_seleccionar
    else:
        print(
            f"No se encontró una coincidencia cercana para '{carroceria_buscada}'.")
        return None


# =============================
# CASOS MODELOS VEHICULOS
# =============================

def separar_sufijos_conocidos(texto):
    """ Separa 'X70FL' -> 'X70 FL' sin fallar """
    if not texto:
        return ""
        
    t = texto.upper().strip()
    
    #  LA MAGIA NUEVA: Lookbehind (?<=[A-Z0-9])
    # Significa: "Asegúrate de que justo antes del sufijo haya una letra o número (no un espacio)"
    patron = r"(?<=[A-Z0-9])(FL|PLUS|PRO|MAX|SPORT|LIMITED)\b"
    
    # Solo necesitamos poner un espacio antes del Grupo 1
    t_separado = re.sub(patron, r" \1", t)
    
    if t != t_separado:
        print(f" [AUTO-CORRECCIÓN]: Separando sufijo pegado -> '{t}' a '{t_separado}'")
        
    return t_separado
    

def obtener_variantes_texto(modelo, version):
    """ 
    NUEVO MOTOR: Genera dos versiones del texto eliminando comas pero respetando - y /.
    Retorna: (texto_con_duplicados, texto_sin_duplicados)
    """
    m = (modelo or "").strip().upper().replace(",", "")
    v = (version or "").strip().upper().replace(",", "")

    if v in ["SIN VERSION", "SINVERSION" "S/V", "", "NO APLICA"]:
        return m, m

    # 1. TEXTO CON DUPLICADOS (Se junta todo tal cual)
    texto_con_dup = f"{m} {v}".strip()

    # 2. TEXTO SIN DUPLICADOS (Análisis inteligente)
    m_analisis = separar_sufijos_conocidos(m)
    v_analisis = separar_sufijos_conocidos(v)

    palabras_m = m_analisis.split()
    palabras_v = v_analisis.split()

    # Verificamos si TODAS las palabras del modelo están en la versión
    set_v_limpio = set(w.replace("-", "").replace("/", "") for w in palabras_v)
    modelo_incluido = True
    for pm in palabras_m:
        pm_limpio = pm.replace("-", "").replace("/", "")
        if pm_limpio not in set_v_limpio:
            modelo_incluido = False
            break

    if modelo_incluido:
        # Caso: CS55 y NEW CS55 PLUS -> Ya está incluido, dejamos solo la versión
        texto_sin_dup = v
    else:
        # Fusión normal eliminando solo palabras repetidas exactas (Caso Supervan)
        palabras_raw = m.split() + v.split()
        palabras_finales = []
        vistos_limpios = set()
        for p in palabras_raw:
            p_clean = p.replace("-", "").replace(".", "").replace("/", "")
            if p_clean not in vistos_limpios:
                palabras_finales.append(p)
                vistos_limpios.add(p_clean)
        texto_sin_dup = " ".join(palabras_finales)

    return texto_con_dup, texto_sin_dup


def obtener_token_comparacion(palabra):
    p = palabra.upper().strip()
    if re.match(r"^\d+(\.\d+)?L$", p):
        return p[:-1]
    if p in ["DLX", "DELUXE"]:
        return "TOKEN_DELUXE"
    if p in ["LTD", "LIMITED"]:
        return "TOKEN_LIMITED"
    if p in ["AUT", "AUTOMATICO", "AT"]:
        return "TOKEN_AUTOMATICO"
    if p in ["4X2", "2WD"]:
        return "TOKEN_TRACCION_SIMPLE"
    if p in ["4X4", "AWD", "4WD", "QUATTRO"]:
        return "TOKEN_TRACCION_DOBLE"
    return p


def normalizar_texto_lista(texto):
    if not texto:
        return []
    texto_pre = separar_sufijos_conocidos(texto)
    texto_limpio = texto_pre.upper().strip().replace(",", "").replace("/", "")
    lista_tokens = []
    for palabra in texto_limpio.split():
        palabra_sin_guion = palabra.replace("-", "")
        if not palabra_sin_guion.strip():
            continue
        token = obtener_token_comparacion(palabra_sin_guion)
        match_sep = re.match(r"^([A-Z]+)(\d+)$", palabra_sin_guion)
        if token.startswith("TOKEN_"):
            lista_tokens.append(token)
        elif match_sep:
            lista_tokens.append(match_sep.group(1))
            lista_tokens.append(match_sep.group(2))
        else:
            lista_tokens.append(token)
    return lista_tokens

# ==============================================================================
# 2. MOTOR DE BÚSQUEDA AVANZADO
# ==============================================================================


def generar_intentos_busqueda_avanzado(texto_con_dup, texto_sin_dup):
    """ Agrupa las estrategias: Primero CON duplicados, luego SIN duplicados """
    intentos = []
    vistos = set()

    def agregar_variantes(base_text, texto_original_para_comparar):
        if not base_text:
            return
        palabras_prohibidas = ["LTD", "GNV"]
        base = " ".join([p for p in base_text.split()
                        if p not in palabras_prohibidas])

        # 1. Original (con símbolos)
        if base not in vistos:
            intentos.append((base, texto_original_para_comparar))
            vistos.add(base)

        # 2. Sin L
        base_sin_l = re.sub(r'\b(\d+(?:\.\d+)?)L\b', r'\1', base)
        if base_sin_l not in vistos:
            intentos.append((base_sin_l, texto_original_para_comparar))
            vistos.add(base_sin_l)

        # 3. Sin símbolos
        base_sin_simbolos = base.replace("-", "").replace("/", "")
        base_sin_simbolos = " ".join(base_sin_simbolos.split())
        if base_sin_simbolos not in vistos:
            intentos.append((base_sin_simbolos, texto_original_para_comparar))
            vistos.add(base_sin_simbolos)

        # 4. Sin símbolos y sin L
        base_sin_simbolos_y_l = re.sub(
            r'\b(\d+(?:\.\d+)?)L\b', r'\1', base_sin_simbolos)
        if base_sin_simbolos_y_l not in vistos:
            intentos.append(
                (base_sin_simbolos_y_l, texto_original_para_comparar))
            vistos.add(base_sin_simbolos_y_l)

    # SECUENCIA ESTRICTA SOLICITADA:
    # Primero: Intentos CON el duplicado
    agregar_variantes(texto_con_dup, texto_con_dup)

    # Segundo: Intentos SIN el duplicado (Si es que hay diferencia)
    if texto_con_dup != texto_sin_dup:
        agregar_variantes(texto_sin_dup, texto_sin_dup)

    return intentos


def interactuar_y_buscar(page, texto_con_dup, texto_sin_dup, selector_input, selector_items_lista):
    intentos = generar_intentos_busqueda_avanzado(texto_con_dup, texto_sin_dup)
    print(f"\nINICIANDO BUSQUEDA EN SAT: '{texto_sin_dup}'")

    for i, (texto_a_buscar, texto_original_comparacion) in enumerate(intentos):

        texto_a_buscar_limpio = " ".join(
            texto_a_buscar.replace("-", " ").split())

        lista_buscada = normalizar_texto_lista(texto_original_comparacion)
        lista_buscada_ordenada = sorted(lista_buscada)
        set_buscado = set(lista_buscada)

        tipo = "CON DUPLICADOS" if texto_original_comparacion == texto_con_dup else "SIN DUPLICADOS"
        print(
            f"Intento #{i+1} [{tipo}]: Escribiendo '{texto_a_buscar_limpio}'...")

        # 1. ESCRITURA
        try:
            page.locator(selector_input).clear()
            page.locator(selector_input).press_sequentially(
                texto_a_buscar_limpio, delay=0.10)
        except Exception as e:
            print(f"Error al escribir en el input: {e}")
            return False

        # 2. ESPERA DE LA LISTA
        time.sleep(2)

        if not page.locator(selector_items_lista).first.is_visible():
            print("La lista autocompletable no aparecio.")
            continue

        # 3. PURIFICACION DE API Y CONTEO
        texto_api_limpio_case = " ".join(texto_original_comparacion.split())
        texto_api_limpio_upper = texto_api_limpio_case.upper()

        # Contamos cuántas opciones hay para probarlas una por una
        cantidad_opciones = page.locator(selector_items_lista).count()

        # ==============================================================
        # PASADA 0.1: PRIORIDAD ABSOLUTA (Mayusculas y espacios perfectos)
        # ==============================================================
        for idx in range(cantidad_opciones):
            op = page.locator(selector_items_lista).nth(idx)
            if not op.is_visible():
                continue

            texto_opcion_original = op.inner_text().replace('\xa0', ' ').strip()
            texto_opcion_upper = texto_opcion_original.upper()

            if "OTROS MODELOS" in texto_opcion_upper and "OTROS MODELOS" not in texto_api_limpio_upper:
                continue

            if texto_api_limpio_case == texto_opcion_original:
                print(
                    f"MATCH PERFECTO (Case Sensitive): '{texto_opcion_original}'")
                try:
                    op.click(timeout=3000, force=True)
                    page.wait_for_timeout(500)
                    valor_en_caja = page.locator(selector_input).input_value()

                    if "  " in valor_en_caja and "SOLUTO" not in valor_en_caja.upper():
                        print(
                            f"Trampa detectada en la opción {idx+1}. Descartando y probando la siguiente...")
                        page.locator(selector_input).clear()
                        # Volvemos a teclear para que reaparezca la lista y seguir con el siguiente
                        page.locator(selector_input).press_sequentially(
                            texto_a_buscar_limpio, delay=0.10)
                        page.wait_for_timeout(1500)
                        continue  # SALTA AL SIGUIENTE ÍNDICE

                    return True
                except Exception as e:
                    return False

        # ==============================================================
        # PASADA 0.2: BUSQUEDA LITERAL (Ignorando mayusculas/minusculas)
        # ==============================================================
        for idx in range(cantidad_opciones):
            op = page.locator(selector_items_lista).nth(idx)
            if not op.is_visible():
                continue

            texto_opcion_original = op.inner_text().replace('\xa0', ' ').strip()
            texto_opcion_upper = texto_opcion_original.upper()

            if "OTROS MODELOS" in texto_opcion_upper and "OTROS MODELOS" not in texto_api_limpio_upper:
                continue

            if texto_api_limpio_upper == texto_opcion_upper:
                print(f"MATCH LITERAL EXACTO: '{texto_opcion_original}'")
                try:
                    op.click(timeout=3000, force=True)
                    page.wait_for_timeout(500)
                    valor_en_caja = page.locator(selector_input).input_value()

                    if "  " in valor_en_caja and "SOLUTO" not in valor_en_caja.upper():
                        print(
                            f"Trampa detectada en la opción {idx+1}. Descartando y probando la siguiente...")
                        page.locator(selector_input).clear()
                        page.locator(selector_input).press_sequentially(
                            texto_a_buscar_limpio, delay=0.10)
                        page.wait_for_timeout(1500)
                        continue

                    return True
                except Exception as e:
                    return False

        # ==============================================================
        # PASADA 1: BUSQUEDA EXACTA (Mismas palabras, distinto orden)
        # ==============================================================
        for idx in range(cantidad_opciones):
            op = page.locator(selector_items_lista).nth(idx)
            if not op.is_visible():
                continue

            texto_opcion_original = op.inner_text().replace('\xa0', ' ').strip()
            texto_opcion_upper = texto_opcion_original.upper()

            if "OTROS MODELOS" in texto_opcion_upper and "OTROS MODELOS" not in texto_api_limpio_upper:
                continue
            if "  " in texto_opcion_upper and "  " not in texto_api_limpio_upper:
                continue

            lista_opcion_ordenada = sorted(
                normalizar_texto_lista(texto_opcion_upper))

            if lista_buscada_ordenada == lista_opcion_ordenada:
                print(f"MATCH EXACTO ORDENADO: '{texto_opcion_original}'")
                try:
                    op.click(timeout=3000, force=True)
                    page.wait_for_timeout(500)
                    valor_en_caja = page.locator(selector_input).input_value()

                    if "  " in valor_en_caja and "SOLUTO" not in valor_en_caja.upper():
                        print(
                            f"Trampa detectada en la opción {idx+1}. Descartando y probando la siguiente...")
                        page.locator(selector_input).clear()
                        page.locator(selector_input).press_sequentially(
                            texto_a_buscar_limpio, delay=0.10)
                        page.wait_for_timeout(1500)
                        continue

                    return True
                except:
                    return False

        # ==============================================================
        # PASADA 2: BUSQUEDA HOMOLOGO / SUBSET
        # ==============================================================
        for idx in range(cantidad_opciones):
            op = page.locator(selector_items_lista).nth(idx)
            if not op.is_visible():
                continue

            texto_opcion_original = op.inner_text().replace('\xa0', ' ').strip()
            texto_opcion_upper = texto_opcion_original.upper()

            if "OTROS MODELOS" in texto_opcion_upper and "OTROS MODELOS" not in texto_api_limpio_upper:
                continue
            if "  " in texto_opcion_upper and "  " not in texto_api_limpio_upper:
                continue

            set_opcion = set(normalizar_texto_lista(texto_opcion_upper))

            if set_buscado == set_opcion:
                print(f"MATCH EXACTO POR SETS: '{texto_opcion_original}'")
                try:
                    op.click(timeout=3000, force=True)
                    page.wait_for_timeout(500)
                    valor_en_caja = page.locator(selector_input).input_value()

                    if "  " in valor_en_caja and "SOLUTO" not in valor_en_caja.upper():
                        print(
                            f"Trampa detectada en la opción {idx+1}. Descartando y probando la siguiente...")
                        page.locator(selector_input).clear()
                        page.locator(selector_input).press_sequentially(
                            texto_a_buscar_limpio, delay=0.10)
                        page.wait_for_timeout(1500)
                        continue

                    return True
                except:
                    return False

        print("Opciones visibles, pero ninguna hizo MATCH estricto o todas eran trampas.")

    print("Agotados todos los intentos. Pasando a Plan B (Llenado manual mediante Checkbox).")
    return False


def detectar_tipo_otros_modelos(page, peso_bruto=None):
    """Calcula el fallback correcto ('OTROS MODELOS...') según la clase y peso."""
    try:
        val_clase = page.locator("#ddlClase").input_value().strip()

        # ---------------------------------------------------------
        # Automóvil (1), Ómnibus (7), Remolcador/Tracto (12)
        # ---------------------------------------------------------
        if val_clase in ["1", "7", "12"]:
            return "OTROS MODELOS"

        # ---------------------------------------------------------
        # Camioneta (11) - Validación de Tracción
        # ---------------------------------------------------------
        elif val_clase == "11":
            try:
                txt = page.locator(
                    "#ddlTraccion option:checked").inner_text().upper()
                if any(k in txt for k in ["4X4", "AWD", "4WD", "QUATTRO"]):
                    # Devolvemos la lista con ambas versiones (sin tilde y con tilde)
                    return ["OTROS MODELOS TRACCIÓN DOBLE", "OTROS MODELOS TRACCION DOBLE"]
            except:
                pass  # Si falla al leer la tracción, asume tracción simple

            # Devolvemos la lista para la tracción simple también
            return ["OTROS MODELOS TRACCIÓN SIMPLE", "OTROS MODELOS TRACCION SIMPLE"]

        # ---------------------------------------------------------
        # Camión (8) - Validación de Peso Bruto Vehicular
        # ---------------------------------------------------------
        elif val_clase == "8":
            if not peso_bruto:
                return "OTROS MODELOS"
            try:
                peso = float(peso_bruto)

                # Rango 1: De 4001 a 7000
                if 4001 <= peso <= 7000:
                    return "OTROS MODELOS PVB HASTA 7 000 KG."

                # Rango 2: De 7001 a 20000
                elif 7001 <= peso <= 20000:
                    return "OTROS MODELOS DE PVB MAS DE 7 000 KG A 20 000 KG."

                # Rango 3: De 20001 a mas
                elif peso >= 20001:
                    return "OTROS MODELOS PVB MAYOR A 20 000 KG."

                # Fallback para camiones atipicos (4000 kg o menos)
                else:
                    return "OTROS MODELOS"

            except ValueError:
                return "OTROS MODELOS"

    except Exception as e:
        print(f" Error en detectar_tipo_otros_modelos: {e}")
        return "OTROS MODELOS"


def flujo_seleccionar_otros(page, tipo_otros, texto_sin_dup, selectores):
    print(f"\nINICIANDO FLUJO MANUAL: Usando puente...")

    # =================================================================
    # PASO 1: Seleccionar el puente (Soporta Textos simples y Listas)
    # =================================================================
    puente_exitoso = False

    # Verificamos si 'tipo_otros' es una lista (como el caso de las camionetas con y sin tilde)
    if isinstance(tipo_otros, list):
        for tipo in tipo_otros:
            print(f"Intentando opción puente: '{tipo}'...")
            if interactuar_y_buscar(page, tipo, tipo, selectores['input'], selectores['lista_items']):
                puente_exitoso = True
                tipo_otros = tipo  # Guardamos la opción que funcionó para usarla luego si es necesario
                break  # Salimos del bucle porque ya encontró uno válido y lo seleccionó
    else:
        # Flujo normal si 'tipo_otros' es un solo texto
        if interactuar_y_buscar(page, tipo_otros, tipo_otros, selectores['input'], selectores['lista_items']):
            puente_exitoso = True

    # Si después de intentar todo no funcionó, cortamos el proceso
    if not puente_exitoso:
        print("Fallo la seleccion de la opcion puente generica.")
        return None

    import time
    time.sleep(1)

    # A partir de aquí sigue el PASO 2 normal de tu función...
    texto_limpio_final = texto_sin_dup.replace(",", "").strip()

    # =================================================================
    # PASO 2: Buscar en la segunda caja
    # =================================================================
    if selectores.get('input_real'):
        lista_secundaria = "ul.ui-autocomplete:visible > li"
        print(f"Buscando '{texto_limpio_final}' en input secundario...")

        if interactuar_y_buscar(page, texto_limpio_final, texto_limpio_final, selectores['input_real'], lista_secundaria):
            return tipo_otros

        print("No hubo match valido en la lista. Activando Checkbox...")

    # =================================================================
    # PASO 3: ACTIVAR CHECKBOX
    # =================================================================
    if selectores.get('check'):
        try:
            chk_selector = selectores['check']
            estado_check = page.locator(
                chk_selector).evaluate("node => node.checked")

            if not estado_check:
                print(
                    f"Forzando clic en Checkbox '{chk_selector}' mediante JS...")
                page.locator(chk_selector).evaluate("node => node.click()")
                time.sleep(1.5)
            else:
                print("El checkbox ya estaba marcado.")
        except Exception as e:
            print(f"Error al forzar el checkbox: {e}")

    # =================================================================
    # PASO 4: ESCRITURA FORZADA Y DISPARO DE EVENTOS
    # =================================================================
    if selectores.get('input_real'):
        try:
            real_inp = page.locator(selectores['input_real'])

            real_inp.evaluate("node => node.value = ''")
            real_inp.fill("")
            time.sleep(0.5)

            print(f"Tipeando modelo final: '{texto_limpio_final}'")
            real_inp.press_sequentially(texto_limpio_final, delay=0.10)

            real_inp.evaluate(
                "node => node.dispatchEvent(new Event('change', { bubbles: true }))")
            real_inp.evaluate(
                "node => node.dispatchEvent(new Event('blur', { bubbles: true }))")
            page.keyboard.press('Tab')

            print(
                f"Modelo '{texto_limpio_final}' inyectado y guardado con exito.")
        except Exception as e:
            print(f"Error critico al escribir manualmente: {e}")

    return tipo_otros


# ==============================================================================
# Casos mapeados de modelos mal escritos en SAT
# ==============================================================================
reglas_sat = [
    {
        "modelo": "F-150",
        "version": "LARIAT FHEV",
        "f_rodante": "4X4",
        "modelo_sat": "F-150 LARIAT 4X4 FHEV"
    },
    {
        "modelo": "CR-V",
        "version": "EXL FHEV",
        "f_rodante": "",
        "modelo_sat": "CR-V EXL FHEV"
    },
    {
        "modelo": "CR-V",
        "version": "EXL",
        "f_rodante": "",
        "modelo_sat": "CR-V EX-L"
    },
    {
        "modelo": "FORESTER",
        "version": "2.0I AWD CVT XS SI DRIVE",
        "f_rodante": "",
        "modelo_sat": "FORESTER XS SI-DRIVE AWD 2.0I CVT"
    },
    {
        "modelo": "PARTNER",
        "version": "1.6 DIESEL CORTA 2AS",
        "f_rodante": "",
        "modelo_sat": "PARTNER 1.6 DISEL CORTA 2AS"
    },
    {
        "modelo": "TAOS",
        "version": "TAOS HIGHLINE 250 TSI, 1.4L, 2WD, TIP",
        "f_rodante": "",
        "modelo_sat": "TAOS HIGHLINE 2WD 1.4 250TSI TIP"
    },
    {
        "modelo": "JETTA",
        "version": "TRENDLINE 250TSI 1.4L TIP",
        "f_rodante": "",
        "modelo_sat": "JETTA TRENDLINE 250 TSI 1.4 TIP"
    },
    {
        "modelo": "JETTA",
        "version": "HIGHLINE 250TSI 1.4L TIP",
        "f_rodante": "",
        "modelo_sat": "JETTA HIGHLINE 250 TSI 1.4 TIP"
    },
    {
        "modelo": "Q8",
        "version": "BLACK S LINE 55 TFSI QUATTRO TIPTRONIC",
        "f_rodante": "",
        "modelo_sat": "Q8 BLACK S LINE 55 TFSI QUATRRO TIPTRONIC"
    },
    {
        "modelo": "C37",
        "version": "MINIBUS 1.5 L V2",
        "f_rodante": "",
        "modelo_sat": "C37 MINIBUS 1.5L V2"
    },
    {
        "modelo": "REFINE",
        "version": "NEW REFINE 2.0 VVT GASOLINA",
        "f_rodante": "",
        "modelo_sat": "NEW REFINE 2.0 VVT GASOLINA"
    },
    {
        "modelo": "BRONCO SPORT",
        "version": "BIG BEND 4X4 AT",
        "f_rodante": "",
        "modelo_sat": "BRONCO SPORT BID BEND 4X4 AT"
    },
    {
        "modelo": "MAZDA3",
        "version": "MAZDA 3 SPORT CORE 2.0 AT 2WD IPM IV E6B",
        "f_rodante": "",
        "modelo_sat": "MAZDA3 SPORT CORE 2.0 AT 2WD IPM IV E6B"
    },
    {
        "modelo": "MAZDA3",
        "version": "MAZDA 3 SPORT CORE 2.0 AT 2WD IPM IV E6B3",
        "f_rodante": "",
        "modelo_sat": "MAZDA3 SPORT CORE 2.0 AT 2WD IPM IV E6B3"
    },
    {
        "modelo": "SOLUTO",
        "version": "1.4 AT - LX PLUS",
        "f_rodante": "",
        "modelo_sat": "SOLUTO 1.4 AT  LX PLUS"
    },
    {
        "modelo": "CROSSTREK",
        "version": "2.0I AWD CVT",
        "f_rodante": "",
        "modelo_sat": "CROSSTREK 2.0 AWD CVT"
    },
    {
        "modelo": "T1",
        "version": "2.0T AWD 8AT B/O",
        "f_rodante": "",
        "modelo_sat": "T1 2.0T AWD 8AT BO"
    },
    {
        "modelo": "CS55",
        "version": "NEW CS55 PLUS FLAGSHIP 1.5 DCT",
        "f_rodante": "",
        "modelo_sat": "NEW CS55 4X2 1.5 DCT FLAGSHIP PLUS"
    },
]

# ==============================================================================
# Paso 2: Correccion casos mapeados
# ==============================================================================


def aplicar_reglas_sat(modelo_api, version_api, traccion_api):
    """
    Recibe los datos crudos. Busca en 'reglas_sat'.
    Si hay coincidencia, devuelve (Texto_Corregido, "").
    Si no hay coincidencia, devuelve los datos crudos intactos.
    """
    mod_filtro = (modelo_api or "").strip().upper()
    ver_filtro = (version_api or "").strip().upper()
    trac_filtro = (traccion_api or "").strip().upper()

    # =================================================================
    # 1. (Modelos Intocables)
    # =================================================================
    # Unimos el modelo y la versión para evaluar la cadena completa
    nombre_completo_api = f"{mod_filtro} {ver_filtro}".strip()

    # Agrega más aquí si el SAT te vuelve a cortar otros modelos en el futuro
    modelos_intocables = [
        "CROSSTREK 2.0I AWD CVT PLUS",
    ]

    for intocable in modelos_intocables:
        # Si el modelo intocable está dentro del texto completo de la API
        if intocable in nombre_completo_api:
            print(
                f" Modelo blindado detectado '{intocable}'. Ignorando reglas_sat.")
            # Lo retornamos crudito, tal cual como entró, ignorando la parte de abajo
            return mod_filtro, ver_filtro

    # =================================================================
    # 2. BÚSQUEDA EN REGLAS SAT (Tu código original)
    # =================================================================
    # Usamos next() como el .find() de JavaScript leyendo la variable global reglas_sat
    regla_encontrada = next(
        (item for item in reglas_sat
         if (item.get("modelo", "").upper() in mod_filtro)
         and (item.get("version", "").upper() in ver_filtro)
         and (not item.get("f_rodante") or item.get("f_rodante", "").upper() in trac_filtro)
         ),
        None
    )

    if regla_encontrada:
        print(
            f" [CASO MAPEADO]: MODELO ENCONTRADO EN LA LISTA. CAMBIANDO A: '{regla_encontrada['modelo_sat']}'")
        # El truco: Mandamos el texto perfecto en la variable modelo, y vaciamos la versión
        return regla_encontrada["modelo_sat"], ""

    # Si es un carro normal sin problemas, lo dejamos pasar igual
    return mod_filtro, ver_filtro

# ==============================================================================
# Paso 3: Selectores modelo
# ==============================================================================


def encontrar_modelo(page, modelo, version, formulaRodante="", peso_bruto=None):
    # 1er PASO: Pasar por la aduana ANTES de hacer cualquier cosa en la web
    modelo, version = aplicar_reglas_sat(modelo, version, formulaRodante)

    sel = {
        'input': "#txtDesModelo",
        'lista_items': "#ui-id-2 > li",
        'check': "#chkNueModelo",
        'input_real': "#txtDesModeloReal"
    }

    # 2do PASO: Generar variantes con lo que sea que haya salido de la aduana
    texto_con_dup, texto_sin_dup = obtener_variantes_texto(modelo, version)

    # 3er PASO: Intentar teclear en el SAT
    if interactuar_y_buscar(page, texto_con_dup, texto_sin_dup, sel['input'], sel['lista_items']):
        return True

    # 4to PASO: Si el SAT no lo encuentra, activar el salvavidas manual
    print(" Pasando a manual...")
    # AQUÍ PASAMOS EL PESO AL CEREBRO
    tipo_otros = detectar_tipo_otros_modelos(page, peso_bruto)

    # EXCEPCIÓN DE FALLBACK FINAL (TERRAMAR)
    texto_unido = f"{modelo} {version}".upper()
    if "TERRAMAR" in texto_unido:
        print(
            " [EXCEPCIÓN ACTIVADA]: Forzando la categoría 'OTROS MODELOS' para Terramar.")
        tipo_otros = "OTROS MODELOS"

    return flujo_seleccionar_otros(page, tipo_otros, texto_sin_dup, sel)


def encontrar_modelo2(page, modelo, version, seleccion_previa=None, formulaRodante="", peso_bruto=None):
    print(f" [Popup] Validando datos en aduana...")
    # 1er PASO: Pasar por la aduana
    modelo, version = aplicar_reglas_sat(modelo, version, formulaRodante)

    sel = {
        'input': "#txtDesModeloV",
        'lista_items': "#ui-id-6 > li",
        'check': None,
        'input_real': None
    }

    texto_con_dup, texto_sin_dup = obtener_variantes_texto(modelo, version)

    # ATAJO DE "OTROS MODELOS" (Se mantiene intacto)
    if isinstance(seleccion_previa, str) and "OTROS MODELOS" in seleccion_previa.upper():
        print(
            f" ATAJO ACTIVADO: La selección previa fue '{seleccion_previa}'.")
        print(f"   -> Escribiendo fielmente: {texto_sin_dup}")
        return flujo_seleccionar_otros(page, seleccion_previa, texto_sin_dup, sel)

    print(f" [Popup] Iniciando búsqueda...")
    if interactuar_y_buscar(page, texto_con_dup, texto_sin_dup, sel['input'], sel['lista_items']):
        return True

    print(" Pasando a manual en Popup...")
    # AQUÍ PASAMOS EL PESO AL CEREBRO
    tipo_otros = detectar_tipo_otros_modelos(page, peso_bruto)

    # EXCEPCIÓN DE FALLBACK FINAL (TERRAMAR) PARA EL POPUP
    texto_unido = f"{modelo} {version}".upper()
    if "TERRAMAR" in texto_unido:
        print(
            " [EXCEPCIÓN ACTIVADA]: Forzando la categoría 'OTROS MODELOS' para Terramar.")
        tipo_otros = "OTROS MODELOS"

    return flujo_seleccionar_otros(page, tipo_otros, texto_sin_dup, sel)


def agregarcompradores(page):
    page.go_back()
    page.locator("#btnRegresar").click()
    page.locator("#btnRegresar").click()
    page.locator("#dgDeclaraciones_lnkPorcentaje_0 > img").click()


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
        Registrador.info(
            f"Enviando inmatriculación con ambos archivos: cambio domicilio y declaración jurada")
    else:
        estructura = {
            "TramitId": inmatriculacion,
            "cliente": dni,
            "file": "",
            "file2": archivo_declaracionJurada
        }
        Registrador.info(
            f"Enviando inmatriculación solo con declaración jurada (sin cambio de domicilio)")

    try:
        Registrador.info(f"Enviando correo electrónico a la API: {url}")
        Registrador.debug(f"Estructura de la inmatriculacion: {estructura}")

        response = requests.post(url, json=estructura)

        if response.status_code == 200:
            Registrador.info(
                f"Inmatriculacion enviado exitosamente. Código de estado: {response.status_code}")
            Registrador.debug(f"Respuesta de la API: {response.json()}")

            # Email de éxito
            destinos = ["practicantes.sistemas@notariapaino.pe",
                        "jmallqui@notariapaino.pe"]
            if tiene_domicilio:
                asunto = f"TEST BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Ambos archivos"
                mensaje = f"<p>Se envió la inmatriculación N°{inmatriculacion} por el APISAT con ambos archivos (cambio domicilio y declaración jurada).</p>"
            else:
                asunto = f"TEST BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Solo declaración"
                mensaje = f"<p>Se envió la inmatriculación N°{inmatriculacion} por el APISAT solo con declaración jurada (sin cambio de domicilio).</p>"

            enviar_email_Api(destinos, asunto, mensaje)
            return response

        elif response.status_code == 400:
            Registrador.error(
                f"Error al enviar la inmatriculacion. Código de estado: {response.status_code}. Verifique los datos enviados.")
            Registrador.debug(
                f"Respuesta de la API (error 400): {response.text}")

            # Email de error 400
            destinos = ["practicantes.sistemas@notariapaino.pe",
                        "jmallqui@notariapaino.pe"]
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Error 400"
            error_message = f"<p>Error 400 al enviar la inmatriculación N°{inmatriculacion} por el APISAT.</p><p>Respuesta: {response.text}</p>"
            enviar_email_Api(destinos, asunto, error_message)
            return response

        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        Registrador.error(f"Error al enviar la inmatriculacion a la API: {e}")
        destinos = ["practicantes.sistemas@notariapaino.pe",
                    "jmallqui@notariapaino.pe"]

        if tiene_domicilio:
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Ambos archivos"
            error_message = f"<p>Hubo un error al enviar la inmatriculación con ambos archivos por el APISAT.</p><p>Error: {e}</p>"
        else:
            asunto = f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculacion} - Solo declaración"
            error_message = f"<p>Hubo un error al enviar la inmatriculación solo con declaración jurada por el APISAT.</p><p>Error: {e}</p>"

        Registrador.error(
            f"Hubo un error al enviar la inmatriculacion por el APISAT. Error: {e}")
        print(traceback.format_exc())
        enviar_email_Api(destinos, asunto, error_message)
        return None

    except Exception as e:
        Registrador.error(
            f"Error inesperado al enviar la inmatriculacion a la API: {e}")
        destinos = ["practicantes.sistemas@notariapaino.pe",
                    "jmallqui@notariapaino.pe"]

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
    carpeta_inmatriculacion = os.path.join(
        carpeta_base_proyecto, str(inmatriculacion))
    os.makedirs(carpeta_inmatriculacion, exist_ok=True)

    # RUTA ARCHIVOS
    archivo_declaracion = os.path.join(
        carpeta_inmatriculacion, f"ArchivoDeclaracion_{inmatriculacion}_{dni}.pdf")
    archivo_cambioDomicilio = os.path.join(
        carpeta_inmatriculacion, f"ArchivoCambioDomicilio_{inmatriculacion}_{dni}.pdf")

    # INICIALIZAR VARIABLES
    existe_boton_cambio_domicilio = False
    archivo_declaracion_base64 = ""
    archivo_cambioDomicilio_base64 = ""

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

            html_cambioDomicilio = page.inner_html("#form1 > div:nth-child(4)")

            with open(archivo_cambioDomicilio, "wb") as pdf:
                pisa_status = pisa.CreatePDF(html_cambioDomicilio, dest=pdf)
                if pisa_status.err:
                    raise Exception(
                        "La librería pisa falló al crear el PDF del Cambio de Domicilio")

            print(
                f"PDF del cambio domicilio guardado en: {archivo_cambioDomicilio}")
            Registrador.info(
                f"PDF del cambio domicilio guardado en: {archivo_cambioDomicilio}")

            with page.expect_navigation(wait_until='load'):
                page.locator("#btnRegresar").click()

        except Exception as e:
            #  FRENO DE EMERGENCIA 1: Muere si falla el Domicilio
            mensaje_error = f" ERROR CRÍTICO: Falló la descarga de documentos (Cambio de Domicilio). Finalizando bot. Volver a procesar la inmatriculación: {inmatriculacion}. Detalle: {e}"
            print(mensaje_error)
            Registrador.error(mensaje_error)
            raise Exception(mensaje_error)
    else:
        print(" Saltando proceso de cambio de domicilio - botón no encontrado")

    # =================================================================
    # 1. GENERACIÓN DE PDF (Declaración Jurada)
    # =================================================================
    try:
        print("Procesando declaración jurada...")
        parte1 = page.inner_html(
            "#DivImpresion > table > tbody > tr > td > table:nth-child(1)")
        parte2 = page.inner_html(
            "#DivImpresion > table > tbody > tr > td > table:nth-child(2)")
        parte3 = page.inner_html(
            "#DivImpresion > table > tbody > tr > td > table:nth-child(3)")

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
        nueva_pagina.pdf(path=archivo_declaracion,
                         format="A4", print_background=False)
        nueva_pagina.close()

        print(f" PDF de declaración guardado en: {archivo_declaracion}")
        Registrador.info(
            f"PDF de declaración guardado en: {archivo_declaracion}")

    except Exception as e:
        mensaje_error = f" ERROR CRÍTICO: Falló la generación del PDF. Volver a procesar: {inmatriculacion}. Detalle: {e}"
        print(mensaje_error)
        Registrador.error(mensaje_error)
        raise Exception(mensaje_error)  # Frenamos todo si no hay PDF

    # =================================================================
    # 2. LECTURA DE DECLARACIÓN JURADA A BASE64
    # =================================================================
    try:
        with open(archivo_declaracion, 'rb') as archivo_declaracion_file:
            archivo_declaracion_bytes = archivo_declaracion_file.read()
            archivo_declaracion_base64 = base64.b64encode(
                archivo_declaracion_bytes).decode('utf-8')
    except Exception as e:
        mensaje_error = f" ERROR CRÍTICO: No se pudo leer el PDF de Declaración para Base64. Volver a procesar: {inmatriculacion}. Detalle: {e}"
        print(mensaje_error)
        Registrador.error(mensaje_error)
        raise Exception(mensaje_error)

    # =================================================================
    # 3. LECTURA DE CAMBIO DE DOMICILIO A BASE64 (Solo si existe el botón)
    # =================================================================
    if existe_boton_cambio_domicilio:
        try:
            with open(archivo_cambioDomicilio, 'rb') as archivo_cambioDomicilio_file:
                archivo_cambioDomicilio_bytes = archivo_cambioDomicilio_file.read()
                archivo_cambioDomicilio_base64 = base64.b64encode(
                    archivo_cambioDomicilio_bytes).decode('utf-8')
        except Exception as e:
            mensaje_error = f" ERROR CRÍTICO: No se pudo leer el PDF de Cambio Domicilio para Base64. Volver a procesar: {inmatriculacion}. Detalle: {e}"
            print(mensaje_error)
            Registrador.error(mensaje_error)
            raise Exception(mensaje_error)

    # =================================================================
    # 4. SALVAVIDAS JSON (Respaldo local)
    # =================================================================
    print("\n Salvaguardando JSON del vehículo...")

    data = {
        "inmatriculacion": inmatriculacion,
        "cliente": dni,
        "file_cambio_domicilio": archivo_cambioDomicilio_base64,
        "file_declaracion_jurada": archivo_declaracion_base64
    }

    if existe_boton_cambio_domicilio:
        print("Preparando datos con ambos archivos (cambio domicilio y declaración)")
    else:
        print("Preparando datos solo con declaración jurada (sin cambio de domicilio)")

    json_output = json.dumps(data, indent=4)
    Namejson = f"DATOS_DEL_VEHICULO{inmatriculacion}_{dni}.json"
    ruta_archivo_json = os.path.join(carpeta_inmatriculacion, Namejson)

    try:
        with open(ruta_archivo_json, "w") as f_json:
            f_json.write(json_output)
        print(f" JSON guardado localmente en: {ruta_archivo_json}\n")
    except Exception as e_json:
        print(f" Error al guardar el JSON de respaldo: {e_json}\n")

    # =================================================================
    # 5. ENVÍO A LA API
    # =================================================================
    try:
        print("Enviando documentos a la API...")
        enviar_inmatriculacion(
            inmatriculacion, dni, archivo_cambioDomicilio_base64, archivo_declaracion_base64)
        print("Envío a la API completado con éxito.")
    except Exception as e:
        mensaje_error = f" ERROR CRÍTICO: Falló la comunicación con la API (enviar_inmatriculacion) para la placa {inmatriculacion}. Detalle: {e}"
        print(mensaje_error)
        Registrador.error(mensaje_error)
        raise Exception(mensaje_error)

    time.sleep(3)


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
        Registrador.error(
            f"Error al intentar regresar al menú de inscripción: {e}")
        print(f"Error al intentar regresar al menú de inscripción: {e}")


def combinar_modelo_version(modelo, version):
    if modelo and version:  # Evitar errores si alguno está vacío
        if modelo.lower() in version.lower():
            return version.strip()
        else:
            return f"{modelo} {version}".strip()
    return version or modelo or ""
