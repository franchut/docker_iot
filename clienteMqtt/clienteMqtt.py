import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(
    format='%(asctime)s - %(taskName)s - %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%d/%m/%Y %H:%M:%S %z'
)

class Estado():

    def __init__(self):

        self.valor = 0

async def recibir_mensajes_top1(mensaje):

    logging.info(f"{os.environ['TOPICO1']} : {mensaje}")

async def recibir_mensajes_top2(mensaje):

    logging.info(f"{os.environ['TOPICO2']} : {mensaje}")

async def consumir_mensajes(client):

    async for mensaje in client.messages:

        topico = str(mensaje.topic)
        carga = mensaje.payload.decode()

        if topico == os.environ['TOPICO1']:

            asyncio.create_task(recibir_mensajes_top1(carga), name="Consumidor Mensajes 1")

        elif topico == os.environ['TOPICO2']:

            asyncio.create_task(recibir_mensajes_top2(carga), name="Consumidor Mensajes 2")

async def contador(n):

    while True:

        n.valor += 1
        await asyncio.sleep(3)

async def publicar_contador(client, n):

    while True:

        try:

            await client.publish(os.environ["TOPICO3"],
                            str(n.valor), 
                            qos=aiomqtt.QoS.AT_LEAST_ONCE)

            await asyncio.sleep(5)

        except Exception as e:

            logging.error(e)


async def main():

    try:

        cont = Estado()
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        tls_context.verify_mode = ssl.CERT_REQUIRED
        tls_context.check_hostname = True
        tls_context.load_default_certs()

        async with aiomqtt.Client(

            os.environ['SERVIDOR'],
            port=8883,
            tls_context=tls_context,
        ) as client:

            await client.subscribe(os.environ['TOPICO1'])
            await client.subscribe(os.environ['TOPICO2'])
            tarea1 = asyncio.create_task(contador(cont), name="contador")
            tarea2 = asyncio.create_task(publicar_contador(client, cont), name="publicador")
            tarea3 = asyncio.create_task(consumir_mensajes(client), name="consumidor")

            await asyncio.gather(tarea1, tarea2, tarea3)

    except KeyboardInterrupt:

        print("Programa finalizado")

if __name__ == "__main__":

    asyncio.run(main())
