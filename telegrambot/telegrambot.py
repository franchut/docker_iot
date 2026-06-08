from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.ext import ConversationHandler
import logging, os, asyncio, aiomysql, traceback, locale
import matplotlib.pyplot as plt
from io import BytesIO
import re
import ssl
import aiomqtt
import json

class ClienteMqtt:

    def __init__(self):

        self.clientemqtt = None
        self.ultimo_estado = {}

    async def publicar(self, topico, mensaje):

        logging.info(f"Publicando en {topico}")

        await self.clientemqtt.publish(
            topico,
            mensaje,
            qos=1
        )

        logging.info(f"Publicado en {topico}: {mensaje}")

SETPOINT, PERIODO = range(2)

token=os.environ["TB_TOKEN"]

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

ID_PICO = os.environ["ID_PICO"]

async def conectar_mqtt():

    logging.info(f"Loop MQTT: {id(asyncio.get_running_loop())}")

    try:

        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        tls_context.verify_mode = ssl.CERT_REQUIRED
        tls_context.check_hostname = True
        tls_context.load_default_certs()

        client = aiomqtt.Client(
            os.environ["SERVIDOR"],
            username=os.environ["MQTT_USR"],
            password=os.environ["MQTT_PASS"],
            port=int(os.environ["PUERTO_MQTTS"]),
            tls_context=tls_context
        )

        logging.info("Antes de __aenter__")

        await client.__aenter__()

        logging.info("Después de __aenter__")

        return client

    except Exception as e:

        logging.exception(e)
        raise

async def escuchar_mqtt(conexion):

    logging.info("escuchar_mqtt iniciada")

    async for mensaje in conexion.clientemqtt.messages:

        payload = mensaje.payload.decode()

        logging.info(f"MQTT recibido: {payload}")

        conexion.ultimo_estado = json.loads(payload)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    kb = [["Setpoint"],["Periodo"],["Temperatura"],["Humedad"],["Modo automatico"],["Modo manual"],["Activar Rele"],["Desactivar rele"],["Destello"]]
    await context.bot.send_message(update.message.chat.id, text="Bienvenido al Bot "+ nombre + " " + apellido,reply_markup=ReplyKeyboardMarkup(kb))

async def about(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado para el curso de IoT FIO")

async def kill(update: Update, context):
    logging.info(context.args)
    if context.args and context.args[0] == '@e':
        await context.bot.send_animation(update.message.chat.id, "CgACAgEAAxkBAAICI2oYKdAqh4YkBCLifiVJZlRXy74-AAKUBwACZ_PBRLgV_qZf-9kGOwQ")
        await asyncio.sleep(6)
        await context.bot.send_message(update.message.chat.id, text="¡¡¡Ahora estan todos muertos!!!")
    else:
        await context.bot.send_message(update.message.chat.id, text="☠️ ¡¡¡Esto es muy peligroso!!! ☠️")

async def temperatura(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    temp = mqtt.ultimo_estado.get(
        "temperatura",
        "Sin datos"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text=f"Temperatura: {temp} °C"
    )

async def humedad(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    humedad = mqtt.ultimo_estado.get(
        "humedad",
        "Sin datos"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text=f"Humedad: {humedad} %"
    )

async def automatico(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    await mqtt.publicar(
        f"{ID_PICO}/modo",
        "auto"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text="Modo automático activado"
    )

async def manual(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    await mqtt.publicar(
        f"{ID_PICO}/modo",
        "manual"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text="Modo manual activado"
    )

async def activar_rele(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    await mqtt.publicar(
        f"{ID_PICO}/rele",
        "1"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text="Relé activado"
    )

async def desactivar_rele(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    await mqtt.publicar(
        f"{ID_PICO}/rele",
        "0"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text="Relé desactivado"
    )

async def destello(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    await mqtt.publicar(
        f"{ID_PICO}/destello",
        "1"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text="Destello enviado"
    )

async def estado(update: Update, context):

    mqtt = context.application.bot_data["mqtt"]

    datos = mqtt.ultimo_estado

    mensaje = (
        f"Temperatura: {datos.get('temperatura', '-') } °C\n"
        f"Humedad: {datos.get('humedad', '-') } %\n"
        f"Modo: {datos.get('modo', '-') }\n"
        f"Relé: {datos.get('rele', '-') }\n"
        f"Setpoint: {datos.get('setpoint', '-') }\n"
        f"Periodo: {datos.get('periodo', '-') } s"
    )

    await context.bot.send_message(
        update.message.chat.id,
        text=mensaje
    )

async def pedir_setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        update.message.chat.id,
        text="Ingrese el nuevo setpoint:"
    )

    return SETPOINT

async def recibir_setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mqtt = context.application.bot_data["mqtt"]

    try:

        valor = float(update.message.text)

        await mqtt.publicar(
            f"{ID_PICO}/setpoint",
            str(valor)
        )

        await context.bot.send_message(
            update.message.chat.id,
            text=f"Setpoint actualizado a {valor}"
        )

    except ValueError:

        await context.bot.send_message(
            update.message.chat.id,
            text="Ingrese un número válido"
        )

        return SETPOINT

    return ConversationHandler.END

async def pedir_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        update.message.chat.id,
        text="Ingrese el nuevo periodo en segundos:"
    )

    return PERIODO

async def recibir_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mqtt = context.application.bot_data["mqtt"]

    try:

        valor = int(update.message.text)

        await mqtt.publicar(
            f"{ID_PICO}/periodo",
            str(valor)
        )

        await context.bot.send_message(
            update.message.chat.id,
            text=f"Periodo actualizado a {valor} segundos"
        )

    except ValueError:

        await context.bot.send_message(
            update.message.chat.id,
            text="Ingrese un número entero válido"
        )

        return PERIODO

    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        update.message.chat.id,
        text="Operación cancelada"
    )

    return ConversationHandler.END



async def post_init(application):

    conexion = ClienteMqtt()

    conexion.clientemqtt = await conectar_mqtt()

    application.bot_data["mqtt"] = conexion

    await conexion.clientemqtt.subscribe(
        "e663a837cb6d5435",
        qos=1
    )

    logging.info("Suscripto al tópico de la Pico")

    asyncio.create_task(
        escuchar_mqtt(conexion)
    )

def main():

    application = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    setpoint_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(
                re.compile("^(setpoint)$", re.IGNORECASE)
            ),
            pedir_setpoint
        )
    ],
    states={
        SETPOINT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                recibir_setpoint
            )
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancelar)
    ]
    )

    periodo_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(
                re.compile("^(periodo)$", re.IGNORECASE)
            ),
            pedir_periodo
        )
    ],
    states={
        PERIODO: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                recibir_periodo
            )
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancelar)
    ]
    )

    application.add_handler(setpoint_handler)
    application.add_handler(periodo_handler)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('about', about))
    application.add_handler(CommandHandler('kill', kill))
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(temperatura)$",re.IGNORECASE)), temperatura))
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(humedad)$",re.IGNORECASE)), humedad))
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(modo automatico)$",re.IGNORECASE)), automatico))
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(modo manual)$",re.IGNORECASE)), manual))
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(activar rele)$",re.IGNORECASE)), activar_rele))
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(desactivar rele)$",re.IGNORECASE)), desactivar_rele))
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(destello)$",re.IGNORECASE)), destello))
    application.add_handler(CommandHandler('estado', estado))
    application.run_polling()

if __name__ == '__main__':
    main()
