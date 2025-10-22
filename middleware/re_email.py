
import requests
import logging
import os


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def enviar_email_Api(destinos, asunto, mensaje):
    """
    Envía un correo electrónico a través de una API.

    Args:
        destinos (str): Lista de destinatarios separados por comas o un solo destinatario.
        asunto (str): El asunto del correo electrónico.
        mensaje (str): El cuerpo del correo electrónico.

    Returns:
        requests.Response or None: El objeto de respuesta de la API si la petición fue exitosa,
                                     None si ocurrió un error.
    """
    url_EMAILAPI = os.getenv('URL_EMAILAPI') 
    url = url_EMAILAPI
    payload = {
        "codigo": "01",
        "destinos": destinos,
        "asunto": asunto,
        "mensaje": mensaje
    }

    try:
        logging.info(f"Enviando correo electrónico a la API: {url}")
        logging.debug(f"Payload del correo electrónico: {payload}")

        response = requests.post(url, json=payload)
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP erróneos (4xx o 5xx)

        logging.info(f"Correo electrónico enviado exitosamente. Código de estado: {response.status_code}")
        logging.debug(f"Respuesta de la API: {response.json()}")
        return response  

    except requests.exceptions.RequestException as e:
        logging.error(f"Error al enviar el correo electrónico a la API: {e}")
        return None  # Retornar None para indicar que hubo un error

    except Exception as e:
        logging.error(f"Error inesperado al enviar el correo electrónico: {e}")
        return None
    


