from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale
import matplotlib.pyplot as plt
from io import BytesIO
import re
import ssl
import aiomqtt

class ClienteMqtt:

    def __init__(self):

        self.clientemqtt = None

    async def publicar(self, topico, mensaje):

        logging.info(f"Publicando en {topico}")

        await self.clientemqtt.publish(
            topico,
            mensaje,
            qos=1
        )

        logging.info(f"Publicado en {topico}: {mensaje}")

token=os.environ["TB_TOKEN"]

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

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
    kb = [["Temperatura"],["Humedad"],["Modo automatico"],["Modo manual"],["Activar Rele"],["Desactivar rele"],["Destello"]]
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

    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    async with aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context
    ) as client:

        await client.publish(
            "iot/temperatura",
            "consulta",
            qos=1
        )

    await context.bot.send_message(
        update.message.chat.id,
        text="Consulta MQTT enviada"
    )

async def humedad(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Funciona")

async def automatico(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Funciona")

async def manual(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Funciona")

async def activar_rele(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Funciona")

async def desactivar_rele(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Funciona")

async def destello(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Funciona")


def main():

    application = (
        Application.builder()
        .token(token)
        .build()
    )

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
    application.run_polling()

if __name__ == '__main__':
    main()
