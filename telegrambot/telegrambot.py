from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale
import matplotlib.pyplot as plt
from io import BytesIO
import re
import ssl
import aiomqtt
from clienteMqtt import ClienteMqtt

class ClienteMqtt:
    def __init__(self):
        self.clientemqtt = None

token=os.environ["TB_TOKEN"]

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

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

    mqtt = context.application.bot_data["mqtt"]

    await mqtt.publicar(
        "iot/temperatura",
        "consulta"
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
    conexion = ClienteMqtt()
    conexion.clientemqtt = asyncio.run(conectar_mqtt())
    application = Application.builder().token(token).build()
    application.bot_data["mqtt"] = conexion
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
