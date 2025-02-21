from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Cargar variables de entorno definidas en el fichero .env
load_dotenv()

# Configuración de variables de entorno para SendGrid
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
    raise Exception("Falta la configuración de SendGrid en las variables de entorno.")

app = FastAPI()

# Modelo para recibir los parámetros del endpoint
class EmailTemplate(BaseModel):
    template_id: str
    substitutions: dict
    # Se puede pasar la dirección de destino o utilizar la definida en las variables de entorno
    to_email: str = os.getenv("SENDGRID_TO_EMAIL")  

def send_email(template_id: str, substitutions: dict, to_email: str) -> int:
    """
    Envía un email utilizando una plantilla dinámica de SendGrid.

    :param template_id: ID de la plantilla en SendGrid.
    :param substitutions: Diccionario con los valores a sustituir en la plantilla.
    :param to_email: Dirección de correo destino.
    :return: Código de estado HTTP de la respuesta de SendGrid.
    """
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
    )
    message.template_id = template_id
    message.dynamic_template_data = substitutions

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        raise e

@app.post("/send_email")
async def send_email_endpoint(email_data: EmailTemplate):
    """
    Endpoint REST que recibe el ID de la plantilla y el mapa de sustituciones para enviar un email.
    """
    try:
        status_code = send_email(email_data.template_id, email_data.substitutions, email_data.to_email)
        return {"status": "Email enviado", "status_code": status_code}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@app.get("/test_email")
async def test_email():
    """
    Función de test que invoca send_email con parámetros predefinidos para enviar un email de prueba.
    """
    test_template_id = os.getenv("SENDGRID_TEST_TEMPLATE_ID")
    test_to_email = os.getenv("SENDGRID_TEST_TO_EMAIL", SENDGRID_FROM_EMAIL)
    if not test_template_id:
        raise HTTPException(status_code=400, detail="Falta la variable de entorno SENDGRID_TEST_TEMPLATE_ID para la prueba.")

    test_substitutions = {
        "nombre": "Usuario de prueba",
        "mensaje": "Este es un email de prueba enviado desde FastAPI utilizando SendGrid."
    }

    try:
        status_code = send_email(test_template_id, test_substitutions, test_to_email)
        return {"status": "Email de prueba enviado", "status_code": status_code}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

