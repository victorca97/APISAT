import json
from utils.loggers import Registrador
from datetime import datetime
import time
from utils.common import *
from middleware.re_email import enviar_email_Api
import traceback
from playwright.sync_api import Page, expect

#-----------------------------------------------PERSONA NATURAL SIN REPRESENTANTE-------------------------------------------------
def natural_sin_representante(referencia,comprador_info:dict,data,page:Page,browser,inmatriculaciones,compradores_array):
    try:
        json_formateado = json.dumps(data, indent=4, ensure_ascii=False)

        tipo_persona = comprador_info.get('tipoPersona', None)
        tipo_documento = comprador_info.get('tipoDocumento', None)
        num_documento = comprador_info.get('numDocumento', None)
        celular = comprador_info.get('celular', None)
        correoElectronico = comprador_info.get('correoElectronico', None)
        fecha_nacimiento = comprador_info.get('fechaDeNacimiento', "")
        #fecha_nacimiento = comprador_info.get('fechaDeNacimiento', None)
        domicilio_fiscal:dict = comprador_info.get('domicilioFiscal', {})
        distrito = domicilio_fiscal.get('distrito')
        direccion = domicilio_fiscal.get('direccion')
        apellido_paterno = comprador_info.get('apellidoPaterno')
        apellido_materno = comprador_info.get('apellidoMaterno')
        nombre=comprador_info.get('nombres')
        razon_social = comprador_info.get('razonSocial', None)
        tieneRepresentante = comprador_info.get('tieneRepresentante', None)

        # Acceder a la información de 'adquisicion'
        adquisicion_info: dict = comprador_info.get('adquisicion', {})
        fechaInscripcion = adquisicion_info.get('fecha_inscripcion')
        tipodeadquisicion = adquisicion_info.get('tipoDeAdquisicion')
        fechasAdquisicion_factura_cancelacion = adquisicion_info.get('fechasAdquisicion_factura_cancelacion')
        condicionDePropiedad = adquisicion_info.get('condicionDePropiedad')
        moneda = adquisicion_info.get('moneda')
        valorMonetario = adquisicion_info.get('valorMonetario')
        datos_transferente:dict = adquisicion_info.get('datosDelTransferente', {})
        distritoUbicacion = datos_transferente.get('distritoUbicacion',None)


        #DATOS DEL VEHICULO
        vehiculo_data:dict = data.get('vehiculo', {})
        categoriaMtc = vehiculo_data.get('categoriaMtc', '')
        carroceria = vehiculo_data.get('carroceria', '')
        anoModelo = vehiculo_data.get('anoModelo', '')
        modelos = vehiculo_data.get('modelo', '')
        version= vehiculo_data.get('version', '')
        marcas = vehiculo_data.get('marca', '')
        nroMotor = vehiculo_data.get('nroMotor', '')
        nAsientos = vehiculo_data.get('nAsientos', '')
        combustible = vehiculo_data.get('combustible', '')
        cilindraje = vehiculo_data.get('cilindraje', '')
        formulaRodante = vehiculo_data.get('formulaRodante', '')
        pesoBruto = vehiculo_data.get('pesoBruto', '')
        transmision = vehiculo_data.get('transmision', '')

        if not tipo_persona :
            Registrador.error(f"No se encontro el dni de la persona de la inmatriculacion° {inmatriculaciones}")
            raise ValueError(f"El numero del documento esta vacio o no existe de la inmatriculacion°{inmatriculaciones}")

        if not isinstance(pesoBruto,int):
            raise ValueError(f"El campo peso bruto '{pesoBruto}' debe ser un número (entero). Se recibió: {repr(pesoBruto)}")
        
        if not isinstance(cilindraje,int):
            raise ValueError(f"El campo  cilindraje'{cilindraje}' debe ser un número (entero). Se recibió: {repr(cilindraje)}")
        

        if len(direccion) < 7 :
            Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 7 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
            raise ValueError(f"La dirección de la Empresa '{direccion}' es muy corta debe tener al menos 7 caracteres. El cliente es {nombre} con el DNI {num_documento}")
        

        try:
            page.select_option("#ddlTipoAdministrado", value=tipo_persona)
            page.select_option("#ddlTipoDocuAdmi", value=tipo_documento)
            page.keyboard.press('Tab')

            print(f"Buscando documento: {num_documento}")
            page.locator("input[name='txtDocuAdmi']").fill(num_documento)
            
            # ==========================================================
            # 1. PRIMERA BÚSQUEDA EN EL SAT
            # ==========================================================
            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass
            
            page.wait_for_timeout(2000) # Tiempo para que cargue la info
            page.keyboard.press('Tab')

            # Capturamos lo que el SAT trajo a la pantalla
            sat_paterno = page.locator("#txtApePateAdmi").input_value().strip()
            sat_materno = page.locator("#txtApeMateAdmi").input_value().strip()
            sat_nombre = page.locator("#txtNombAdmi").input_value().strip()

            # ==========================================================
            # 2. VALIDACIÓN Y SEGUNDA BÚSQUEDA
            # ==========================================================
            usar_nombres_api = False # Variable de control

            if sat_paterno != apellido_paterno or sat_materno != apellido_materno or sat_nombre != nombre:
                # CASO A: El SAT no trajo absolutamente nada (ej. Extranjeros nuevos)
                if not sat_paterno and not sat_nombre:
                    Registrador.warning("El SAT no devolvió nombres. Se forzará el uso de la información de la API.")
                    usar_nombres_api = True
                    
                # CASO B: El SAT trajo un nombre distinto a la API (Rafael vs Raphael)
                else:
                    Registrador.info("Discrepancia detectada. Realizando segunda búsqueda para confirmar nombre oficial (RENIEC)...")
                    
                    # Manejo de alerta por si el SAT lanza un popup en el segundo intento
                    page.once("dialog", lambda dialog: dialog.accept()) 
                    page.locator("input[name='cmdBuscaDocuAdmi']").click()
                    page.wait_for_timeout(3000) # Damos 3 segundos para confirmar
                    
                    # ==========================================================
                    # 🚨 INYECCIÓN DE SEGURIDAD: ÚLTIMA LECTURA
                    # ==========================================================
                    sat_paterno2 = page.locator("#txtApePateAdmi").input_value().strip()
                    sat_materno2 = page.locator("#txtApeMateAdmi").input_value().strip()
                    sat_nombre2 = page.locator("#txtNombAdmi").input_value().strip()
                    
                    if sat_paterno2 != apellido_paterno or sat_materno2 != apellido_materno or sat_nombre2 != nombre:
                        Registrador.warning("El SAT insiste con nombres distintos. ¡Forzando datos de la API!")
                        usar_nombres_api = True
                    else:
                        Registrador.info("La segunda búsqueda corrigió los nombres. Todo en orden.")
            else:
                print("✅ Los nombres de la API coinciden con el SAT.")

            # ==========================================================
            # 3. LLENADO DE NOMBRES Y APELLIDOS
            # ==========================================================
            if usar_nombres_api:
                # PLAN B: Llenamos manualmente porque el SAT estaba vacío
                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)
                
                if not apellido_materno:
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                    
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                    
                nombre_a_validar = nombre
                page.locator("input[name='txtNombAdmi']").fill(nombre)
            
            else:
                # PLAN A: Dejamos el nombre oficial que el SAT ya puso en las cajas.
                # Solo validamos si trajo apellido materno para marcar el check si hace falta.
                sat_materno_final = page.locator("#txtApeMateAdmi").input_value().strip()
                if not sat_materno_final:
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                
                # Guardamos el nombre final del SAT para contar sus letras
                nombre_a_validar = page.locator("#txtNombAdmi").fill(nombre)
                
                # 2. Extraemos el texto real que está dentro de la caja
                nombre_a_validar = page.locator("#txtNombAdmi").input_value()

            # Validación del límite de 30 caracteres
            if len(nombre_a_validar) > 30:
                Registrador.warning(f"El nombre a ingresar excede los 30 caracteres (Longitud actual: {len(nombre_a_validar)}). Se intentará enviar de todas formas.")

            # ==========================================================
            # 4. LLENADO DEL RESTO DE DATOS (SIEMPRE MANDA LA API)
            # ==========================================================
            # Teléfonos y Correo
            page.locator("input[name='txtTelefono1']").fill("") # Limpiamos fijo
            page.locator("input[name='txtTelefono2']").fill(celular)
            page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)

            # Distrito y Dirección
            if page.is_enabled("#ddlDistrito"):
                page.select_option("#ddlDistrito", value=distrito)
                page.locator("input[name='txtDireccion']").fill(direccion)
            else:
                Registrador.warning("El combo de distrito no está habilitado en el SAT.")

            # Fecha de Nacimiento
            if fecha_nacimiento:
                try:
                    # Convertimos 'YYYY-MM-DD' a 'DD/MM/YYYY' en una sola línea
                    fecha_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").strftime("%d/%m/%Y")
                    print(f"Fecha de nacimiento a ingresar: {fecha_formateada}")
                    page.locator("input[name='txtFecNacPersona']").fill(fecha_formateada)
                except ValueError as e:
                    Registrador.error(f"Error al procesar la fecha de nacimiento ({fecha_nacimiento}): {e}")
            else:
                Registrador.warning("No llegó fecha de nacimiento en la API. Campo omitido.")

            # ==========================================================
            # 5. FINALIZACIÓN
            # ==========================================================
            page.select_option("#ddlTipoRelacionado", value="0")

            input("Corrige la dirección u otro dato si es necesario y presiona Enter para continuar...")
            Registrador.info("Terminé la primera hoja de persona natural.")

            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnSiguiente']").click()

            page.wait_for_load_state()
            time.sleep(5)

        except Exception as e:
            Registrador.error(f"Error crítico en el bloque de llenado de persona natural: {e}")
            page.locator("#lnkRegresar").click()
            raise
    
    
        #DATOS DEL VEHICULO------------------
            
            #fechaInscripcion1 = datetime.strptime(fechaInscripcion, "%Y-%m-%d")  
            # Formatear el objeto datetime a la cadena deseada (día-mes-año)

        try:
            # input("Ingresar fecha de inscripcion...")
            fecha_formateada = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
            fecha_formateada = fecha_formateada.strftime("%d-%m-%Y")
            fecha_formateada = fecha_formateada.replace("-", "/")
            print(fecha_formateada)
            page.locator("input[name='txtInscripcion']").fill(fecha_formateada)

            page.locator("input[name='txtAnoModelo']").fill(anoModelo)
            page.keyboard.press("Enter")                

            value_categoriaMtc=categoria(categoriaMtc)
            page.select_option("#ddlCatMTC",value=str(value_categoriaMtc))

            valuecarroceria=encontrar_carroceria(page,carroceria)
            page.select_option("#ddlCarroceria",value=valuecarroceria)

            #page.locator("input[name='txtAnoFabrica']").fill(anoFabricacion)

            time.sleep(2)
            # page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=100)
            time.sleep(2)

            if not encontrar_marca(page,marcas):
                raise ValueError("Marca no encontrada")

            time.sleep(2)
            # Validacion de nroMotor
            if " " in str(nroMotor):
                print("*" * 40)
                print("*" * 40)
                print("*" * 40)
                print("*" * 40)
                print("CAMBIO REALIZADO")
                print("*" * 40)
                print("*" * 40)
                print("*" * 40)
                print("*" * 40)

            # 3. Limpiamos el dato y lo escribimos en la web
            nroMotor_limpio = str(nroMotor).replace(" ", "")
            page.locator("input[name='txtMotor']").fill(nroMotor_limpio)
            
            
            page.locator("input[name='txtNroAsientos']").fill(nAsientos)

            value_combustible=encontrar_combustible(combustible)
            page.select_option("#ddlTipoMotor",value=str(value_combustible))
            
            formulaRodante1=encontrar_formulaRodante(formulaRodante)
            page.select_option("#ddlTraccion",value=str(formulaRodante1))

            #rpt_cilindraje=int(cilindraje)*1000
            try:
                cilindraje_int = int(cilindraje)
            except ValueError:
                cilindraje_int = 0  # Manejo de error si no es número

            # 2. APLICAMOS LA CORRECCIÓN DE CEROS EXTRAS
            # Si es mayor a 20,000 (ningún auto normal pasa de 10k-12k cc), asumimos error de formato
            if cilindraje_int > 50000: 
                cilindraje_int = cilindraje_int // 1000  # División entera: 1995000 -> 1995

            # 3. Tu lógica de llenado (usando la variable corregida)
            if cilindraje_int == 0:
                page.locator("#txtCilindraje").fill("1")
            elif cilindraje_int > 0:
                page.locator("#txtCilindraje").fill(str(cilindraje_int))


            #rpt_pesobruto=int(pesoBruto) * 1000
            page.locator("input[name='txtPesoBruto']").fill(str(int(pesoBruto)))
            page.keyboard.press("Enter")


            value_T=encontrar_transmision(transmision)
            page.select_option("#ddlTransmision",value=str(value_T))

            page.locator("#btnDetermClaseCat").click
            page.wait_for_timeout(2000)
        
            # Opcional: Solo para tu control en consola (no afecta la lógica)
            clase_vehiculo = page.locator("#ddlClase").input_value()
            print(f"ℹ️ Clase detectada antes de buscar modelo: {clase_vehiculo}")
            
            # Seleccionar modelo ULTIMO PASO
            v_modelos=f"{modelos}".strip()
            time.sleep(2)
            page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=30)
            v_modeloCompleto = combinar_modelo_version(modelos, version)
            
            time.sleep(2)
            resultado_seleccion = encontrar_modelo(page, modelos, version, formulaRodante=formulaRodante, peso_bruto=pesoBruto)
            


            #DATOS DE LA ADQUISICION------------------
            page.select_option("#ddlTipoTransferencia",value={tipodeadquisicion})

            fechaAdquisicion = datetime.strptime(fechasAdquisicion_factura_cancelacion, "%Y-%m-%d")
            fecha_formateada1 = fechaAdquisicion.strftime("%d-%m-%Y")
            fecha_formateada1 = fecha_formateada1.replace("-", "/")
            print(fecha_formateada1)
            page.locator("input[name='txtFechaAdqui']").fill(fecha_formateada1)

            comprador_infoes_list = compradores_array
            porcentaje=100

            longitud_comprador_infoes = len(comprador_infoes_list)
            print(longitud_comprador_infoes)
            if longitud_comprador_infoes > 1:
                page.select_option("#ddlTipoPropiedad",value="6")
                valorporcentaje = porcentaje / longitud_comprador_infoes
                porcentaje =valorporcentaje
                page.locator("input[name='txtPorcentaje']").fill(str(porcentaje))
            else:
                page.select_option("#ddlTipoPropiedad",value="5")
                #page.locator("input[name='txtPorcentaje']").fill(str(porcentaje))

            time.sleep(3)
            valueM=value_moneda(moneda)
            page.select_option("#ddlTipoMoneda",value=valueM) 

            page.locator("input[name='txtValorTrasferencia']").fill(valorMonetario)

            #apartados de documentos adjuntos

            page.locator("input[name='grdAdjuntos$ctl07$chkSel']").check()
            page.locator("input[name='grdAdjuntos$ctl08$chkSel']").check()
            
            page.locator("input[name='grdAdjuntos$ctl10$chkSel']").check()

            page.locator("input[name='txtOtros']").fill("Recibos")

            input("Corrige el modelo...")
            Registrador.info("Termine la Segunda Hoja")
            # Parte final
            page.locator("input[name='btnValidar']").click()
            
            time.sleep(2)
            
        except Exception as e:
            page.locator("#btnCancelar").click()
            raise
        
        # page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=200)
        time.sleep(2)
        if not encontrar_marca1(page,marcas):
            raise ValueError("Marca no encontrada")
        time.sleep(2)

        encontrar_modelo2(page, modelos, version, seleccion_previa=resultado_seleccion, formulaRodante=formulaRodante, peso_bruto=pesoBruto)


        page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))
        page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)
        page.select_option("#ddlTipoMonedaV",value=valueM)
        input("Corrige el modelo...")
        
        Registrador.info("Termine la parte final de la hoja")
        time.sleep(2)
        
        # 1. EL VIGÍA (page.once): Se coloca ANTES de hacer el clic.
        page.once("dialog", lambda dialog: dialog.accept())
        
        try:
            with page.expect_navigation(wait_until='load', timeout=30000):
                page.locator("input[name='btnAceptarV']").click()
        except Exception as e:
            Registrador.warning(f"Aviso de navegación lenta o trabada: {e}")
            
        time.sleep(2) 

        # 2. Llamada a la función. Si algo falla aquí adentro, saltará directo al except de abajo.
        Guardar_Archivos(page, browser, inmatriculaciones, num_documento)


    # 3. EL ATRAPADOR MAESTRO: Un solo except que envía el correo sí o sí.
    except Exception as e:
        import traceback
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto = f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        
        traza_error = traceback.format_exc()
        error_message = f"""
        <html>
        <body>
            <h3>Hubo un error crítico procesando los datos del cliente.</h3>
            <p><strong>Error detectado:</strong> {e}</p>
            <p><strong>Detalle Técnico (Traceback):</strong></p>
            <pre>{traza_error}</pre>
        </body>
        </html>
        """
        print(traza_error)
        enviar_email_Api(destinos, asunto, error_message)
        
        
        
#-----------------------------------------------PERSONA JURIDICA CON REPRESENTANTE-------------------------------------------------
def  juridica_con_representante(referencia,comprador_info:dict,data,page:Page,browser,inmatriculaciones,compradores_array):
    try:
        tipo_persona = comprador_info.get('tipoPersona', None)
        tipo_documento = comprador_info.get('tipoDocumento', None)
        num_documento = comprador_info.get('numDocumento', None)
        celular = comprador_info.get('celular', None)
        telefonoFijo = comprador_info.get('telefonoFijo', None)
        correoElectronico = comprador_info.get('correoElectronico', None)
        correoElectronicoAlternativoR =comprador_info.get('correoElectronicoAlternativo',None)
        fecha_nacimiento = comprador_info.get('fechaDeNacimiento', "")
        domicilio_fiscal:dict = comprador_info.get('domicilioFiscal', {})
        distrito = domicilio_fiscal.get('distrito')
        direccion = domicilio_fiscal.get('direccion')
        apellido_paterno = comprador_info.get('apellidoPaterno')
        apellido_materno = comprador_info.get('apellidoMaterno')
        nombre=comprador_info.get('nombres')
        razon_social = comprador_info.get('razonSocial', None)
        

        #representante
        representante_info:dict =comprador_info.get('Representante',{})
        tipo_personaR = representante_info.get('tipoPersona', None)
        tipo_documentoR = representante_info.get('tipoDeDocumento', None)
        num_documentoR = representante_info.get('numDocumento', None)
        apellido_paternoR = representante_info.get('apellidoPaterno')
        apellido_maternoR = representante_info.get('apellidoMaterno')
        nombreR=representante_info.get('nombres')
        celularR = representante_info.get('celular', '')
        telefonoR = representante_info.get('telefonoFijo', '')
        correoElectronicoR = representante_info.get('correoElectronico', None)
        fecha_nacimientoR = representante_info.get('fechaDeNacimiento', None)
        
        
        domicilio_fiscal:dict = representante_info.get('domicilioDeRelacionado', {})
        distritoR = domicilio_fiscal.get('distrito')
        direccionR = domicilio_fiscal.get('direccion')




        # Acceder a la información de 'adquisicion'
        adquisicion_info: dict = comprador_info.get('adquisicion', {})
        fechaInscripcion = adquisicion_info.get('fecha_inscripcion')
        tipodeadquisicion = adquisicion_info.get('tipoDeAdquisicion')
        fechasAdquisicion_factura_cancelacion = adquisicion_info.get('fechasAdquisicion_factura_cancelacion')
        condicionDePropiedad = adquisicion_info.get('condicionDePropiedad')
        moneda = adquisicion_info.get('moneda')
        valorMonetario = adquisicion_info.get('valorMonetario')
        datos_transferente:dict = adquisicion_info.get('datosDelTransferente', {})
        distritoUbicacion = datos_transferente.get('distritoUbicacion')


        #DATOS DEL VEHICULO
        vehiculo_data:dict = data.get('vehiculo', {})
        categoriaMtc = vehiculo_data.get('categoriaMtc', '')
        carroceria = vehiculo_data.get('carroceria', '')
        anoModelo = vehiculo_data.get('anoModelo', '')
        modelos = vehiculo_data.get('modelo', '')
        version= vehiculo_data.get('version', '')
        marcas = vehiculo_data.get('marca', '')
        nroMotor = vehiculo_data.get('nroMotor', '')
        nAsientos = vehiculo_data.get('nAsientos', '')
        combustible = vehiculo_data.get('combustible', '')
        cilindraje = vehiculo_data.get('cilindraje', '')
        formulaRodante = vehiculo_data.get('formulaRodante', '')
        pesoBruto = vehiculo_data.get('pesoBruto', '')
        transmision = vehiculo_data.get('transmision', '')

        json_formateado = json.dumps(data, indent=4, ensure_ascii=False)

        if not tipo_persona :
            Registrador.error(f"No se encontro el dni de la persona de la inmatriculacion° {inmatriculaciones}")
            raise ValueError(f"El numero del documento esta vacio o no existe de la inmatriculacion°{inmatriculaciones}")

        if not isinstance(pesoBruto,int):
            raise ValueError(f"El campo peso bruto '{pesoBruto}' debe ser un número (entero). Se recibió: {repr(pesoBruto)}")
        
        if not isinstance(cilindraje,int):
            raise ValueError(f"El campo  cilindraje'{cilindraje}' debe ser un número (entero). Se recibió: {repr(cilindraje)}")

        if len(direccion) < 7:
            Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 7 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
            raise ValueError(f"La dirección de la Empresa '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre} con el DNI {num_documento}")
    
        if len(direccionR)< 7:
            Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 7 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
            raise ValueError(f"La dirección del representate '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombreR} con el DNI {num_documentoR}")
        
        try:
            # ==============================================================================
            # FASE 1: DATOS DE LA EMPRESA (ADMINISTRADO PRINCIPAL)
            # ==============================================================================
            print("\n--- DATOS DE LA EMPRESA (PERSONA JURÍDICA) ---")
            page.select_option("#ddlTipoAdministrado", value=tipo_persona)
            page.keyboard.press('Tab')

            print(f"Buscando documento de la empresa: {num_documento}")
            page.locator("input[name='txtDocuAdmi']").fill(num_documento)
            
            # BÚSQUEDA 1 (Con lectura de alerta segura)
            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            
            page.wait_for_timeout(2000)
            page.keyboard.press('Tab')

            # VALIDACIÓN DE LA RAZÓN SOCIAL
            value_razonsocial = page.locator("#txtRazoSociAdmi").input_value().strip()
            print(f"Razón social SAT: '{value_razonsocial}' | API: '{razon_social}'")

            if value_razonsocial != razon_social:
                Registrador.warning("Discrepancia en razón social. Forzando segunda búsqueda en SUNAT...")
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("input[name='cmdBuscaDocuAdmi']").click() 
                page.wait_for_timeout(3000) 
                
                value_razonsocial_nueva = page.locator("#txtRazoSociAdmi").input_value().strip()
                Registrador.info(f"Nombre oficial confirmado por SUNAT: {value_razonsocial_nueva}")
            else:
                print("✅ La razón social de la empresa coincide.")

            # LLENADO DE DATOS (Solo campos válidos para Empresa, sin apellidos ni nombres)
            page.locator("input[name='txtTelefono1']").fill(telefonoFijo if telefonoFijo else "")
            page.locator("input[name='txtTelefono2']").fill(celular if celular else "")
            page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico if correoElectronico else "")
            
            if page.locator("#ddlDistrito").is_enabled():
                page.select_option("#ddlDistrito", value=distrito)
                page.locator("input[name='txtDireccion']").fill(direccion)
            else:
                Registrador.warning("El combo de distrito de la empresa no está habilitado.")
                
            input("Corrige los datos de la EMPRESA si es necesario y presiona Enter para continuar...")

            # ==============================================================================
            # FASE 2: DATOS DEL REPRESENTANTE LEGAL
            # ==============================================================================
            print("\n--- DATOS DEL REPRESENTANTE ---")
            
            # 1. Guardar LOS DATOS del Representante
            data_rep = {
                "tipo_doc": tipo_documentoR,
                "num_doc": num_documentoR,
                "paterno": apellido_paternoR,
                "materno": apellido_maternoR,
                "nombre": nombreR,
                "celular": celularR if celularR else "",
                "correo": correoElectronicoR if correoElectronicoR else "",
                "fecha": fecha_nacimientoR,
                "distrito": distritoR,
                "direccion": direccionR
            }

            # 2. SELECCIÓN DE DOCUMENTO Y BÚSQUEDA
            page.select_option("#ddlTipoDocuRela", value=data_rep["tipo_doc"])

            if page.locator("#txtDocuRela").is_enabled():
                try: page.locator("#btnNuevaBusquedaRel").click()
                except: pass 
                
                page.locator("#txtDocuRela").fill(data_rep["num_doc"])
                
                page.once("dialog", lambda d: d.accept())
                page.locator("#cmdBuscaDocuRel").click()
                page.wait_for_timeout(2000) 

            # 3. VALIDACIÓN INTELIGENTE (El SAT vs La API)
            sat_pate = page.locator("#txtApePateRela").input_value().strip()
            sat_mate = page.locator("#txtApeMateRela").input_value().strip()
            sat_nomb = page.locator("#txtNombRela").input_value().strip()

            usar_api_rep = False

            if sat_pate != data_rep["paterno"] or sat_mate != data_rep["materno"] or sat_nomb != data_rep["nombre"]:
                # CASO A: SAT vacío
                if not sat_pate and not sat_nomb:
                    Registrador.warning("SAT vacío para representante. Se forzará el uso de la API.")
                    usar_api_rep = True
                # CASO B: Discrepancia. Segunda búsqueda de confirmación.
                else:
                    Registrador.info("Discrepancia en representante. Realizando segunda búsqueda para confirmar...")
                    page.once("dialog", lambda d: d.accept())
                    page.locator("#cmdBuscaDocuRel").click()
                    page.wait_for_timeout(3000)
                    
                    # Volvemos a leer lo que trajo el SAT tras el segundo intento
                    sat_pate2 = page.locator("#txtApePateRela").input_value().strip()
                    sat_mate2 = page.locator("#txtApeMateRela").input_value().strip()
                    sat_nomb2 = page.locator("#txtNombRela").input_value().strip()
                    
                    # DECISIÓN FINAL: Si sigue distinto, chancamos la data.
                    if sat_pate2 != data_rep["paterno"] or sat_mate2 != data_rep["materno"] or sat_nomb2 != data_rep["nombre"]:
                        Registrador.warning("El SAT insiste con otro representante. ¡Sobreescribiendo con la API a la fuerza!")
                        usar_api_rep = True
                    else:
                        Registrador.info("La segunda búsqueda corrigió los nombres. Todo en orden.")
            else:
                print("✅ Los nombres del representante coinciden perfectamente.")

            # 4. LLENADO DE NOMBRES Y APELLIDOS DEL REPRESENTANTE
            if usar_api_rep:
                page.locator("input[name='txtApePateRela']").fill(data_rep["paterno"])
                
                if not data_rep["materno"]:
                    page.locator("input[name='chkSinApeMatRela']").check()
                    page.locator("input[name='txtApeMateRela']").fill("")
                else:
                    page.locator("input[name='txtApeMateRela']").fill(data_rep["materno"])
                
                nombre_final_rep = data_rep["nombre"]
                page.locator("input[name='txtNombRela']").fill(data_rep["nombre"])
            else:
                if not page.locator("#txtApeMateRela").input_value().strip():
                    page.locator("input[name='chkSinApeMatRela']").check()
                nombre_final_rep = page.locator("#txtNombRela").input_value().strip()

            if len(nombre_final_rep) > 30:
                Registrador.warning(f"El nombre del representante excede 30 caracteres (Longitud: {len(nombre_final_rep)}).")

            # 5. LLENADO DEL RESTO DE DATOS (Manda la API)
            page.locator("input[name='txtTelefono1Rela']").fill("") 
            page.locator("input[name='txtTelefono2Rela']").fill(data_rep["celular"])
            page.locator("input[name='txtCorreoElectronicoRela']").fill(data_rep["correo"])

            if page.is_enabled("#ddlDistritoRela"):
                page.select_option("#ddlDistritoRela", value=data_rep["distrito"])
                page.locator("input[name='txtDireccionRela']").fill(data_rep["direccion"])
            else:
                Registrador.warning("El combo de distrito del representante no está habilitado.")

            if data_rep["fecha"]:
                try:
                    f_nac_rep = datetime.strptime(data_rep["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    # Verifica si el SAT usa este selector exacto para la fecha del representante
                    if page.locator("input[name='txtFecNacPersona']").is_visible():
                        page.locator("input[name='txtFecNacPersona']").fill(f_nac_rep)
                except Exception as e:
                    Registrador.error(f"Error al procesar la fecha de nacimiento del rep: {e}")

            # 6. FINALIZACIÓN
            input("Corrige algún dato del representante si es necesario y presiona Enter para continuar...")
            Registrador.info("Terminé la hoja completa de la Persona Jurídica.")
            
            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnSiguiente']").click()
                
            page.wait_for_load_state()

        except Exception as e:
            Registrador.error(f"Error crítico procesando a la Persona Jurídica: {e}")
            try: 
                page.locator("#lnkRegresar").click()
            except: 
                pass
            raise
        
            
            #DATOS DEL VEHICULO------------------
            #fechaInscripcion1 = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
        try:
            # Formatear el objeto datetime a la cadena deseada (día-mes-año)
            #input("Presiona Enter para continuar...")
                
            fecha_formateada = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
            fecha_formateada = fecha_formateada.strftime("%d-%m-%Y")
            fecha_formateada = fecha_formateada.replace("-", "/")
            print(fecha_formateada)
            page.locator("input[name='txtInscripcion']").fill(fecha_formateada)
            #input("Ingresar fecha de inscripcion...")
            page.locator("input[name='txtAnoModelo']").fill(anoModelo)
            page.keyboard.press("Enter")                

            value_categoriaMtc=categoria(categoriaMtc)
            page.select_option("#ddlCatMTC",value=str(value_categoriaMtc))

            valuecarroceria=encontrar_carroceria(page,carroceria)
            page.select_option("#ddlCarroceria",value=valuecarroceria)

            #page.locator("input[name='txtAnoFabrica']").fill(anoFabricacion)

            time.sleep(2)
            # page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=100)
            time.sleep(2)
            if not encontrar_marca(page,marcas):
                raise ValueError("Marca no encontrada")

            
            time.sleep(2)
            # 2. Validacion de nroMotor
            if " " in str(nroMotor):
                print("*" * 40)
                print("*" * 40)
                print("CAMBIO REALIZADO")
                print("*" * 40)
                print("*" * 40)

            # 3. Limpiamos el dato y lo escribimos en la web
            nroMotor_limpio = str(nroMotor).replace(" ", "")
            page.locator("input[name='txtMotor']").fill(nroMotor_limpio)
            page.locator("input[name='txtNroAsientos']").fill(nAsientos)

            value_combustible=encontrar_combustible(combustible)
            page.select_option("#ddlTipoMotor",value=str(value_combustible))
            
            formulaRodante1=encontrar_formulaRodante(formulaRodante)
            page.select_option("#ddlTraccion",value=str(formulaRodante1))
            
            

            #rpt_cilindraje=int(cilindraje)*1000
            # Después de las validaciones, llenar el campo en la página
            # Después de llenar otros campos del vehículo como:
            page.locator("input[name='txtAnoModelo']").fill(anoModelo)
            page.select_option("#ddlCatMTC", value=str(value_categoriaMtc))

            # CILINDRAJE Validacion en 0
            try:
                cilindraje_int = int(cilindraje)
            except ValueError:
                cilindraje_int = 0  # Manejo de error si no es número

            # 2. APLICAMOS LA CORRECCIÓN DE CEROS EXTRAS
            # Si es mayor a 20,000 (ningún auto normal pasa de 10k-12k cc), asumimos error de formato
            if cilindraje_int > 50000: 
                cilindraje_int = cilindraje_int // 1000  # División entera: 1995000 -> 1995

            # 3. Tu lógica de llenado (usando la variable corregida)
            if cilindraje_int == 0:
                page.locator("#txtCilindraje").fill("1")
            elif cilindraje_int > 0:
                page.locator("#txtCilindraje").fill(str(cilindraje_int))
                
            #rpt_pesobruto=int(pesoBruto) * 1000
            page.locator("input[name='txtPesoBruto']").fill(str(int(pesoBruto)))
            page.keyboard.press("Enter")


            value_T=encontrar_transmision(transmision)
            page.select_option("#ddlTransmision",value=str(value_T))

            page.locator("#btnDetermClaseCat").click
            page.wait_for_timeout(2000)
        
            # Opcional: Solo para tu control en consola (no afecta la lógica)
            clase_vehiculo = page.locator("#ddlClase").input_value()
            print(f"ℹ️ Clase detectada antes de buscar modelo: {clase_vehiculo}")
            
            # Seleccionar modelo ULTIMO PASO
            v_modelos=f"{modelos}".strip()
            time.sleep(2)
            page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=30)
            v_modeloCompleto = combinar_modelo_version(modelos, version)
            
            time.sleep(2)
            resultado_seleccion = encontrar_modelo(page, modelos, version, formulaRodante=formulaRodante, peso_bruto=pesoBruto)
            
            #DATOS DE LA ADQUISICION------------------
            page.select_option("#ddlTipoTransferencia",value={tipodeadquisicion})


            fechaAdquisicion = datetime.strptime(fechasAdquisicion_factura_cancelacion, "%Y-%m-%d")
            fecha_formateada1 = fechaAdquisicion.strftime("%d-%m-%Y")
            fecha_formateada1 = fecha_formateada1.replace("-", "/")
            print(fecha_formateada1)
            page.locator("input[name='txtFechaAdqui']").fill(fecha_formateada1)

            # input("Corrige la fecha y monto")
            page.select_option("#ddlTipoPropiedad",value="5")

            valueM=value_moneda(moneda)
            page.select_option("#ddlTipoMoneda",value=valueM) 

            page.locator("input[name='txtValorTrasferencia']").fill(valorMonetario)
            # input("Corrige la fecha y monto")
            

            #apartados de documentos adjuntos

            page.locator("input[name='grdAdjuntos$ctl07$chkSel']").check()
            page.locator("input[name='grdAdjuntos$ctl08$chkSel']").check()
            
            page.locator("input[name='grdAdjuntos$ctl10$chkSel']").check()

            page.locator("input[name='txtOtros']").fill("Recibos")

            input("Corrige el modelo...")
            Registrador.info("Termine la Segunda Hoja")
            # Parte final
            page.locator("input[name='btnValidar']").click()
            
            time.sleep(3)
        
        #page.select_option("#ddlClaseV", value="11")
        except Exception as e:
            page.locator("#btnCancelar").click()
            raise

        # 1. LLENADO DE DATOS
        # ---------------------------------------------------------
        # page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas, delay=200)
        time.sleep(2)

        if not encontrar_marca1(page, marcas):
            raise ValueError("Marca no encontrada")

        encontrar_modelo2(page, modelos, version, seleccion_previa=resultado_seleccion, formulaRodante=formulaRodante, peso_bruto=pesoBruto)

            
        page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))
        page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)
        page.select_option("#ddlTipoMonedaV", value=valueM)
        input("Corrige el modelo...")
        
        Registrador.info("Termine la parte final de la hoja")
        time.sleep(2)
        
        # 1. EL VIGÍA (page.once): Se coloca ANTES de hacer el clic.
        page.once("dialog", lambda dialog: dialog.accept())
        
        try:
            with page.expect_navigation(wait_until='load', timeout=30000):
                page.locator("input[name='btnAceptarV']").click()
        except Exception as e:
            Registrador.warning(f"Aviso de navegación lenta o trabada: {e}")
            
        time.sleep(2) 

        # 2. Llamada a la función. Si algo falla aquí adentro, saltará directo al except de abajo.
        Guardar_Archivos(page, browser, inmatriculaciones, num_documento)


    # 3. EL ATRAPADOR MAESTRO: Un solo except que envía el correo sí o sí.
    except Exception as e:
        import traceback
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto = f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        
        traza_error = traceback.format_exc()
        error_message = f"""
        <html>
        <body>
            <h3>Hubo un error crítico procesando los datos del cliente.</h3>
            <p><strong>Error detectado:</strong> {e}</p>
            <p><strong>Detalle Técnico (Traceback):</strong></p>
            <pre>{traza_error}</pre>
        </body>
        </html>
        """
        print(traza_error)
        enviar_email_Api(destinos, asunto, error_message)
        

        
#-----------------------------------------------PERSONA SOCIEDAD CONYUGAL-------------------------------------------------

def sociedadconyugal(referencia,comprador_info,data,page:Page,browser,inmatriculaciones,compradores_array: list[dict]):

    try:
            
        if len(compradores_array) >=1:
            comprador1_info = compradores_array[0]
            comprador2_info = compradores_array[1]

            print("Primera persona")
            print(comprador1_info)

            print("segunda persona")
            print(comprador2_info)

            tipo_persona = comprador1_info.get('tipoPersona', None)
            tipo_documento = comprador1_info.get('tipoDocumento', None)
            num_documento = comprador1_info.get('numDocumento', None)
            celular = comprador1_info.get('celular', None)
            correoElectronico = comprador1_info.get('correoElectronico', None)
            fecha_nacimiento = comprador1_info.get('fechaDeNacimiento',"")

            domicilio_fiscal:dict = comprador1_info.get('domicilioFiscal', {})
            distrito = domicilio_fiscal.get('distrito')
            direccion = domicilio_fiscal.get('direccion')
            apellido_paterno = comprador1_info.get('apellidoPaterno','')
            apellido_materno = comprador1_info.get('apellidoMaterno','')
            nombre=comprador1_info.get('nombres')
            razon_social = comprador1_info.get('razonSocial', None)

            print(tipo_documento)
            print(num_documento)
            print(apellido_paterno)
            print(apellido_materno)

            print("separar datos")
                    # Acceder a la información de 'adquisicion'
            adquisicion_info:dict = comprador1_info.get('adquisicion', {})
            fechaInscripcion = adquisicion_info.get('fecha_inscripcion')
            tipodeadquisicion = adquisicion_info.get('tipoDeAdquisicion')
            fechasAdquisicion_factura_cancelacion = adquisicion_info.get('fechasAdquisicion_factura_cancelacion')
            datos_transferente:dict = adquisicion_info.get('datosDelTransferente', {})
            distritoUbicacion = datos_transferente.get('distritoUbicacion',None)
            
            condicionDePropiedad = adquisicion_info.get('condicionDePropiedad')
            
            moneda = adquisicion_info.get('moneda')
            valorMonetario = adquisicion_info.get('valorMonetario')
            #PERSONA CON LA QUE ESTA CASADA
            tipo_persona2 = comprador2_info.get('tipoPersona', None)
            tipo_documento2 = comprador2_info.get('tipoDocumento', None)
            razon_social2 = comprador2_info.get('razonSocial', None)
            print(tipo_documento2)
            num_documento2 = comprador2_info.get('numDocumento', None)
            print(num_documento2)
            apellido_paterno2 = comprador2_info.get('apellidoPaterno','')
            print(apellido_paterno2)
            apellido_materno2 = comprador2_info.get('apellidoMaterno', '')
            print(apellido_materno2)
            nombre2=comprador2_info.get('nombres')
            print(nombre2)
            correoElectronico2 = comprador2_info.get('correoElectronico', None)
            print(correoElectronico2)
            fecha_nacimiento2 = comprador2_info.get('fechaDeNacimiento',"")
            print(fecha_nacimiento2)
            celular2 = comprador2_info.get('celular', None)


            domicilio_fiscal2: dict = comprador2_info.get('domicilioFiscal', {})
            distrito2 = domicilio_fiscal2.get('distrito')
            direccion2 = domicilio_fiscal2.get('direccion')
            

            #DATOS DEL VEHICULO
            vehiculo_data:dict = data.get('vehiculo', {})
            categoriaMtc = vehiculo_data.get('categoriaMtc', '')
            carroceria = vehiculo_data.get('carroceria', '')
            anoModelo = vehiculo_data.get('anoModelo', '')
            modelos = vehiculo_data.get('modelo', '')
            version= vehiculo_data.get('version', '')
            marcas = vehiculo_data.get('marca', '')
            nroMotor = vehiculo_data.get('nroMotor', '')
            nAsientos = vehiculo_data.get('nAsientos', '')
            combustible = vehiculo_data.get('combustible', '')
            cilindraje = vehiculo_data.get('cilindraje', '')
            formulaRodante = vehiculo_data.get('formulaRodante', '')
            pesoBruto = vehiculo_data.get('pesoBruto', '')
            transmision = vehiculo_data.get('transmision', '')

            if not tipo_persona :
                Registrador.error(f"No se encontro el dni de la persona de la inmatriculacion° {inmatriculaciones}")
                raise ValueError(f"El numero del documento esta vacio o no existe de la inmatriculacion°{inmatriculaciones}")


            if not isinstance(pesoBruto,int):
                raise ValueError(f"El campo peso bruto '{pesoBruto}' debe ser un número (entero). Se recibió: {repr(pesoBruto)}")
        
            if not isinstance(cilindraje,int):
                raise ValueError(f"El campo  cilindraje'{cilindraje}' debe ser un número (entero). Se recibió: {repr(cilindraje)}")

            # Validar longitud mínima de direcciones
            if len(direccion) < 7 :
                Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 7 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
                raise ValueError(f"La dirección del Conyuje '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre} con el DNI {num_documento}") 

            if len(direccion2) < 7:
                Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 7 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
                raise ValueError(f"La dirección del Conyuje '{direccion2}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre2} con el DNI {num_documento2}")


            try:
                # ==============================================================================
                # FASE 1: DATOS DEL COMPRADOR (ADMINISTRADO - PARTE SUPERIOR)
                # ==============================================================================
                print("\n--- FASE 1: DATOS DEL COMPRADOR 1 ---")
                page.select_option("#ddlTipoAdministrado", value=tipo_persona)
                page.select_option("#ddlTipoDocuAdmi", value=tipo_documento)
                page.keyboard.press('Tab')

                page.locator("input[name='txtDocuAdmi']").fill(num_documento)
                
                # -------------------------------------------------------------------
                # EL "CEREBRO" QUE DETECTA QUÉ HIZO EL SAT
                # -------------------------------------------------------------------
                estado_sat = "NORMAL"

                def leer_alerta_sat(dialog):
                    nonlocal estado_sat
                    texto_alerta = dialog.message.lower()
                    print(f" ALERTA DEL SAT: {dialog.message}")
                    
                    if "como cónyuge" in texto_alerta or "se colocará el número de documento ingresado" in texto_alerta:
                        estado_sat = "INVERTIDO"
                        Registrador.warning("El SAT decidió INVERTIR los roles.")
                    elif "sociedad conyugal" in texto_alerta:
                        estado_sat = "PRECARGADO"
                        Registrador.warning("El SAT precargó la sociedad conyugal (Roles Normales).")
                        
                    try: dialog.accept()
                    except: pass

                # Escuchamos el popup justo antes de hacer clic en buscar
                page.once("dialog", leer_alerta_sat)
                page.locator("input[name='cmdBuscaDocuAdmi']").click()
                page.wait_for_timeout(2000)
                page.keyboard.press('Tab')

                # ==============================================================================
                # 1. EMPAQUETAMOS LOS DATOS DE LA API (Las "Mochilas")
                # ==============================================================================
                data_comprador = {
                    "paterno": apellido_paterno,
                    "materno": apellido_materno,
                    "nombre": nombre,
                    "celular": celular if celular else "",
                    "correo": correoElectronico if correoElectronico else "",
                    "fecha": fecha_nacimiento,
                    "distrito": distrito,
                    "direccion": direccion,
                    "tipo_doc": tipo_documento,
                    "num_doc": num_documento
                }

                data_conyuge = {
                    "paterno": apellido_paterno2,
                    "materno": apellido_materno2,
                    "nombre": nombre2,
                    "celular": celular2 if celular2 else "",
                    "correo": correoElectronico2 if correoElectronico2 else "",
                    "fecha": fecha_nacimiento2,
                    "distrito": distrito2,
                    "direccion": direccion2,
                    "tipo_doc": tipo_documento2,
                    "num_doc": num_documento2
                }

                # ==============================================================================
                # 2. ASIGNACIÓN DINÁMICA DE ROLES SEGÚN LO QUE HIZO EL SAT
                # ==============================================================================
                if estado_sat == "INVERTIDO":
                    admin = data_conyuge   # Arriba va la cónyuge
                    rela = data_comprador  # Abajo va el comprador
                else:
                    admin = data_comprador # Arriba va el comprador
                    rela = data_conyuge    # Abajo va la cónyuge

                # ==============================================================================
                # CONTINÚA FASE 1 (LLENANDO LA PARTE DE ARRIBA USANDO EL DICCIONARIO 'admin')
                # ==============================================================================
                sat_pate_admi = page.locator("#txtApePateAdmi").input_value().strip()
                sat_mate_admi = page.locator("#txtApeMateAdmi").input_value().strip()
                sat_nomb_admi = page.locator("#txtNombAdmi").input_value().strip()

                usar_api_admi = False

                # ¡VALIDAMOS SIEMPRE! Sin importar si el SAT lo precargó o no
                if sat_pate_admi != admin["paterno"] or sat_mate_admi != admin["materno"] or sat_nomb_admi != admin["nombre"]:
                    
                    if estado_sat == "NORMAL": 
                        page.once("dialog", lambda d: d.accept()) 
                        page.locator("input[name='cmdBuscaDocuAdmi']").click()
                        page.wait_for_timeout(3000)
                        
                        sat_pate_admi = page.locator("#txtApePateAdmi").input_value().strip()
                        sat_mate_admi = page.locator("#txtApeMateAdmi").input_value().strip()
                        sat_nomb_admi = page.locator("#txtNombAdmi").input_value().strip()
                        
                    # Si no hace match perfecto, forzamos la API
                    if sat_pate_admi != admin["paterno"] or sat_mate_admi != admin["materno"] or sat_nomb_admi != admin["nombre"]:
                        Registrador.warning("¡Forzando nombres de la API en Fase 1!")
                        usar_api_admi = True
                
            
                # Llenado de nombres arriba
                if usar_api_admi:
                    page.locator("input[name='txtApePateAdmi']").fill(admin["paterno"])
                    if not admin["materno"]:
                        page.locator("input[name='chkSinApeMatAdmi']").check()
                    else:
                        page.locator("input[name='txtApeMateAdmi']").fill(admin["materno"])
                    page.locator("input[name='txtNombAdmi']").fill(admin["nombre"])
                else:
                    if not page.locator("#txtApeMateAdmi").input_value().strip():
                        page.locator("input[name='chkSinApeMatAdmi']").check()
                        
                # Resto de Datos Arriba
                page.locator("input[name='txtTelefono1']").fill("")
                page.locator("input[name='txtTelefono2']").fill(admin["celular"])
                page.locator("input[name='txtCorreoElectronico']").fill(admin["correo"])

                if page.is_enabled("#ddlDistrito"):
                    page.select_option("#ddlDistrito", value=admin["distrito"])
                    page.locator("input[name='txtDireccion']").fill(admin["direccion"])

                if admin["fecha"]:
                    try:
                        f_nac_arriba = datetime.strptime(admin["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
                        page.locator("input[name='txtFecNacPersona']").fill(f_nac_arriba)
                    except ValueError as e:
                        Registrador.error(f"Error al procesar la fecha de nacimiento ({fecha_nacimiento}): {e}")
                else:
                    Registrador.warning("No llegó fecha de nacimiento en la API. Campo omitido.")

                # ==============================================================================
                # FASE 2: DATOS DEL CONYUGUE
                # ==============================================================================
                print("\n--- FASE 2: DATOS DEL CONYUGUE ---")

                # 1. Si el flujo es NORMAL, necesitamos hacer la primera búsqueda manual
                if estado_sat == "NORMAL":
                    page.locator("#btnNuevaBusquedaRel").click()
                    page.select_option("#ddlTipoDocuRela", value=rela["tipo_doc"])
                    page.locator("input[name='txtDocuRela']").fill(rela["num_doc"])
                    
                    page.once("dialog", lambda d: d.accept())
                    page.locator("input[name='cmdBuscaDocuRel']").click()
                    page.wait_for_timeout(2000)

                # 2. Leemos lo que el SAT tiene en pantalla (ya sea por búsqueda manual o precargado)
                sat_pate_r1 = page.locator("#txtApePateRela").input_value().strip()
                sat_mate_r1 = page.locator("#txtApeMateRela").input_value().strip()
                sat_nomb_r1 = page.locator("#txtNombRela").input_value().strip()

                usar_api_r1 = False
                
                # 3. COMPARACIÓN ESTRICTA CON LA API (Como en el Natural)
                if sat_pate_r1 != rela["paterno"] or sat_mate_r1 != rela["materno"] or sat_nomb_r1 != rela["nombre"]:
                    
                    # Si es NORMAL, le damos una segunda oportunidad al botón buscar
                    if estado_sat == "NORMAL":
                        page.once("dialog", lambda d: d.accept())
                        page.locator("input[name='cmdBuscaDocuRel']").click()
                        page.wait_for_timeout(3000)
                        
                        # Volvemos a leer
                        sat_pate_r1 = page.locator("#txtApePateRela").input_value().strip()
                        sat_mate_r1 = page.locator("#txtApeMateRela").input_value().strip()
                        sat_nomb_r1 = page.locator("#txtNombRela").input_value().strip()
                        
                    # Si a pesar de todo (búsqueda doble o precargado erróneo) sigue diferente, obligamos a la API
                    if sat_pate_r1 != rela["paterno"] or sat_mate_r1 != rela["materno"] or sat_nomb_r1 != rela["nombre"]:
                        Registrador.warning(f"Discrepancia detectada en Cónyuge | API: {rela['nombre']} {rela['paterno']} vs SAT: {sat_nomb_r1} {sat_pate_r1}. ¡Forzando API!")
                        usar_api_r1 = True

                # 4. LLENADO O FORZADO DE NOMBRES
                if usar_api_r1:
                    page.locator("input[name='txtApePateRela']").fill(rela["paterno"])
                    if not rela["materno"]:
                        page.locator("input[name='chkSinApeMatRela']").check()
                    else:
                        page.locator("input[name='txtApeMateRela']").fill(rela["materno"])
                    page.locator("input[name='txtNombRela']").fill(rela["nombre"])
                else:
                    if not page.locator("#txtApeMateRela").input_value().strip():
                        page.locator("input[name='chkSinApeMatRela']").check()

                # ==============================================================================
                # FORZAMOS CONTACTO, DIRECCIÓN Y FECHA (Siempre se ejecuta)
                # ==============================================================================
                page.locator("input[name='txtTelefono2Rela']").fill(rela["celular"])
                page.locator("input[name='txtCorreoElectronicoRela']").fill(rela["correo"])

                if page.is_enabled("#ddlDistritoRela"):
                    page.select_option("#ddlDistritoRela", value=rela["distrito"])
                    page.locator("input[name='txtDireccionRela']").fill(rela["direccion"])

                if rela["fecha"]:
                    try:
                        f_nac_abajo = datetime.strptime(rela["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
                        selector_fecha_abajo = "input[name='txtFecNacRelacionado']" 
                        
                        if page.locator(selector_fecha_abajo).is_visible():
                            page.locator(selector_fecha_abajo).fill(f_nac_abajo)
                            
                    except ValueError as e:
                        Registrador.error(f"Error al procesar la fecha de nacimiento ({fecha_nacimiento2}): {e}")
                else:
                    Registrador.warning("No llegó fecha de nacimiento de cónyuge en la API. Campo omitido.")

                # ==============================================================================
                # FINALIZACIÓN
                # ==============================================================================
                input("Revisa los datos del Comprador y Cónyuge y presiona Enter para continuar...")
                Registrador.info("Terminé la hoja de la Sociedad Conyugal")

                with page.expect_navigation(wait_until='load'):
                    page.locator("input[name='btnSiguiente']").click()
                    
            except Exception as e:
                Registrador.error(f"Error crítico en Sociedad Conyugal: {e}")
                try:
                    page.locator("#lnkRegresar").click()
                except:
                    pass
                raise

            
            
            
            
                #DATOS DEL VEHICULO-------------------------                    
            try:
                time.sleep(2)
                
                # Formatear el objeto datetime a la cadena deseada (día-mes-año)
                fecha_formateada = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
                fecha_formateada = fecha_formateada.strftime("%d-%m-%Y")
                fecha_formateada = fecha_formateada.replace("-", "/")
                print(fecha_formateada)
                page.locator("input[name='txtInscripcion']").fill(fecha_formateada)


                page.locator("input[name='txtAnoModelo']").fill(anoModelo)
                page.keyboard.press("Enter")                

                value_categoriaMtc=categoria(categoriaMtc)
                page.select_option("#ddlCatMTC",value=str(value_categoriaMtc))

                # carroceria=funcarroceria()
                valuecarroceria=encontrar_carroceria(page,carroceria)
                page.select_option("#ddlCarroceria",value=valuecarroceria)

                #page.locator("input[name='txtAnoFabrica']").fill(anoFabricacion)
                time.sleep(2)
                # page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=100)
                time.sleep(2)
                if not encontrar_marca(page,marcas):
                    raise ValueError("Marca no encontrada")

                time.sleep(2)
                
                # VALIDACION NRO MOTOR
                if " " in str(nroMotor):
                    print("*" * 40)
                    print("*" * 40)
                    print("CAMBIO REALIZADO")
                    print("*" * 40)
                    print("*" * 40)

                # 3. Limpiamos el dato y lo escribimos en la web
                nroMotor_limpio = str(nroMotor).replace(" ", "")
                page.locator("input[name='txtMotor']").fill(nroMotor_limpio)
                page.locator("input[name='txtNroAsientos']").fill(nAsientos)

                value_combustible=encontrar_combustible(combustible)
                page.select_option("#ddlTipoMotor",value=str(value_combustible))
                
                formulaRodante1=encontrar_formulaRodante(formulaRodante)
                page.select_option("#ddlTraccion",value=str(formulaRodante1))

                #rpt_cilindraje=int(cilindraje)*1000
                # Después de las validaciones, llenar el campo en la página
                try:
                    cilindraje_int = int(cilindraje)
                except ValueError:
                    cilindraje_int = 0  # Manejo de error si no es número

                # 2. APLICAMOS LA CORRECCIÓN DE CEROS EXTRAS
                # Si es mayor a 20,000 (ningún auto normal pasa de 10k-12k cc), asumimos error de formato
                if cilindraje_int > 50000: 
                    cilindraje_int = cilindraje_int // 1000  # División entera: 1995000 -> 1995

                # 3. Tu lógica de llenado (usando la variable corregida)
                if cilindraje_int == 0:
                    page.locator("#txtCilindraje").fill("1")
                elif cilindraje_int > 0:
                    page.locator("#txtCilindraje").fill(str(cilindraje_int))


                #rpt_pesobruto=int(pesoBruto) * 1000
                page.locator("input[name='txtPesoBruto']").fill(str(int(pesoBruto)))
                page.keyboard.press("Enter")


                value_T=encontrar_transmision(transmision)
                page.select_option("#ddlTransmision",value=str(value_T))

                page.locator("#btnDetermClaseCat").click
                page.wait_for_timeout(2000)
            
                # Opcional: Solo para tu control en consola (no afecta la lógica)
                clase_vehiculo = page.locator("#ddlClase").input_value()
                print(f"ℹ️ Clase detectada antes de buscar modelo: {clase_vehiculo}")
                
                # Seleccionar modelo ULTIMO PASO
                v_modelos=f"{modelos}".strip()
                time.sleep(2)
                page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=30)
                v_modeloCompleto = combinar_modelo_version(modelos, version)
                
                time.sleep(2)
                resultado_seleccion = encontrar_modelo(page, modelos, version, formulaRodante=formulaRodante, peso_bruto=pesoBruto)


                #DATOS DE LA ADQUISICION------------------  
                page.select_option("#ddlTipoTransferencia",value={tipodeadquisicion})


                fechaAdquisicion = datetime.strptime(fechasAdquisicion_factura_cancelacion, "%Y-%m-%d")
                fecha_formateada1 = fechaAdquisicion.strftime("%d-%m-%Y")
                fecha_formateada1 = fecha_formateada1.replace("-", "/")
                print(fecha_formateada1)
                page.locator("input[name='txtFechaAdqui']").fill(fecha_formateada1)

                #input("Ingresar fecha de adquisicion...")

                page.select_option("#ddlTipoPropiedad",value="5")

                time.sleep(3)
                valueM=value_moneda(moneda)
                page.select_option("#ddlTipoMoneda",value=valueM) 

                page.locator("input[name='txtValorTrasferencia']").fill(valorMonetario)

                

                #apartados de documentos adjuntos

                page.locator("input[name='grdAdjuntos$ctl07$chkSel']").check()
                page.locator("input[name='grdAdjuntos$ctl08$chkSel']").check()
                
                page.locator("input[name='grdAdjuntos$ctl10$chkSel']").check()

                page.locator("input[name='txtOtros']").fill("Recibos")

                input("Corrige el modelo...")
                Registrador.info("Termine la segunda hoja")
                # Parte final
            
                page.locator("input[name='btnValidar']").click()
                
                time.sleep(5)
            
            
            except Exception as e:
                page.locator("#btnCancelar").click()
                raise

            
            # page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=200)
            time.sleep(2)
            if not encontrar_marca1(page,marcas):
                raise ValueError("Marca no encontrada")

            encontrar_modelo2(page, modelos, version, seleccion_previa=resultado_seleccion, formulaRodante=formulaRodante, peso_bruto=pesoBruto)

            page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))
            page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)
            page.select_option("#ddlTipoMonedaV",value=valueM)
            input("Corrige el modelo...")
            
            Registrador.info("Termine la parte final de la hoja")
            time.sleep(2)
        
        page.once("dialog", lambda dialog: dialog.accept())
        
        try:
            with page.expect_navigation(wait_until='load', timeout=30000):
                page.locator("input[name='btnAceptarV']").click()
        except Exception as e:
            Registrador.warning(f"Aviso de navegación lenta o trabada: {e}")
            
        time.sleep(2) 

        Guardar_Archivos(page, browser, inmatriculaciones, num_documento)

    except Exception as e:
        import traceback
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto = f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        
        traza_error = traceback.format_exc()
        error_message = f"""
        <html>
        <body>
            <h3>Hubo un error crítico procesando los datos del cliente.</h3>
            <p><strong>Error detectado:</strong> {e}</p>
            <p><strong>Detalle Técnico (Traceback):</strong></p>
            <pre>{traza_error}</pre>
        </body>
        </html>
        """
        print(traza_error)
        enviar_email_Api(destinos, asunto, error_message)

    return inmatriculaciones


#-----------------------------------------------PERSONA NATURAL CO-COMPRADOR-------------------------------------------------
    
def natural_coocomprador(referencia,_co_comprador_info:dict,inicio_comprador,data,page:Page,browser,inmatriculaciones,compradores_array):
    
    tipo_persona = _co_comprador_info.get('tipoPersona', None)
    tipo_documento = _co_comprador_info.get('tipoDocumento', None)
    num_documento = _co_comprador_info.get('numDocumento', None)
    celular = _co_comprador_info.get('celular', None)
    correoElectronico = _co_comprador_info.get('correoElectronico', None)
    fecha_nacimiento = _co_comprador_info.get('fechaDeNacimiento', "")

    apellido_paterno = _co_comprador_info.get('apellidoPaterno')
    apellido_materno = _co_comprador_info.get('apellidoMaterno')
    nombre=_co_comprador_info.get('nombres')
    razon_social = _co_comprador_info.get('razonSocial', None)
    tieneRepresentante = _co_comprador_info.get('TieneRepresentante', None)
    domicilio_fiscal:dict = _co_comprador_info.get('domicilioFiscal', {})
    distrito = domicilio_fiscal.get('distrito')
    direccion = domicilio_fiscal.get('direccion')

    # Acceder a la información de 'adquisicion'
    adquisicion_info: dict = _co_comprador_info.get('adquisicion', {})
    fechaInscripcion = adquisicion_info.get('fecha_inscripcion')
    tipodeadquisicion = adquisicion_info.get('tipoDeAdquisicion')
    fechasAdquisicion_factura_cancelacion = adquisicion_info.get('fechasAdquisicion_factura_cancelacion')
    condicionDePropiedad = adquisicion_info.get('condicionDePropiedad')
    moneda = adquisicion_info.get('moneda')
    valorMonetario = adquisicion_info.get('valorMonetario')
    datos_transferente:dict = adquisicion_info.get('datosDelTransferente', {})
    distritoUbicacion = datos_transferente.get('distritoUbicacion')


    vehiculo_data:dict = data.get('vehiculo', {})
    categoriaMtc = vehiculo_data.get('categoriaMtc', '')
    carroceria = vehiculo_data.get('carroceria', '')
    anoModelo = vehiculo_data.get('anoModelo', '')
    modelos = vehiculo_data.get('modelo', '')
    version= vehiculo_data.get('version', '')
    marcas = vehiculo_data.get('marca', '')
    nroMotor = vehiculo_data.get('nroMotor', '')
    nAsientos = vehiculo_data.get('nAsientos', '')
    combustible = vehiculo_data.get('combustible', '')
    cilindraje = vehiculo_data.get('cilindraje', '')
    formulaRodante = vehiculo_data.get('formulaRodante', '')
    pesoBruto = vehiculo_data.get('pesoBruto', '')
    transmision = vehiculo_data.get('transmision', '')

    if not tipo_persona :
        Registrador.error(f"No se encontro el dni de la persona de la inmatriculacion° {inmatriculaciones}")
        raise ValueError(f"El numero del documento esta vacio o no existe de la inmatriculacion°{inmatriculaciones}")

    if not isinstance(pesoBruto,int):
        raise ValueError(f"El campo peso bruto '{pesoBruto}' debe ser un número (entero). Se recibió: {repr(pesoBruto)}")
        
    if not isinstance(cilindraje,int):
        raise ValueError(f"El campo  cilindraje'{cilindraje}' debe ser un número (entero). Se recibió: {repr(cilindraje)}")

    if len(direccion) < 7 :
        Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 7 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
        raise ValueError(f"La dirección de la Empresa '{direccion}' es muy corta debe tener al menos 7 caracteres. El cliente es {nombre} con el DNI {num_documento}")
    
    try:
        if inicio_comprador:
            print("\n--- DATOS DEL CO-COMPRADOR ---")
            page.select_option("#ddlTipoAdministrado", value=tipo_persona)
            page.select_option("#ddlTipoDocuAdmi", value=tipo_documento)
            page.keyboard.press('Tab')

            print(f"Buscando documento del co-comprador: {num_documento}")
            page.locator("input[name='txtDocuAdmi']").fill(num_documento)
            
            # ==========================================================
            # 1. PRIMERA BÚSQUEDA
            # ==========================================================
            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass
            
            page.wait_for_timeout(2000)
            page.keyboard.press('Tab')

            # Capturamos datos del SAT
            sat_paterno = page.locator("#txtApePateAdmi").input_value().strip()
            sat_materno = page.locator("#txtApeMateAdmi").input_value().strip()
            sat_nombre = page.locator("#txtNombAdmi").input_value().strip()

            # ==========================================================
            # 2. VALIDACIÓN Y SEGUNDA BÚSQUEDA
            # ==========================================================
            usar_nombres_api = False

            if sat_paterno != apellido_paterno or sat_materno != apellido_materno or sat_nombre != nombre:
                # CASO A: SAT vacío
                if not sat_paterno and not sat_nombre:
                    Registrador.warning("SAT vacío para Co-comprador. Forzando uso de la API.")
                    usar_nombres_api = True
                    
                # CASO B: Discrepancia con la API
                else:
                    Registrador.info("Discrepancia detectada en Co-comprador. Forzando 2da búsqueda en RENIEC...")
                    
                    page.once("dialog", lambda dialog: dialog.accept())
                    page.locator("input[name='cmdBuscaDocuAdmi']").click()
                    page.wait_for_timeout(3000)
                    
                    # --- LA MAGIA: REVISAMOS SI EL SAT LO CORRIGIÓ ---
                    sat_paterno2 = page.locator("#txtApePateAdmi").input_value().strip()
                    sat_materno2 = page.locator("#txtApeMateAdmi").input_value().strip()
                    sat_nombre2 = page.locator("#txtNombAdmi").input_value().strip()
                    
                    if sat_paterno2 != apellido_paterno or sat_materno2 != apellido_materno or sat_nombre2 != nombre:
                        Registrador.warning("SAT terco con Co-comprador. ¡Activando permiso para usar la API!")
                        usar_nombres_api = True # <--- ¡AQUÍ LE DAMOS PERMISO AL PASO 3!
                    else:
                        Registrador.info("Nombres oficiales confirmados por el SAT.")
            else:
                print("✅ Los nombres del co-comprador coinciden con el SAT.")

            # ==========================================================
            # 3. LLENADO DE NOMBRES Y APELLIDOS
            # ==========================================================
            if usar_nombres_api:
                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)
                if not apellido_materno:
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                nombre_a_validar = nombre
                page.locator("input[name='txtNombAdmi']").fill(nombre)
            else:
                # Dejamos la info de RENIEC, solo validamos el check materno
                if not page.locator("#txtApeMateAdmi").input_value().strip():
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                
                nombre_a_validar = page.locator("#txtNombAdmi").input_value().strip()

            # Límite de 30 caracteres
            if len(nombre_a_validar) > 30:
                Registrador.warning(f"Nombre de Co-comprador excede 30 chars (Longitud: {len(nombre_a_validar)}). Se intentará enviar igual.")

            # ==========================================================
            # 4. RESTO DE DATOS (Manda la API)
            # ==========================================================
            page.locator("input[name='txtTelefono1']").fill("") # Limpiamos fijo
            
            # Usamos tu validación de None para evitar errores
            celular_valor = celular if celular is not None else ""
            page.locator("input[name='txtTelefono2']").fill(celular_valor)
            
            correo_valor = correoElectronico if correoElectronico is not None else ""
            page.locator("input[name='txtCorreoElectronico']").fill(correo_valor)

            # Distrito y Dirección
            if page.is_enabled("#ddlDistrito"):
                page.select_option("#ddlDistrito", value=distrito)
                page.locator("input[name='txtDireccion']").fill(direccion)
            else:
                Registrador.warning("El combo de distrito no está habilitado en el SAT.")

            # Fecha de Nacimiento
            if fecha_nacimiento:
                try:
                    fecha_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").strftime("%d/%m/%Y")
                    print(f"Fecha de nacimiento a ingresar: {fecha_formateada}")
                    page.locator("input[name='txtFecNacPersona']").fill(fecha_formateada)
                except ValueError as e:
                    Registrador.error(f"Error al procesar la fecha de nacimiento: {e}")
            else:
                Registrador.warning("No se proporcionó fecha de nacimiento. Campo omitido.")

            # ==========================================================
            # 5. FINALIZACIÓN
            # ==========================================================
            input("Corrige los datos si es necesario y Presiona Enter para continuar...")
            print(" Datos bien regularizados")
            Registrador.info("Terminé la primera hoja del Co-comprador")

            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnSiguiente']").click()
            
      
            #DATOS DEL VEHICULO-------------------------                    
            #fechaInscripcion1 = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
            # Formatear el objeto datetime a la cadena deseada (día-mes-año)
            
            time.sleep(3)
            # input("Corregir fecha")
            fecha_formateada = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
            fecha_formateada = fecha_formateada.strftime("%d-%m-%Y")
            fecha_formateada = fecha_formateada.replace("-", "/")
            print(fecha_formateada)
            page.locator("input[name='txtInscripcion']").fill(fecha_formateada)
            #nput("Corregir fecha")

            page.locator("input[name='txtAnoModelo']").fill(anoModelo)
            page.keyboard.press("Enter")                

            value_categoriaMtc=categoria(categoriaMtc)
            page.select_option("#ddlCatMTC",value=str(value_categoriaMtc))

            # carroceria=funcarroceria()
            valuecarroceria=encontrar_carroceria(page,carroceria)
            page.select_option("#ddlCarroceria",value=valuecarroceria)

            #page.locator("input[name='txtAnoFabrica']").fill(anoFabricacion)
            time.sleep(2)
            # page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=100)
            time.sleep(2)
            if not encontrar_marca(page,marcas):
                raise ValueError("Marca no encontrada")

            v_modelos=f"{modelos}".strip()
            time.sleep(2)
            
            # VALIDACION NRO MOTOR
            if " " in str(nroMotor):
                print("*" * 40)
                print("*" * 40)
                print("CAMBIO REALIZADO")
                print("*" * 40)
                print("*" * 40)

            # 3. Limpiamos el dato y lo escribimos en la web
            nroMotor_limpio = str(nroMotor).replace(" ", "")
            page.locator("input[name='txtMotor']").fill(nroMotor_limpio)
            page.locator("input[name='txtNroAsientos']").fill(nAsientos)

            value_combustible=encontrar_combustible(combustible)
            page.select_option("#ddlTipoMotor",value=str(value_combustible))
            
            formulaRodante1=encontrar_formulaRodante(formulaRodante)
            page.select_option("#ddlTraccion",value=str(formulaRodante1))

            #rpt_cilindraje=int(cilindraje)*1000
            try:
                cilindraje_int = int(cilindraje)
            except ValueError:
                cilindraje_int = 0  # Manejo de error si no es número

            # 2. APLICAMOS LA CORRECCIÓN DE CEROS EXTRAS
            # Si es mayor a 20,000 (ningún auto normal pasa de 10k-12k cc), asumimos error de formato
            if cilindraje_int > 50000: 
                cilindraje_int = cilindraje_int // 1000  # División entera: 1995000 -> 1995

            # 3. Tu lógica de llenado (usando la variable corregida)
            if cilindraje_int == 0:
                page.locator("#txtCilindraje").fill("1")
            elif cilindraje_int > 0:
                page.locator("#txtCilindraje").fill(str(cilindraje_int))

            #rpt_pesobruto=int(pesoBruto) * 1000
            page.locator("input[name='txtPesoBruto']").fill(str(int(pesoBruto)))
            page.keyboard.press("Enter")

            value_T=encontrar_transmision(transmision)
            page.select_option("#ddlTransmision",value=str(value_T))

            page.locator("#btnDetermClaseCat").click
            page.wait_for_timeout(2000)
        
            # Opcional: Solo para tu control en consola (no afecta la lógica)
            clase_vehiculo = page.locator("#ddlClase").input_value()
            print(f"ℹ️ Clase detectada antes de buscar modelo: {clase_vehiculo}")
            
            # Seleccionar modelo ULTIMO PASO
            v_modelos=f"{modelos}".strip()
            time.sleep(2)
            page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=30)
            v_modeloCompleto = combinar_modelo_version(modelos, version)
            
            time.sleep(2)
            resultado_seleccion = encontrar_modelo(page, modelos, version, formulaRodante=formulaRodante, peso_bruto=pesoBruto)
            
            #DATOS DE LA ADQUISICION------------------
            # TIPO TRANSFERENCIA
            page.select_option("#ddlTipoTransferencia",value={tipodeadquisicion})

            fechaAdquisicion = datetime.strptime(fechasAdquisicion_factura_cancelacion, "%Y-%m-%d")
            fecha_formateada1 = fechaAdquisicion.strftime("%d-%m-%Y")
            fecha_formateada1 = fecha_formateada1.replace("-", "/")
            print(fecha_formateada1)
            page.locator("input[name='txtFechaAdqui']").fill(fecha_formateada1)

            comprador_infoes_list = compradores_array
            porcentaje=100

            longitud_comprador_infoes = len(comprador_infoes_list)
            print(longitud_comprador_infoes)
            if longitud_comprador_infoes > 1:
                page.select_option("#ddlTipoPropiedad",value="6")
                valorporcentaje = porcentaje / longitud_comprador_infoes
                porcentaje =int(valorporcentaje)
                page.locator("input[name='txtPorcentaje']").fill(str(porcentaje))
            else:
                page.select_option("#ddlTipoPropiedad",value="5")
                #page.locator("input[name='txtPorcentaje']").fill(str(porcentaje))

            time.sleep(3)
            valueM=value_moneda(moneda)
            page.select_option("#ddlTipoMoneda",value=valueM) 

            page.locator("input[name='txtValorTrasferencia']").fill(valorMonetario)
            
            # Apartados de documentos adjuntos

            page.locator("input[name='grdAdjuntos$ctl07$chkSel']").check()
            page.locator("input[name='grdAdjuntos$ctl08$chkSel']").check()
            
            page.locator("input[name='grdAdjuntos$ctl10$chkSel']").check()

            page.locator("input[name='txtOtros']").fill("Recibos")

            input("Corrige el modelo...") 
            Registrador.info("Termine la segunda hoja")

            # Parte final
            
            page.locator("input[name='btnValidar']").click()
            
            time.sleep(5)
            
            #page.select_option("#ddlClaseV", value="11")


            # page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=200)
            time.sleep(2)
            if not encontrar_marca1(page,marcas):
                raise ValueError("Marca no encontrada")
            time.sleep(2)

            encontrar_modelo2(page, modelos, version, seleccion_previa=resultado_seleccion, formulaRodante=formulaRodante, peso_bruto=pesoBruto)
            input("Corrige el modelo...")

            
            page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))
            page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)
            page.select_option("#ddlTipoMonedaV",value=valueM)
            
            Registrador.info("Termine la parte final de la hoja")
            time.sleep(2)

            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnAceptarV']").click()
                time.sleep(2)

            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass
            time.sleep(2)

            Guardar_Archivos(page,browser,inmatriculaciones,num_documento)

        else:
            
            # ==============================================================================
            # FASE: DATOS DEL CO-COMPRADOR
            # ==============================================================================
            print("\n--- INICIANDO LLENADO DE DATOS: CO-COMPRADOR ---")
            page.select_option("#ddlTipoAdministrado", value=tipo_persona)
            page.select_option("#ddlTipoDocuAdmi", value=tipo_documento)
            page.keyboard.press('Tab')

            print(f"Buscando documento del co-comprador: {num_documento}")
            page.locator("input[name='txtDocuAdmi']").fill(num_documento)
            
            # 1. BÚSQUEDA 1
            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except: 
                pass
            
            page.wait_for_timeout(2000)
            page.keyboard.press('Tab')

            # 2. VALIDACIÓN Y DOBLE BÚSQUEDA
            sat_pate_admi = page.locator("#txtApePateAdmi").input_value().strip()
            sat_mate_admi = page.locator("#txtApeMateAdmi").input_value().strip()
            sat_nomb_admi = page.locator("#txtNombAdmi").input_value().strip()

            usar_api_admi = False
            
            if sat_pate_admi != apellido_paterno or sat_mate_admi != apellido_materno or sat_nomb_admi != nombre:
                # CASO A: SAT vacío
                if not sat_pate_admi and not sat_nomb_admi:
                    Registrador.warning("SAT vacío para el Co-comprador. Forzando uso de la API.")
                    usar_api_admi = True
                    
                # CASO B: Discrepancia con la API
                else:
                    Registrador.info("Discrepancia en Co-comprador. Forzando 2da búsqueda en RENIEC...")
                    
                    page.once("dialog", lambda dialog: dialog.accept())
                    page.locator("input[name='cmdBuscaDocuAdmi']").click()
                    page.wait_for_timeout(3000)
                    
                    # ==========================================================
                    # 🚨 INYECCIÓN DE SEGURIDAD: ÚLTIMA LECTURA
                    # ==========================================================
                    sat_pate_admi2 = page.locator("#txtApePateAdmi").input_value().strip()
                    sat_mate_admi2 = page.locator("#txtApeMateAdmi").input_value().strip()
                    sat_nomb_admi2 = page.locator("#txtNombAdmi").input_value().strip()
                    
                    if sat_pate_admi2 != apellido_paterno or sat_mate_admi2 != apellido_materno or sat_nomb_admi2 != nombre:
                        Registrador.warning("SAT terco con el Co-comprador. ¡Forzando datos de la API!")
                        usar_api_admi = True
                    else:
                        Registrador.info("La segunda búsqueda corrigió los nombres. Todo en orden.")
            else:
                print("✅ Los nombres del co-comprador coinciden con el SAT.")

            # 3. LLENADO DE NOMBRES Y APELLIDOS
            if usar_api_admi:
                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)
                if not apellido_materno:
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                nombre_val_admi = nombre
                page.locator("input[name='txtNombAdmi']").fill(nombre)
            else:
                # Dejamos la info de RENIEC, solo validamos el check materno
                if not page.locator("#txtApeMateAdmi").input_value().strip():
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                
                nombre_val_admi = page.locator("#txtNombAdmi").input_value().strip()

            # Límite de 30 caracteres
            if len(nombre_val_admi) > 30:
                Registrador.warning(f"Nombre de Co-comprador excede 30 chars (Longitud: {len(nombre_val_admi)}).")

            # 4. RESTO DE DATOS (Manda la API)
            page.locator("input[name='txtTelefono1']").fill("") # Limpiamos fijo
            
            celular_valor = celular if celular is not None else ""
            page.locator("input[name='txtTelefono2']").fill(celular_valor)
            
            correo_valor = correoElectronico if correoElectronico is not None else ""
            page.locator("input[name='txtCorreoElectronico']").fill(correo_valor)

            # Distrito y Dirección
            if page.is_enabled("#ddlDistrito"):
                page.select_option("#ddlDistrito", value=distrito)
                page.locator("input[name='txtDireccion']").fill(direccion)
            else:
                Registrador.warning("El combo de distrito no está habilitado en el SAT.")

            # Fecha de Nacimiento
            if fecha_nacimiento:
                try:
                    fecha_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").strftime("%d/%m/%Y")
                    page.locator("input[name='txtFecNacPersona']").fill(fecha_formateada)
                except ValueError as e:
                    Registrador.error(f"Error al procesar la fecha de nacimiento: {e}")
            else:
                Registrador.warning("No se ingresó fecha de nacimiento. Campo omitido.")




            # 5. FINALIZACIÓN DE LA HOJA
            input("Corrige los datos del co-comprador si es necesario y presiona Enter para continuar...")
            Registrador.info("Terminé la hoja del co-comprador.")

            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnSiguiente']").click()
                
            # Variables originales de tu código que preparan la siguiente etapa
            comprador_infoes_list = compradores_array
            porcentaje = 100
            longitud_comprador_infoes = len(comprador_infoes_list)
            print(f"Total de compradores en la lista: {longitud_comprador_infoes}")

            page.evaluate("""
                let input = document.querySelector("input[name='txtNroAsientos']");
                input.removeAttribute('disabled');
                input.value = '';
                """)
            # Llenar el nuevo valor
            page.locator("input[name='txtNroAsientos']").fill(nAsientos)
            
            if longitud_comprador_infoes > 1:
                valorporcentaje = porcentaje / longitud_comprador_infoes
                porcentaje =int(valorporcentaje)
                page.locator("input[name='txtPorcentaje']").fill(str(porcentaje))

            
            Registrador.info("Termine la segunda hoja del coocomprador")

            page.locator("#btnSiguiente").click()

            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass
            time.sleep(2)   

            Guardar_Archivos(page,browser,inmatriculaciones,num_documento)

    except Exception as e:
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto=f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        error_message = f"""
        <p>Hubo un error al momento de procesar los datos del cliente(Natural Coo-comprador). </p>
        <p>Error: {e} </p>
        <pre>{traceback.format_exc()}</pre>
        """
        enviar_email_Api(destinos, asunto, error_message)
        print(e)
        print(traceback.format_exc())