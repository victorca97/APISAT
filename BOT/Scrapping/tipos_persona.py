import json
from utils.loggers import Registrador
from datetime import datetime
import time
from utils.common import *
from middleware.re_email import enviar_email_Api
import traceback
from playwright.sync_api import Page

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
            Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 10 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
            raise ValueError(f"La dirección de la Empresa '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre} con el DNI {num_documento}")
        

        try:
            page.select_option("#ddlTipoAdministrado",value=tipo_persona)
            page.select_option("#ddlTipoDocuAdmi",value=tipo_documento)
            page.keyboard.press('Tab')

            page.locator("input[name='txtDocuAdmi']").fill(num_documento)

            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass

            page.keyboard.press('Tab')

            apellidoPaterno=page.locator("#txtApePateAdmi").get_attribute('value')
            print(apellidoPaterno)
            apellidoMaterno=page.locator("#txtApeMateAdmi").get_attribute('value')
            print(apellidoMaterno)
            print("---------------------")
            print(apellido_materno)
            print(apellido_paterno)


            if apellidoMaterno==apellido_materno  and apellidoPaterno ==apellido_paterno :

                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

                if apellido_materno == "":
                    page.locator("input[name='txtApeMateAdmi']").fill("")
                else:   
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)

                page.locator("input[name='txtNombAdmi']").fill(nombre)

                page.locator("input[name='txtTelefono1']").fill("")

                
                page.locator("input[name='txtTelefono2']").fill(celular)
                page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                if page.is_enabled("#ddlDistrito"):
                    page.select_option("#ddlDistrito",value=distrito)
                    page.locator("input[name='txtDireccion']").fill(direccion)

                if fecha_nacimiento:  # Solo entra si NO está vacío
                    try:
                        fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                        fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y").replace("-", "/")
                        print(fecha_nacimiento_formateada)
                        page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
                    except ValueError as e:
                        print(f"❌ Error al procesar la fecha de nacimiento: {e}")
                else:
                    print("⚠️ No se ingresó fecha de nacimiento. Campo omitido.")

            else:
                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

                if apellido_materno == "":
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                print(nombre)
                page.locator("input[name='txtNombAdmi']").fill(nombre)

                print(razon_social)
                page.locator("input[name='txtRazoSociAdmi']").fill(razon_social)

                #page.locator("input[name='txtTelefono1']").fill(telefono_fijo)
                print(celular)
                page.locator("input[name='txtTelefono2']").fill(celular)

                page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                #page.locator("input[name='txtCorreoElectronico2']").fill(correoElectronicoAlternativo)

                page.locator("input[name='txtTelefono1']").fill("")


                fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y")
                fecha_nacimiento_formateada = fecha_nacimiento_formateada.replace("-", "/")
                print(fecha_nacimiento_formateada)
                page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)

                if page.is_enabled("#ddlDistrito"):
                    page.select_option("#ddlDistrito",value=distrito)
                    page.locator("input[name='txtDireccion']").fill(direccion)

            
            page.select_option("#ddlTipoRelacionado",value="0")

            input("Corrige la direccion u otro dato si es necesario y presiona Enter para continuar...")
            Registrador.info("Termine la primera hoja")

            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnSiguiente']").click()

            page.wait_for_load_state()
            time.sleep(5)

            #DATOS DEL VEHICULO------------------
            
            #fechaInscripcion1 = datetime.strptime(fechaInscripcion, "%Y-%m-%d")  

            # Formatear el objeto datetime a la cadena deseada (día-mes-año)
        except Exception as e:
            page.locator("#lnkRegresar").click()
            raise

        try:

            fecha_formateada = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
            fecha_formateada = fecha_formateada.strftime("%d-%m-%Y")
            fecha_formateada = fecha_formateada.replace("-", "/")
            print(fecha_formateada)
            page.locator("input[name='txtInscripcion']").fill(fecha_formateada)
            # input("Ingresar fecha de inscripcion...")

            page.locator("input[name='txtAnoModelo']").fill(anoModelo)
            page.keyboard.press("Enter")                

            value_categoriaMtc=categoria(categoriaMtc)
            page.select_option("#ddlCatMTC",value=str(value_categoriaMtc))

            valuecarroceria=encontrar_carroceria(page,carroceria)
            page.select_option("#ddlCarroceria",value=valuecarroceria)

            #page.locator("input[name='txtAnoFabrica']").fill(anoFabricacion)

            time.sleep(2)
            page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=700)
            time.sleep(2)

            if not encontrar_marca(page,marcas):
                raise ValueError("Marca no encontrada")

            time.sleep(2)
            page.locator("input[name='txtMotor']").fill(nroMotor)
            page.locator("input[name='txtNroAsientos']").fill(nAsientos)

            value_combustible=encontrar_combustible(combustible)
            page.select_option("#ddlTipoMotor",value=str(value_combustible))
            
            formulaRodante1=encontrar_formulaRodante(formulaRodante)
            page.select_option("#ddlTraccion",value=str(formulaRodante1))

            #rpt_cilindraje=int(cilindraje)*1000
            if cilindraje == 0:  # Si es cero
                page.locator("#txtCilindraje").fill("1")
            elif cilindraje > 0:  # Solo llenar si es positivo
                page.locator("#txtCilindraje").fill(str(cilindraje))


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
            page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=700)
            v_modeloCompleto = combinar_modelo_version(modelos, version)
            
            time.sleep(2)
            encontrar_modelo(page, modelos, version)
            


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
        
        page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=200)
        time.sleep(2)
        if not encontrar_marca1(page,marcas):
            raise ValueError("Marca no encontrada")
        time.sleep(2)

        encontrar_modelo2(page,modelos, version)        
        input("Corrige el modelo...")
        
        page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))
        page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)
        page.select_option("#ddlTipoMonedaV",value=valueM)

        Registrador.info("Termine la parte final de la hoja")
            
        with page.expect_navigation(wait_until='load'):
            page.locator("input[name='btnAceptarV']").click()
            time.sleep(1)
        try:
            page.on("dialog", lambda dialog: dialog.accept())
        except:
            pass
        time.sleep(1) 

        Guardar_Archivos(page,browser,inmatriculaciones,num_documento)


    except Exception as e:
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto=f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        error_message = f"""
        <p>Hubo un error al momento de procesar los datos del cliente(persona natural). </p>
        <p>Error: {e} </p>
        <p>Datos JSON:</p>
        <pre>{json_formateado}</pre>
        """
        print(traceback.format_exc())
        enviar_email_Api(destinos, asunto, error_message)

    except Exception as ve:
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto=f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        error_message = f"""
        <html>
        <body>
            <h3>Hubo un error en la validación:</h3>
            <p><strong>Error:</strong> {ve}</p>
            <p><strong>Traceback:</strong></p>
            <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        """
        print(traceback.format_exc())
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
            Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 10 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
            raise ValueError(f"La dirección de la Empresa '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre} con el DNI {num_documento}")
    
        if len(direccionR)< 7:
            Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 10 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
            raise ValueError(f"La dirección del representate '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombreR} con el DNI {num_documentoR}")
        
        try:
            page.select_option("#ddlTipoAdministrado",value=tipo_persona)
            page.keyboard.press('Tab')

            print(num_documento)
            page.locator("input[name='txtDocuAdmi']").fill(num_documento)
            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass

            page.keyboard.press('Tab')

            value_razonsocial=page.locator("#txtRazoSociAdmi").get_attribute('value')
            print(value_razonsocial)

            if value_razonsocial==razon_social:
                print("Es la misma razon social")

                page.locator("input[name='txtRazoSociAdmi']").fill(razon_social)
                
                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

                if apellido_materno == "":
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                page.locator("input[name='txtNombAdmi']").fill(nombre)
                page.locator("input[name='txtTelefono2']").fill(celular)
                page.locator("input[name='txtTelefono1']").fill(telefonoFijo)
                page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                
                distritoenable=page.locator("#ddlDistrito").is_enabled()
                if distritoenable:
                    page.select_option("#ddlDistrito",value=distrito)
                    page.locator("input[name='txtDireccion']").fill(direccion)
                else:
                    print("El distrito no esta habilitado")
                input("Corrige la direccion si es necesario y presiona Enter para continuar...")
                
            else:
                print("No es la misma razon social")            
                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

                if apellido_materno == "":
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                print(nombre)
                page.locator("input[name='txtNombAdmi']").fill(nombre)

                print(razon_social)
                page.locator("input[name='txtRazoSociAdmi']").fill(razon_social)

                print(celular)
                page.locator("input[name='txtTelefono2']").fill(celular)
                page.locator("input[name='txtTelefono1']").fill(telefonoFijo)

                page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                #page.locator("input[name='txtCorreoElectronico2']").fill(correoElectronicoAlternativo)

                distritoenable=page.locator("#ddlDistrito").is_enabled()
                if distritoenable:
                    page.select_option("#ddlDistrito",value=distrito)
                    page.locator("input[name='txtDireccion']").fill(direccion)

                # else:
                #     print("El distrito no esta habilitado")
                #     page.evaluate("""
                #     let input = document.querySelector("input[name='txtDireccion']");
                #     input.removeAttribute('disabled');
                #     input.value = '';
                #     """)
                input("Corrige la direccion si es necesario y presiona Enter para continuar...")
            # Llenar el nuevo valor
            # page.locator("input[name='txtNroAsientos']").fill(nAsientos)
            #Datos del representate--------------------

            print("DATOS DEL REPRESENTATE ")

            page.select_option("#ddlTipoDocuRela",value=tipo_documentoR)

            valuedocumento=page.locator("#txtDocuRela").is_enabled()
            if valuedocumento:
                page.locator("#btnNuevaBusquedaRel").click()
                page.locator("#txtDocuRela").fill(num_documentoR)
                page.locator("#cmdBuscaDocuRel").click()
            value_ApellidoPaterno=page.locator("#txtApePateRela").get_attribute('value')
            value_ApellidoMaterno=page.locator("#txtApeMateRela").get_attribute('value')
            print(value_ApellidoPaterno)
            print(value_ApellidoMaterno)

            
            if value_ApellidoPaterno == apellido_paternoR and value_ApellidoMaterno == apellido_maternoR:
                print("entre aca")
                page.locator("input[name='txtTelefono2Rela']").fill(celularR)

                page.locator("input[name='txtTelefono1Rela']").fill("")

                page.locator("input[name='txtCorreoElectronicoRela']").fill(correoElectronicoR)

                page.select_option("#ddlDistritoRela",value=distritoR)
                page.locator("input[name='txtDireccionRela']").fill(direccionR)
                
                input("Corrige la direccion si es necesario y presiona Enter para continuar...")
                
            else:
                print("entre aca2")
                page.locator("input[name='txtApePateRela']").fill(apellido_paternoR)
                
                if apellido_maternoR == "":
                    page.locator("input[name='chkSinApeMatRela']").click()
                else:
                    page.locator("input[name='txtApeMateRela']").fill(apellido_maternoR)

                page.locator("input[name='txtNombRela']").fill(nombreR)

                page.locator("input[name='txtTelefono2Rela']").fill(celularR)

                page.locator("input[name='txtTelefono1Rela']").fill("")

                page.locator("input[name='txtCorreoElectronicoRela']").fill(correoElectronicoR)

                page.select_option("#ddlDistritoRela",value=distritoR)
                page.locator("input[name='txtDireccionRela']").fill(direccion)
                
                input("Corrige la direccion si es necesario y presiona Enter para continuar...")
            page.locator("input[name='btnSiguiente']").click()
        except Exception as e:
            page.locator("#lnkRegresar").click()
            raise

            #DATOS DEL VEHICULO------------------
            #fechaInscripcion1 = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
        try:
            # Formatear el objeto datetime a la cadena deseada (día-mes-año)
            # input("Presiona Enter para continuar...")
            
            fecha_formateada = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
            fecha_formateada = fecha_formateada.strftime("%d-%m-%Y")
            fecha_formateada = fecha_formateada.replace("-", "/")
            print(fecha_formateada)
            page.locator("input[name='txtInscripcion']").fill(fecha_formateada)
            # input("Ingresar fecha de inscripcion...")
            page.locator("input[name='txtAnoModelo']").fill(anoModelo)
            page.keyboard.press("Enter")                

            value_categoriaMtc=categoria(categoriaMtc)
            page.select_option("#ddlCatMTC",value=str(value_categoriaMtc))

            valuecarroceria=encontrar_carroceria(page,carroceria)
            page.select_option("#ddlCarroceria",value=valuecarroceria)

            #page.locator("input[name='txtAnoFabrica']").fill(anoFabricacion)

            time.sleep(2)
            page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=100)
            time.sleep(2)
            if not encontrar_marca(page,marcas):
                raise ValueError("Marca no encontrada")

            
            time.sleep(2)
            page.locator("input[name='txtMotor']").fill(nroMotor)
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
            if cilindraje == 0:  # Si es cero
                page.locator("#txtCilindraje").fill("1")
            elif cilindraje > 0:  # Solo llenar si es positivo
                page.locator("#txtCilindraje").fill(str(cilindraje))
                
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
            page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=700)
            v_modeloCompleto = combinar_modelo_version(modelos, version)
            
            time.sleep(2)
            encontrar_modelo(page, modelos, version)
            
            #DATOS DE LA ADQUISICION------------------
            page.select_option("#ddlTipoTransferencia",value={tipodeadquisicion})


            fechaAdquisicion = datetime.strptime(fechasAdquisicion_factura_cancelacion, "%Y-%m-%d")
            fecha_formateada1 = fechaAdquisicion.strftime("%d-%m-%Y")
            fecha_formateada1 = fecha_formateada1.replace("-", "/")
            print(fecha_formateada1)
            page.locator("input[name='txtFechaAdqui']").fill(fecha_formateada1)


            page.select_option("#ddlTipoPropiedad",value="5")

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
            
            time.sleep(3)
        
        #page.select_option("#ddlClaseV", value="11")
        except Exception as e:
            page.locator("#btnCancelar").click()
            raise

        page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=200)
        time.sleep(2)
        if not encontrar_marca1(page,marcas):
            raise ValueError("Marca no encontrada")
        encontrar_modelo2(page,modelos, version)
        input("Corrige el modelo...")
        
        page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))

        page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)

        page.select_option("#ddlTipoMonedaV",value=valueM)

        Registrador.info("Termine la parte final de la hoja")
        
        with page.expect_navigation(wait_until='load'):
            page.locator("input[name='btnAceptarV']").click()
            time.sleep(2)
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
        <p>Hubo un error al momento de procesar los datos del cliente(Juridica). </p>
        <p>Error: {e} </p>
        """
        enviar_email_Api(destinos, asunto, error_message)

    except ValueError as ve:
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto=f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        error_message = f"""
        <html>
        <body>
            <h3>Hubo un error en la validación:</h3>
            <p><strong>Error:</strong> {ve}</p>
            <p><strong>Traceback:</strong></p>
            <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        """
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
                Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 10 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
                raise ValueError(f"La dirección del Conyuje '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre} con el DNI {num_documento}") 

            if len(direccion2) < 7:
                Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 10 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
                raise ValueError(f"La dirección del Conyuje '{direccion2}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre2} con el DNI {num_documento2}")

            try:
                page.select_option("#ddlTipoAdministrado",value=tipo_persona)
                page.select_option("#ddlTipoDocuAdmi",value=tipo_documento)
                page.keyboard.press('Tab')
                
                page.locator("input[name='txtDocuAdmi']").fill(num_documento)

                page.locator("input[name='cmdBuscaDocuAdmi']").click()
                
                try:
                    page.on("dialog", lambda dialog: dialog.accept())
                except:
                    pass

                page.keyboard.press('Tab')

                Numerodni1=page.locator("#txtDocuAdmi").get_attribute('value')

   
                apellidoPaterno=page.locator("#txtApePateAdmi").get_attribute('value')
                apellidoMaterno=page.locator("#txtApeMateAdmi").get_attribute('value')

                if Numerodni1 == num_documento:
#                if num_documento == Numerodni1:                    
                    print("Tengo los datos del comprador 1")
                    
                    if (Numerodni1 == num_documento and
                        apellidoPaterno == apellido_paterno and
                        apellidoMaterno == apellido_materno):
                        print("Los datos coinciden el dni con los apellidos.")
                    
                    
                    page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)
                    if apellido_materno == "":
                        page.locator("input[name='txtApeMateAdmi']").fill("")
                    else:   
                        page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)

                    page.locator("input[name='txtNombAdmi']").fill(nombre)


                    page.locator("input[name='txtTelefono1']").fill("")
                    page.locator("input[name='txtTelefono2']").fill(celular)
                    page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                    
                    if page.is_enabled("#ddlDistrito"):
                        page.select_option("#ddlDistrito",value=distrito)
                        page.locator("input[name='txtDireccion']").fill(direccion)
                    if fecha_nacimiento:  # Solo entra si NO está vacío
                        try:
                            fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                            fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y").replace("-", "/")
                            print(fecha_nacimiento_formateada)
                            page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
                        except ValueError as e:
                            print(f"❌ Error al procesar la fecha de nacimiento: {e}")
                    else:
                        print("⚠️ No se ingresó fecha de nacimiento. Campo omitido.")


                    #conyuge
                    print("Datos del conyuge")

                    page.locator("#btnNuevaBusquedaRel").click()

                    page.select_option("#ddlTipoDocuRela",value=tipo_documento2)

                    page.locator("input[name='txtDocuRela']").fill(num_documento2)

                    #page.select_option("#ddlTipoDocuRela",value=tipo_documento2)
                    #page.select_option("#ddlTipoDocuRela",value=tipo_documento2)
                    page.locator("input[name='cmdBuscaDocuRel']").click()
                    try:
                        page.on("dialog", lambda dialog: dialog.accept())
                    except:
                        pass
                    
                    page.locator("input[name='txtTelefono2Rela']").fill(celular2)
                    page.locator("input[name='txtCorreoElectronicoRela']").fill(correoElectronico2)
                    if fecha_nacimiento2:  # Solo entra si NO está vacío
                        fechaN_formateada = datetime.strptime(fecha_nacimiento2, "%Y-%m-%d")
                        fechaN_formateada = fechaN_formateada.strftime("%d-%m-%Y")
                        fechaN_formateada = fechaN_formateada.replace("-", "/")
                        page.locator("input[name='txtFecNacRelacionado']").fill(fechaN_formateada)
                    else:
                        print("⚠️ No se ingresó fecha de nacimiento del conyuge. Campo omitido.")

                    page.locator("input[name='txtApePateRela']").fill(apellido_paterno2)
                    
                    
                    if apellido_materno == "":
                        page.locator("input[name='chkSinApeMatAdmi']").check()
                    else:
                        page.locator("input[name='txtApeMateRela']").fill(apellido_materno2)
                    
                    page.locator("input[name='txtNombRela']").fill(nombre2)
                    
                    # AGREGAR ESTA VALIDACIÓN NUEVA
                    if apellido_materno2 == "":
                        page.locator("input[name='chkSinApeMatRela']").check()
                    else:
                        page.locator("input[name='txtApeMateRela']").fill(apellido_materno2)

                    page.locator("input[name='txtNombRela']").fill(nombre2)
                    
                    if page.is_enabled("#ddlDistritoRela"):
                        page.select_option("#ddlDistritoRela",value=distrito2)
                        page.locator("input[name='txtDireccionRela']").fill(direccion2)

                    input("Corrige la direccion si es necesario y presiona Enter para continuar...")
                else:
                    print("No Tengo los datos")

                    #datos comprador
                    page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno2)
                    if apellido_materno == "":
                        page.locator("input[name='txtApeMateAdmi']").fill("")
                    else:   
                        page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno2)
                    
                    page.locator("input[name='txtNombAdmi']").fill(nombre2)


                    page.locator("input[name='txtTelefono1']").fill("")
                    page.locator("input[name='txtTelefono2']").fill(celular2)
                    page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico2)
                    
                    if page.is_enabled("#ddlDistrito"):
                        page.select_option("#ddlDistrito",value=distrito2)
                        page.locator("input[name='txtDireccion']").fill(direccion2)
                    if fecha_nacimiento2:  # Solo entra si NO está vacío
                        try:
                            fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento2, "%Y-%m-%d")
                            fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y").replace("-", "/")
                            print(fecha_nacimiento_formateada)
                            page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
                        except ValueError as e:
                            print(f"❌ Error al procesar la fecha de nacimiento: {e}")
                    else:
                        print("⚠️ No se ingresó fecha de nacimiento. Campo omitido.")

                    #conyuge
                    print("Datos del conyuge")

                    page.locator("#btnNuevaBusquedaRel").click()

                    page.locator("input[name='txtDocuRela']").fill(num_documento)

                    #page.select_option("#ddlTipoDocuRela",value=tipo_documento2)
                    #page.select_option("#ddlTipoDocuRela",value=tipo_documento2)
                    page.locator("input[name='cmdBuscaDocuRel']").click()
                    try:
                        page.on("dialog", lambda dialog: dialog.accept())
                    except:
                        pass
                    
                    # Datos del comprador

                    page.locator("input[name='txtTelefono2Rela']").fill(celular)
                    page.locator("input[name='txtCorreoElectronicoRela']").fill(correoElectronico)
                    if fecha_nacimiento:  # Solo entra si NO está vacío
                        fechaN_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                        fechaN_formateada = fechaN_formateada.strftime("%d-%m-%Y")
                        fechaN_formateada = fechaN_formateada.replace("-", "/")
                        page.locator("input[name='txtFecNacRelacionado']").fill(fechaN_formateada)
                    else:
                        print("⚠️ No se ingresó fecha de nacimiento. Campo omitido.")

                    if page.is_enabled("#ddlDistritoRela"):
                        page.select_option("#ddlDistritoRela",value=distrito2)
                        page.locator("input[name='txtDireccionRela']").fill(direccion2)
                        
                input("Corrige la direccion si es necesario y presiona Enter para continuar...")

                with page.expect_navigation(wait_until='load'):
                    page.locator("input[name='btnSiguiente']").click()
        
            except Exception as e:
                page.locator("#lnkRegresar").click()
                raise
            
                
            try:
                #DATOS DEL VEHICULO-------------------------                    
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
                page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=100)
                time.sleep(2)
                if not encontrar_marca(page,marcas):
                    raise ValueError("Marca no encontrada")

                time.sleep(2)
                
                page.locator("input[name='txtMotor']").fill(nroMotor)
                page.locator("input[name='txtNroAsientos']").fill(nAsientos)

                value_combustible=encontrar_combustible(combustible)
                page.select_option("#ddlTipoMotor",value=str(value_combustible))
                
                formulaRodante1=encontrar_formulaRodante(formulaRodante)
                page.select_option("#ddlTraccion",value=str(formulaRodante1))

                #rpt_cilindraje=int(cilindraje)*1000
                # Después de las validaciones, llenar el campo en la página
                if cilindraje == 0:  # Si es cero
                    page.locator("#txtCilindraje").fill("1")
                elif cilindraje > 0:  # Solo llenar si es positivo
                    page.locator("#txtCilindraje").fill(str(cilindraje))


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
                page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=700)
                v_modeloCompleto = combinar_modelo_version(modelos, version)
                
                time.sleep(2)
                encontrar_modelo(page, modelos, version)


                #DATOS DE LA ADQUISICION------------------  
                page.select_option("#ddlTipoTransferencia",value={tipodeadquisicion})


                fechaAdquisicion = datetime.strptime(fechasAdquisicion_factura_cancelacion, "%Y-%m-%d")
                fecha_formateada1 = fechaAdquisicion.strftime("%d-%m-%Y")
                fecha_formateada1 = fecha_formateada1.replace("-", "/")
                print(fecha_formateada1)
                page.locator("input[name='txtFechaAdqui']").fill(fecha_formateada1)
#
                # input("Ingresar fecha de adquisicion...")

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

            
            page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=200)
            time.sleep(2)
            if not encontrar_marca1(page,marcas):
                raise ValueError("Marca no encontrada")
            time.sleep(2)

            encontrar_modelo2(page,modelos, version)

            page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))
            page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)
            page.select_option("#ddlTipoMonedaV",value=valueM)
            
            Registrador.info("Termine la parte final de la hoja")
            
            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnAceptarV']").click()
            time.sleep(2)

            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass


            Guardar_Archivos(page,browser,inmatriculaciones,num_documento)


    except Exception as e:
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto=f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        error_message = f"""
        <p>Hubo un error al momento de procesar los datos del cliente(sociedad conyugal). </p>
        <p>Error: {e} </p>
        """
        enviar_email_Api(destinos, asunto, error_message)
        print(traceback.format_exc())

    except ValueError as ve:
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto=f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        error_message = f"""
        <html>
        <body>
            <h3>Hubo un error en la validación:</h3>
            <p><strong>Error:</strong> {ve}</p>
            <p><strong>Traceback:</strong></p>
            <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        """
        enviar_email_Api(destinos, asunto, error_message)
        print(e)
        print(traceback.format_exc())

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
        Registrador.error(f"Su direccion esta mal digitada ya que tiene menos de 10 caracteres la inmatriculacion {inmatriculaciones} y referencia {referencia}")
        raise ValueError(f"La dirección de la Empresa '{direccion}' es muy corta debe tener al menos 10 caracteres. El cliente es {nombre} con el DNI {num_documento}")
    try:
        if inicio_comprador:
            page.select_option("#ddlTipoAdministrado",value=tipo_persona)
            page.select_option("#ddlTipoDocuAdmi",value=tipo_documento)
            page.keyboard.press('Tab')


            page.locator("input[name='txtDocuAdmi']").fill(num_documento)
            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass

            page.keyboard.press('Tab')

            apellidoPaterno=page.locator("#txtApePateAdmi").get_attribute('value')
            print(apellidoPaterno)
            apellidoMaterno=page.locator("#txtApeMateAdmi").get_attribute('value')
            print(apellidoMaterno)
            print("---------------------")
            print(apellido_materno)
            print(apellido_paterno)


            if apellidoMaterno==apellido_materno  and apellidoPaterno ==apellido_paterno :

                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)
                
                if apellido_materno == "":
                    page.locator("input[name='txtApeMateAdmi']").fill("")
                else:   
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)

                page.locator("input[name='txtNombAdmi']").fill(nombre)
                
                page.locator("input[name='txtTelefono2']").fill(celular)
                page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                if page.is_enabled("#ddlDistrito"):
                    page.select_option("#ddlDistrito",value=distrito)
                    page.locator("input[name='txtDireccion']").fill(direccion)

                page.locator("input[name='txtTelefono1']").fill("")

                if fecha_nacimiento:
                    fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.replace("-", "/")
                    print(fecha_nacimiento_formateada)
                    page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
                else:
                    print("No se proporcionó fecha de nacimiento, se omitirá este campo.")

            else:

                page.locator("input[name='txtTelefono1']").fill("")

                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

                if apellido_materno == "":
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                print(nombre)
                page.locator("input[name='txtNombAdmi']").fill(nombre)

                print(razon_social)
                page.locator("input[name='txtRazoSociAdmi']").fill(razon_social)

                #page.locator("input[name='txtTelefono1']").fill(telefono_fijo)
                print(celular)
                celular_valor = celular if celular is not None else ""
                page.locator("input[name='txtTelefono2']").fill(celular_valor)


                correo_valor = correoElectronico if correoElectronico is not None else ""
                page.locator("input[name='txtCorreoElectronico']").fill(correo_valor)
                #page.locator("input[name='txtCorreoElectronico2']").fill(correoElectronicoAlternativo)

                if fecha_nacimiento:
                    fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.replace("-", "/")
                    print(fecha_nacimiento_formateada)
                    page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
                else:
                    print("No se proporcionó fecha de nacimiento, se omitirá este campo.")


                if page.is_enabled("#ddlDistrito"):
                    page.select_option("#ddlDistrito",value=distrito)
                    page.locator("input[name='txtDireccion']").fill(direccion)

            input("Corrige y Presiona Enter para continuar...")
            Registrador.info("Termine la primera hoja")


            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnSiguiente']").click()
            
            #DATOS DEL VEHICULO-------------------------                    
            #fechaInscripcion1 = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
            time.sleep(3)
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
            page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=100)
            time.sleep(2)
            if not encontrar_marca(page,marcas):
                raise ValueError("Marca no encontrada")

            v_modelos=f"{modelos}".strip()
            time.sleep(2)
            
            

            page.locator("input[name='txtMotor']").fill(nroMotor)
            page.locator("input[name='txtNroAsientos']").fill(nAsientos)

            value_combustible=encontrar_combustible(combustible)
            page.select_option("#ddlTipoMotor",value=str(value_combustible))
            
            formulaRodante1=encontrar_formulaRodante(formulaRodante)
            page.select_option("#ddlTraccion",value=str(formulaRodante1))

            #rpt_cilindraje=int(cilindraje)*1000
            if cilindraje == 0:  # Si es cero
                page.locator("#txtCilindraje").fill("1")
            elif cilindraje > 0:  # Solo llenar si es positivo
                page.locator("#txtCilindraje").fill(str(cilindraje))


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
            page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=700)
            v_modeloCompleto = combinar_modelo_version(modelos, version)
            
            time.sleep(2)
            encontrar_modelo(page, modelos, version)
            
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


            

            #apartados de documentos adjuntos

            page.locator("input[name='grdAdjuntos$ctl07$chkSel']").check()
            page.locator("input[name='grdAdjuntos$ctl08$chkSel']").check()
            
            page.locator("input[name='grdAdjuntos$ctl10$chkSel']").check()

            page.locator("input[name='txtOtros']").fill("Recibos")


            input("Corrige el modelo...")  # Pausa para revisión manual si es necesario
            Registrador.info("Termine la segunda hoja")

            # Parte final
            
            page.locator("input[name='btnValidar']").click()
            
            time.sleep(5)
            
            #page.select_option("#ddlClaseV", value="11")


            page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=200)
            time.sleep(2)
            if not encontrar_marca1(page,marcas):
                raise ValueError("Marca no encontrada")
            time.sleep(2)

            encontrar_modelo2(page,modelos, version)
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

            Guardar_Archivos(page,browser,inmatriculaciones,num_documento)



        else:

            page.select_option("#ddlTipoAdministrado",value=tipo_persona)
            page.select_option("#ddlTipoDocuAdmi",value=tipo_documento)
            page.keyboard.press('Tab')


            page.locator("input[name='txtDocuAdmi']").fill(num_documento)
            page.locator("input[name='cmdBuscaDocuAdmi']").click()
            try:
                page.on("dialog", lambda dialog: dialog.accept())
            except:
                pass

            page.keyboard.press('Tab')

            apellidoPaterno=page.locator("#txtApePateAdmi").get_attribute('value')
            print(apellidoPaterno)
            apellidoMaterno=page.locator("#txtApeMateAdmi").get_attribute('value')
            print(apellidoMaterno)
            print("---------------------")
            print(apellido_materno)
            print(apellido_paterno)


            if apellidoMaterno==apellido_materno  and apellidoPaterno ==apellido_paterno :

                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

                if apellido_materno == "":
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                print(nombre)
                page.locator("input[name='txtNombAdmi']").fill(nombre)
                
                page.locator("input[name='txtTelefono2']").fill(celular)
                page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                page.select_option("#ddlDistrito",value=distrito)
                page.locator("input[name='txtDireccion']").fill(direccion)

                page.locator("input[name='txtTelefono2']").fill(celular)

                page.locator("input[name='txtTelefono1']").fill("")

                if fecha_nacimiento:
                    fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.replace("-", "/")
                    print(fecha_nacimiento_formateada)
                    page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
                else:
                    print("⚠️ No se ingresó fecha de nacimiento. Campo omitido.")

            else:

                
                page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

                if apellido_materno == "":
                    page.locator("input[name='chkSinApeMatAdmi']").check()
                else:
                    page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno)
                
                print(nombre)
                page.locator("input[name='txtNombAdmi']").fill(nombre)

                print(razon_social)
                page.locator("input[name='txtRazoSociAdmi']").fill(razon_social)

                #page.locator("input[name='txtTelefono1']").fill(telefono_fijo)
                print(celular)
                page.locator("input[name='txtTelefono2']").fill(celular)

                page.locator("input[name='txtTelefono1']").fill("")

                page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
                #page.locator("input[name='txtCorreoElectronico2']").fill(correoElectronicoAlternativo)

                if fecha_nacimiento:
                    fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y")
                    fecha_nacimiento_formateada = fecha_nacimiento_formateada.replace("-", "/")
                    print(fecha_nacimiento_formateada)
                    page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
                else:
                    print("⚠️ No se ingresó fecha de nacimiento. Campo omitido.")

                page.select_option("#ddlDistrito",value=distrito)
                page.locator("input[name='txtDireccion']").fill(direccion)

            input("Corrige la direccion si es necesario y presiona Enter para continuar...")
            Registrador.info("Termine la primera hoja del coocomprador")

            
            with page.expect_navigation(wait_until='load'):
                page.locator("input[name='btnSiguiente']").click()
                
            comprador_infoes_list = compradores_array
            porcentaje=100

            longitud_comprador_infoes = len(comprador_infoes_list)
            print(longitud_comprador_infoes)
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

    except ValueError as ve:
        destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe","jmallqui@autohub.pe","administracion@autohub.pe"]
        asunto=f"ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones} con la referencia {referencia}"
        error_message = f"""
        <html>
        <body>
            <h3>Hubo un error en la validación:</h3>
            <p><strong>Error:</strong> {ve}</p>
            <p><strong>Traceback:</strong></p>
            <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        """
        enviar_email_Api(destinos, asunto, error_message)
        print(e)
        print(traceback.format_exc())


    




