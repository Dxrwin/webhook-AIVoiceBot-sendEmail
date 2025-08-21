from flask import Flask, request, jsonify
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client  # Para SMS
import mysql.connector  # Para MySQL
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configuración del correo saliente
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "2525"))
SMTP_USER   = os.getenv("SMTP_USER")
SMTP_PASS   = os.getenv("SMTP_PASS")

# ------------------------------
# CONFIGURACIÓN MYSQL
# ------------------------------
db_config = {
    "host": "localhost",
    "user": "root",          # cámbialo por tu usuario MySQL
    "password": 12345,
    "database": "renovaciones_clientes_links" # asegúrate de crear esta BD antes
}


# ------------------------------
# FUNCIÓN PARA GUARDAR EN BASE DE DATOS
# ------------------------------
def guardar_en_bd(data):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = (
            "INSERT INTO Clientes "
            "(NOMBRE, CORREO, NUMERO, SEMESTRE, LINEA_CREDITO, ESTADO_CREDITO, LINK, CUOTAS_PENDIENTES, FECHA_REGISTRO) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())"
        )
        valores = (
            data.get("NOMBRE"),
            data.get("CORREO"),
            data.get("PHONE_NUMBER"),
            int(data.get("SEMESTRE")) if data.get("SEMESTRE") is not None else None,
            data.get("LINEA_CREDITO"),
            data.get("ESTADO_CREDITO"),
            data.get("LINK"),
            data.get("CUOTAS_PENDIENTES")
        )

        cursor.execute(query, valores)
        conn.commit()
        cursor.close()
        conn.close()

        logging.info("Datos insertados en la base de datos correctamente")

    except Exception as e:
        logging.error(f"Error al guardar en BD: {e}")

# -----------------------------
# Configuración Twilio (SMS)
# -----------------------------
# TWILIO_SID = os.getenv("TWILIO_SID")
# TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
# TWILIO_NUMERO = 'whatsapp:+14155238886' #  Número de Twilio comprado

# client = Client(TWILIO_SID, TWILIO_TOKEN)

# Ruta para recibir el webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        
        data = request.get_json()
        print(f"Datos recibidos: {data}")
        
        input_variables = data.get('input_variables', {})
        
        print(f"Variables de entrada: {input_variables}")
        # Guardar en base de datos usando los datos de input_variables
        guardar_en_bd(input_variables)
        
        # Extraer variables de entrada
        semestre = input_variables.get('SEMESTRE')
        linea_credito = input_variables.get('LINEA_CREDITO')
        estado_credito = input_variables.get('ESTADO_CREDITO')
        phone_number = input_variables.get('PHONE_NUMBER')
        correo = input_variables.get('CORREO')
        link = input_variables.get('LINK')
        nombre = input_variables.get('NOMBRE')
        cuotas_pendientes = input_variables.get('CUOTAS_PENDIENTES')
        
        logging.info(f"Datos de entrada: {input_variables}")
        logging.info(f"phone_number: {phone_number}")
        logging.info(f"correo: {correo}")
        logging.info(f"link: {link}")
        logging.info(f"nombre: {nombre}")
        

        
        
        # Extraer variables de salida recibidas correctamente
        extracted = data.get('extracted_variables', {})
        estado = extracted.get("estado")
        resumen = extracted.get("resumen")
        mensaje = extracted.get("mensaje")
        interes_renovar = extracted.get("interes_renovar")
        comentario_libre = extracted.get("comentario_libre")
        link_enviado_sms = extracted.get("link_enviado_sms")
        contesto_llamada = extracted.get("contesto_llamada")
        #correo que proporciono el cliente
        correo_cliente = extracted.get("correo_cliente")
        #calidad_llamada = extracted.get("calidad_llamada")

        # Mostrar en consola con logger
        logging.info(f"Webhook recibido:")
        logging.info(f"  Estado: {estado}")
        logging.info(f"  Resumen: {resumen}")
        logging.info(f"  Mensaje: {mensaje}")
        logging.info(f"  Interés en renovar: {interes_renovar}")
        logging.info(f"  Comentario libre: {comentario_libre}")
        logging.info(f"  Link enviado por SMS: {link_enviado_sms}")
        logging.info(f"  Contesto la llamada: {contesto_llamada}")
        logging.info(f"  Correo proporcionado por el cliente: {correo_cliente}")
        
        link_whatsapp = "https://wa.me/573182856386"
        
        # Si no llega mensaje, armamos uno por defecto
        if not mensaje:
            mensaje = f"""
            Hola {nombre}!,

            Hace unos momentos te contactamos, por ello si deseas seguir con el proceso te invitamos que inicies tu proceso a través de este link:
            {link}
            EL anterior Link es la interfaz para que Puedas gestionar los valores de tu credito.

            Saludos que tengas un excelente día,
            ISA tu asistente virtual de One Two Credit! 
            """


        # --- Condicional para envío de correo ---
        # Validaciones para envío de correo
        enviar_correo = True
        # Si interes_renovar contiene 'No' o está vacío, no se envía correo
        if interes_renovar is not None and (str(interes_renovar).strip().lower() == "no" or str(interes_renovar).strip() == ""):
            enviar_correo = False
        # Si contesto_llamada es False y estado es False, no se envía correo
        if contesto_llamada is False and estado is False:
            enviar_correo = False

        if enviar_correo:
            destinatario = correo if correo else correo_cliente  # Si no hay correo, usa uno por defecto
            asunto = "Renueva tu credito educativo con One2credit"

            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = destinatario
            msg["Subject"] = asunto

            cuerpo = f"""
            
            Hola {nombre}!,

            Hace unos segundos te contactamos de One2credit para renovar tu crédito educativo.  Para que sigas con el proceso, te invitamos a que le des click a este link:

            {link}

            Desde aquí podrás tener acceso a nuestra plataforma para renovar tu crédito.  Recuerda que si tuviste un buen comportamiento de pago, tu aprobación será automática !
            
            este es nuestro canal comercial de whatsapp para que puedas contactarnos:
            {link_whatsapp}

            Que tengas un excelente día.


            ISA, tu asistente virtual de One2credit!

            """

            msg.attach(MIMEText(cuerpo, "plain"))

            # Usar SMTP_SSL si el puerto es 465 (GoDaddy)
            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(msg)
            logging.info("Correo enviado correctamente ✅")
        else:
            logging.info("No se envió correo porque estado es False y interes_renovar es 'No' o 'No responde'.")
        
        # Crear payload para enviar por correo, incluyendo variables extraídas de input_variables
        payload = {
            "enviado a": nombre,
            "correo": correo,
            "link de renovacion": link,
            "mensaje":cuerpo 
        }
        return jsonify({"status": "success", "message": "Correo enviado correctamente", "payload": payload}), 200
        
        
                # -----------------------------
        # Enviar SMS (ejemplo: a un cliente con prefijo +57)
        # -----------------------------
        # Datos del mensaje
        # to_number = '+573008021679'
        # messaging_service_sid = 'MGa5d9e4149f92f18bd26ae9636a37779e'
        # body = 'Hola somos de ONE TWO CREDIT ahce un momento te lalmamos para seguir el proceso de tu renovacion, para continuar entra aqui: https://wa.me/573182856386'

        # # Enviar el mensaje
        # message = client.messages.create(
        # to=to_number,
        # messaging_service_sid=messaging_service_sid,
        # body=body)

        # print(f"Mensaje enviado correctamente. SID: {message.sid}")

        # logging.info(f"SMS enviado correctamente  SID: {mensaje.sid}")
        

        # return jsonify({"status": "success", "payload": payload}), 200

    except Exception as e:
        logging.error(f"Error en webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)

