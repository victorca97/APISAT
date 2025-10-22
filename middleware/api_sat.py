import os
import json
import requests
from utils.loggers import Registrador
from dotenv import load_dotenv

def obtener_datos_sat():
    
    load_dotenv()
    api_url=os.getenv('URL_API_SAT_1')
    print('api',api_url)
    if not api_url :
        print("Error: No se encontro la url del sat en .env")
        return

    try:
        response = requests.get(api_url)
        response.raise_for_status() 

        data_python = response.json() 

        print("Datos de la API:", data_python)

        for objetos in data_python:
            print("Inmatriculaciones:", objetos.get('inmatriculaciones')) 
            print("Placa:", objetos.get('placa'))
            print(f"Cantidad de inmatriculacion a procesar: {len(objetos)}")
            
            compradores = objetos.get('compradores')
            if compradores and isinstance(compradores, list): 
                for comprador in compradores:
                    print("Nombre del comprador:", comprador.get('correoElectronico'))
                    
        Registrador.info(f"Cantidad de inmatriculacion a procesar: {len(objetos)}") 
        return data_python

    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error de Conexión: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Error de Timeout: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Error general en la petición: {err}")
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON de la respuesta: {e}")
    except KeyError as e:
        print(f"Error al acceder a una clave en el JSON: {e}")
    except Exception as e:
        print(f"Otro error inesperado: {e}")

    return None 