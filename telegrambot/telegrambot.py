from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale
import matplotlib.pyplot as plt
from io import BytesIO
import re

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
    await context.bot.send_message(update.message.chat.id, text="Funciona")

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

async def graficos(update: Update, context):
    logging.info(update.message.text)
    sql = f"""SELECT timestamp, {update.message.text.split()[1]}
            FROM (
                SELECT timestamp, {update.message.text.split()[1]},
                    ROW_NUMBER() OVER (ORDER BY id) AS rn
                FROM mediciones
                WHERE timestamp >= NOW() - INTERVAL 1 DAY
                AND sensor_id LIKE 'sensor_1'
            ) AS t
            WHERE rn % 2 = 0
            ORDER BY timestamp;"""
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        filas = await cur.fetchall()

        fig, ax = plt.subplots(figsize=(7, 4))
        fecha,var=zip(*filas)
        ax.plot(fecha,var)
        ax.grid(True, which='both')
        ax.set_title(update.message.text, fontsize=14, verticalalignment='bottom')
        ax.set_xlabel('fecha')
        ax.set_ylabel('unidad')

        buffer = BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)
        buffer.close()
    conn.close()

def main():
    application = Application.builder().token(token).build()
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
    application.add_handler(MessageHandler(filters.Regex(re.compile("^(gráfico temperatura|gráfico humedad)$",re.IGNORECASE)), graficos))
    application.run_polling()

if __name__ == '__main__':
    main()
