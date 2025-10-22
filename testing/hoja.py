# def patrimonioAutonomo(): 
#     tipo_persona = comprador_info.get('tipoPersona', None)
#     tipo_documento = comprador_info.get('tipoDocumento', None)
#     num_documento = comprador_info.get('numDocumento', None)
#     celular = comprador_info.get('celular', None)
#     correoElectronico = comprador_info.get('correoElectronico', None)
#     correoElectronicoAlternativo = comprador_info.get('correoElectronicoAlternativo')
#     fecha_nacimiento = "2000-05-21"
#     #fecha_nacimiento = comprador_info.get('fechaDeNacimiento', None)
#     domicilio_fiscal:dict = comprador_info.get('domicilioFiscal', {})
#     distrito = domicilio_fiscal.get('distrito')
#     direccion = domicilio_fiscal.get('direccion')
#     apellido_paterno = comprador_info.get('apellidoPaterno')
#     apellido_materno = comprador_info.get('apellidoMaterno')
#     nombre=comprador_info.get('nombres')
#     razon_social = comprador_info.get('razonSocial', None)
#     tieneRepresentante = comprador_info.get('tieneRepresentante', None)

#     # Acceder a la información de 'adquisicion'
#     adquisicion_info: dict = comprador_info.get('adquisicion', {})
#     fechaInscripcion = adquisicion_info.get('fecha_inscripcion')
#     tipodeadquisicion = adquisicion_info.get('tipoDeAdquisicion')
#     fechasAdquisicion_factura_cancelacion = adquisicion_info.get('fechasAdquisicion_factura_cancelacion')
#     condicionDePropiedad = adquisicion_info.get('condicionDePropiedad')
#     moneda = adquisicion_info.get('moneda')
#     valorMonetario = adquisicion_info.get('valorMonetario')
#     datos_transferente:dict = adquisicion_info.get('datosDelTransferente', {})
#     distritoUbicacion = datos_transferente.get('distritoUbicacion')
    
#     json_formateado = json.dumps(data, indent=4, ensure_ascii=False)

#     try:
#         page.select_option("#ddlTipoAdministrado",value=tipo_persona)
#         page.select_option("#ddlTipoDocuAdmi",value=tipo_documento)
#         page.keyboard.press('Tab')

#         num_documento=limpiar_iden()
#         page.locator("input[name='txtDocuAdmi']").fill(num_documento)

#         page.locator("input[name='cmdBuscaDocuAdmi']").click()
#         page.on("dialog", lambda dialog: dialog.accept())

#         page.keyboard.press('Tab')

#         page.locator("input[name='txtApePateAdmi']").fill(apellido_paterno)

#         if apellido_materno == "":
#             page.locator("input[name='chkSinApeMatAdmi']").check()
#         else:
#             page.locator("input[name='txtApeMateAdmi']").fill(apellido_materno.lower())
        
#         print(nombre)
#         page.locator("input[name='txtNombAdmi']").fill(nombre)

#         print(razon_social)
#         page.locator("input[name='txtRazoSociAdmi']").fill(razon_social)

#         #page.locator("input[name='txtTelefono1']").fill(telefono_fijo)
#         print(celular)
#         page.locator("input[name='txtTelefono2']").fill(celular)

#         page.locator("input[name='txtCorreoElectronico']").fill(correoElectronico)
#         #page.locator("input[name='txtCorreoElectronico2']").fill(correoElectronicoAlternativo)

        
#         fecha_nacimiento_formateada = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
#         fecha_nacimiento_formateada = fecha_nacimiento_formateada.strftime("%d-%m-%Y")
#         fecha_nacimiento_formateada = fecha_nacimiento_formateada.replace("-", "/")
#         print(fecha_nacimiento_formateada)
#         page.locator("input[name='txtFecNacPersona']").fill(fecha_nacimiento_formateada)
#         page.select_option("#ddlDistrito",value=distrito)
#         page.locator("input[name='txtDireccion']").fill(direccion.lower())
        
        
#         #Datos del representate--------------------------

#         page.select_option("#ddlTipoDocuRela",value=tipoDeDocumento1)            
#         page.keyboard.press('Tab')

#         numDocumentoR=limpiar_iden(numDocumento1)
#         page.locator("input[name='txtDocuRela']").fill(numDocumentoR)

#         page.locator("input[name='cmdBuscaDocuRel']").click()

#         page.locator("input[name='txtApePateRela']").fill(apellido_paterno1.lower())
        
#         if apellido_materno1 == "":
#             page.locator("input[name='chkSinApeMatRela']").click()
#         else:
#             page.locator("input[name='txtApeMateRela']").fill(apellido_materno1.lower())

#         page.locator("input[name='txtNombRela']").fill(nombres1.lower())
                    
#         page.locator("input[name='txtTelefono1Rela']").fill(telefono_fijo1)

#         page.locator("input[name='txtTelefono2Rela']").fill(celular1)

#         page.locator("input[name='txtCorreoElectronicoRela']").fill(correo_electronico1)

#         fecha_nacimiento_formateadaR = datetime.strptime(fecha_nacimiento1, "%Y-%m-%d")
#         fecha_nacimiento_formateadaR = fecha_nacimiento_formateadaR.strftime("%d-%m-%Y")
#         fecha_nacimiento_formateadaR = fecha_nacimiento_formateadaR.replace("-", "/")
#         print(fecha_nacimiento_formateadaR)
#         page.locator("input[name='txtFecNacRelacionado']").fill(fecha_nacimiento_formateadaR)


#         page.select_option("#ddlDistritoRela",value=distrito1)
#         page.locator("input[name='txtDireccionRela']").fill(direccion1.lower())


#         page.locator("input[name='btnSiguiente']").click()
        
        
#         #DATOS DEL VEHICULO-------------------------                    
#         #fechaInscripcion1 = datetime.strptime(fechaInscripcion, "%Y-%m-%d")

#         # Formatear el objeto datetime a la cadena deseada (día-mes-año)
#         fecha_formateada = datetime.strptime(fechaInscripcion, "%Y-%m-%d")
#         fecha_formateada = fecha_formateada.strftime("%d-%m-%Y")
#         fecha_formateada = fecha_formateada.replace("-", "/")
#         print(fecha_formateada)
#         page.locator("input[name='txtInscripcion']").fill(fecha_formateada)


#         page.locator("input[name='txtAnoModelo']").fill(anoModelo)
#         page.keyboard.press("Enter")                

#         value_categoriaMtc=categoria(categoriaMtc)
#         page.select_option("#ddlCatMTC",value=str(value_categoriaMtc))

#         # carroceria=funcarroceria()
#         # print(carroceria)
#         page.select_option("#ddlCarroceria",label=str(carroceria).capitalize())

#         #page.locator("input[name='txtAnoFabrica']").fill(anoFabricacion)

#         page.locator("input[name='txtDesMarca']").press_sequentially(marcas,delay=50)
#         encontrar_marca(marcas)

#         v_modelos=f"{modelos} {version}".strip()
#         page.locator("input[name='txtDesModelo']").press_sequentially(v_modelos ,delay=50)
#         encontrar_modelo(v_modelos)

#         page.locator("input[name='txtMotor']").fill(nroMotor)
#         page.locator("input[name='txtNroAsientos']").fill(nAsientos)

#         value_combustible=encontrar_combustible(combustible)
#         page.select_option("#ddlTipoMotor",label=str(value_combustible).capitalize())
        
#         formulaRodante1=encontrar_formulaRodante(formulaRodante)
#         page.select_option("#ddlTraccion",value=str(formulaRodante1))

#         #rpt_cilindraje=int(cilindraje)*1000
#         page.locator("input[name='txtCilindraje']").fill(str(cilindraje))


#         #rpt_pesobruto=int(pesoBruto) * 1000
#         page.locator("input[name='txtPesoBruto']").fill(str(pesoBruto))
#         page.keyboard.press("Enter")



#         # page.select_option("#ddlClase",value="11")
        
#         # try:
#         #     page.locator("#ddlCategoria > option:nth-child(2)").click()
#         # except:
#         #     page.locator("#ddlCategoria > option").click
#         #Clase y categoriaMef

#         value_T=encontrar_transmision(transmision)
#         page.select_option("#ddlTransmision",value=str(value_T))

#         page.locator("#btnDetermClaseCat").click


#         page.select_option("#ddlTipoTransferencia",value={tipodeadquisicion})


#         fechaAdquisicion = datetime.strptime(fechasAdquisicion_factura_cancelacion, "%Y-%m-%d")
#         fecha_formateada1 = fechaAdquisicion.strftime("%d-%m-%Y")
#         fecha_formateada1 = fecha_formateada1.replace("-", "/")
#         print(fecha_formateada1)
#         page.locator("input[name='txtFechaAdqui']").fill(fecha_formateada1)

#         comprador_infoes_list = compradores_array
#         porcentaje=100

#         longitud_comprador_infoes = len(comprador_infoes_list)
#         print(longitud_comprador_infoes)
#         if longitud_comprador_infoes > 1:
#             page.select_option("#ddlTipoPropiedad",value="6")
#             valorporcentaje = porcentaje / longitud_comprador_infoes
#             porcentaje =valorporcentaje
#             page.locator("input[name='txtPorcentaje']").fill(str(porcentaje))
#         else:
#             page.select_option("#ddlTipoPropiedad",value="5")
#             #page.locator("input[name='txtPorcentaje']").fill(str(porcentaje))

#         time.sleep(3)
#         valueM=value_moneda(moneda)
#         page.select_option("#ddlTipoMoneda",value=valueM) 

#         page.locator("input[name='txtValorTrasferencia']").fill(valorMonetario)

#         #apartados de documentos adjuntos

#         page.locator("input[name='grdAdjuntos$ctl07$chkSel']").check()
#         page.locator("input[name='grdAdjuntos$ctl08$chkSel']").check()
        
#         page.locator("input[name='grdAdjuntos$ctl10$chkSel']").check()

#         page.locator("input[name='txtOtros']").fill("Recibos")

#         input("Segunda Hoja")
#         # Parte final
#         page.locator("input[name='btnValidar']").click()
        
#         time.sleep(3)
        
#         #page.select_option("#ddlClaseV", value="11")
        
#         page.locator("input[name='txtDesMarcaV']").press_sequentially(marcas,delay=500)
#         encontrar_marca1(marcas)


#         page.locator("input[name='txtDesModeloV']").press_sequentially(v_modelos,delay=500)
#         #page.keyboard.press("Enter")
#         encontrar_modelo2(v_modelos)

        
        
#         page.locator("input[name='txtFechaAdquiV']").fill(str(fecha_formateada1))

#         page.locator("input[name='txtValorTrasferenciaV']").fill(valorMonetario)

#         page.select_option("#ddlTipoMonedaV",value=valueM)

#         input("LLegue a la parte final cuidado")
        
#         with page.expect_navigation(wait_until='load'):
#             page.locator("input[name='btnAceptarV']").click()
#             page.on("dialog", lambda dialog: dialog.accept())

    
#     except Exception as e:
#         destinos = ["practicantes.sistemas@notariapaino.pe", "jmallqui@notariapaino.pe"]
#         asunto=f"TEST ERROR BOT SAT-AUTOHUB Inmatriculaciones N°{inmatriculaciones}"
#         error_message = f"""
#         <p>Hubo un error al momento de procesar los datos del cliente(Patrimonio Autonomo). </p>
#         <p>Error: {e} </p>
#         <p>Datos JSON:</p>
#         <pre>{json_formateado}</pre>
#         """
    
#         print(error_message)
#         enviar_email_Api(destinos,asunto,error_message)

#     return inmatriculaciones