import time
import re
from playwright.sync_api import Page

# ==============================================================================
# 1. HERRAMIENTAS DE TEXTO
# ==============================================================================

def obtener_token_sinonimo(palabra):
    """ Estandariza palabras clave (Tokens). """
    p = palabra.upper().strip()
    
    # --- REGLA: MODELO (Normalización de Litros) ---
    # Si detecta números como "1.5L" o "2000L", quita la L para
    # que coincida con "1.5" o "2000" en la lista del SAT.
    if re.match(r"^\d+(\.\d+)?L$", p):
        return p[:-1] 

    # Diccionario de sinónimos
    if p in ["4X2", "2WD", "SIMPLE", "S-AWD", "TRACCION SIMPLE", "TRACCIÓN SIMPLE"]: return "TOKEN_TRACCION_SIMPLE"
    if p in ["4X4", "AWD", "4WD", "QUATTRO", "DOBLE", "XDRIVE", "TRACCION DOBLE", "TRACCIÓN DOBLE"]: return "TOKEN_TRACCION_DOBLE"
    
    # Abreviaturas
    if p in ["DLX", "DELUXE"]: return "TOKEN_DELUXE"
    if p in ["LTD", "LIMITED"]: return "TOKEN_LIMITED"
    if p in ["STD", "STANDARD"]: return "TOKEN_STANDARD"
    if p in ["AUT", "AUTOMATICO", "AT"]: return "TOKEN_AUTOMATICO"
    if p in ["MEC", "MECANICO", "MT"]: return "TOKEN_MECANICO"

    return p 

def normalizar_texto(texto):
    """ Convierte texto en tokens para comparación (Respeta la barra '/'). """
    if not texto: return set()
    
    # Solo quitamos guiones (-). La barra (/) y puntos (.) se quedan.
    texto_limpio = texto.upper().replace("-", " ").strip()
    
    tokens = set()
    for palabra in texto_limpio.split():
        tokens.add(obtener_token_sinonimo(palabra))
    return tokens

def formatear_nombre_busqueda(modelo, version):
    """ Une Modelo y Versión (Aplica regla 'SIN VERSION'). """
    m = (modelo or "").strip().upper()
    v = (version or "").strip().upper()
    
    # --- REGLA: SIN VERSION ---
    # Si la versión no aporta info real, usamos solo el modelo.
    if v in ["SIN VERSION", "SIN VERSIÓN", "S/V", "SIN V", "NO APLICA"]:
        return m

    # Si el modelo ya está incluido en la versión, usamos solo la versión
    if m.replace("-", " ") in v.replace("-", " "):
        return v
        
    return f"{m} {v}".strip()

def limpiar_texto_para_input(texto):
    """ Prepara el texto para escribirlo en el navegador. """
    if not texto: return ""
    
    texto_upper = texto.upper()
    
    # --- REGLA: MODELO (Escritura sin Litros) ---
    # Quitamos la 'L' de litros al escribir para que el filtro web sea más amplio.
    # (Ej: Escribimos "1.5" en vez de "1.5L")
    texto_sin_litros = re.sub(r"\b(\d+(\.\d+)?)L\b", r"\1", texto_upper)
    
    # Quitamos palabras que rompen el filtro web
    palabras_prohibidas = ["DLX", "LTD", "STD", "AUT", "MEC", "FULL", "GLP", "GNV"] 
    
    # Solo quitamos guiones (-). La barra (/) se queda.
    texto_limpio = texto_sin_litros.replace("-", " ")
    
    return " ".join([p for p in texto_limpio.split() if p not in palabras_prohibidas])

# ==============================================================================
# 2. HERRAMIENTAS DE NAVEGACIÓN
# ==============================================================================

def detectar_tipo_otros_modelos(page):
    """ Decide si es Auto, Camioneta Simple o Doble. """
    try:
        val_clase = page.locator("#ddlClase").input_value()
        
        if val_clase == "1": return "OTROS MODELOS" # Automóvil
        
        elif val_clase == "11": # Camioneta
            txt = ""
            try: txt = page.locator("#ddlTraccion option:checked").inner_text().upper()
            except: pass
            
            if any(k in txt for k in ["4X4", "AWD", "4WD", "QUATTRO", "DOBLE"]):
                return "OTROS MODELOS TRACCIÓN DOBLE"
            else:
                return "OTROS MODELOS TRACCIÓN SIMPLE"
                
        return "OTROS MODELOS"
    except: return "OTROS MODELOS"

def interactuar_y_buscar(page, texto_original, selector_input, selector_items_lista):
    """ Escribe, espera y selecciona la MEJOR coincidencia. """
    
    # 1. Escribir
    texto_seguro = limpiar_texto_para_input(texto_original)
    print(f"✍️ Escribiendo: '{texto_seguro}' en {selector_input}")
    
    try:
        page.locator(selector_input).fill("")
        page.locator(selector_input).press_sequentially(texto_seguro, delay=100)
    except: return False

    # 2. Esperar (4 seg para principal, 2 seg para secundario)
    tiempo = 2 if "ui-autocomplete" in selector_items_lista else 4
    print(f"⏳ Esperando lista ({tiempo}s)...")
    time.sleep(tiempo)
    
    try:
        if not page.is_visible(selector_items_lista): return False
    except: return False

    # 3. Buscar Candidato
    try:
        opciones = page.query_selector_all(selector_items_lista)
        tokens_buscados = normalizar_texto(texto_original)
        candidatos = []

        for op in opciones:
            texto_opcion = op.inner_text().strip()
            tokens_opcion = normalizar_texto(texto_opcion)

            if tokens_buscados.issubset(tokens_opcion):
                # Preferimos la opción con menos palabras sobrantes (Más exacta)
                diff = len(tokens_opcion) - len(tokens_buscados)
                candidatos.append({'elem': op, 'txt': texto_opcion, 'diff': diff})

        if candidatos:
            candidatos.sort(key=lambda x: x['diff'])
            mejor = candidatos[0]
            
            print(f"✅ Coincidencia: '{mejor['txt']}'")
            time.sleep(0.5)
            mejor['elem'].click()
            return True
        else:
            print(f"⚠️ No se encontró en lista: {texto_original}")

    except Exception as e:
        print(f"⚠️ Error búsqueda: {e}")

    return False

def flujo_seleccionar_otros(page, tipo_otros, nombre_real, selectores):
    """ Fallback: Otros -> Buscar en Input Real -> Crear Nuevo. """
    print(f"🔄 Activando fallback: '{tipo_otros}'")
    
    # A. Seleccionar "OTROS..." en input principal
    if not interactuar_y_buscar(page, tipo_otros, selectores['input'], selectores['lista_items']):
        return None
        
    time.sleep(1)
    
    # B. Intentar buscar en el Input Real (si existe)
    if selectores.get('input_real'):
        print(f"🔎 Buscando '{nombre_real}' en catálogo secundario...")
        # Buscamos en cualquier lista visible (genérica)
        lista_secundaria = "ul.ui-autocomplete:visible > li"
        
        if interactuar_y_buscar(page, nombre_real, selectores['input_real'], lista_secundaria):
            print("🎉 Encontrado en lista secundaria. No es necesario crear nuevo.")
            return tipo_otros 

    # C. Si no está, marcar Check y Escribir (si aplica)
    if selectores.get('check'):
        try:
            chk = page.locator(selectores['check'])
            if chk.is_visible() and not chk.is_checked(): chk.check()
        except: pass

    if selectores.get('input_real'):
        try:
            real_inp = page.locator(selectores['input_real'])
            real_inp.fill("")
            real_inp.press_sequentially(nombre_real, delay=100)
            print(f"📝 Nombre escrito manualmente: {nombre_real}")
        except: pass
    
    return tipo_otros

# ==============================================================================
# 3. FUNCIONES PRINCIPALES
# ==============================================================================

def encontrar_modelo(page, modelo, version):
    sel = {
        'input': "#txtDesModelo", 
        'lista_items': "#ui-id-2 > li",
        'check': "#chkNueModelo",       
        'input_real': "#txtDesModeloReal" 
    }
    nombre_busqueda = formatear_nombre_busqueda(modelo, version)
    
    if interactuar_y_buscar(page, nombre_busqueda, sel['input'], sel['lista_items']):
        return nombre_busqueda
    
    print("⚠️ No encontrado. Pasando a Otros...")
    tipo_otros = detectar_tipo_otros_modelos(page)
    return flujo_seleccionar_otros(page, tipo_otros, nombre_busqueda, sel)

def encontrar_modelo2(page, modelo, version):
    sel = {
        'input': "#txtDesModeloV", 
        'lista_items': "#ui-id-6 > li",
        'check': None,      
        'input_real': None  
    }
    nombre_busqueda = formatear_nombre_busqueda(modelo, version)
    print(f"🔎 [Popup] Buscando: '{nombre_busqueda}'")

    if interactuar_y_buscar(page, nombre_busqueda, sel['input'], sel['lista_items']):
        return nombre_busqueda
    
    print("⚠️ No encontrado en Popup. Seleccionando Otros...")
    tipo_otros = detectar_tipo_otros_modelos(page) 
    return flujo_seleccionar_otros(page, tipo_otros, nombre_busqueda, sel)