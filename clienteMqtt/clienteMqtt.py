import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(format='%(asctime)s - cliente mqtt - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

class Estado():
    def __init__(self,valor):
        self.valor = 0

async def contador(client,n):

    while True:
        n.valor += 1
        await asyncio.sleep(3)

async def publicar_contador(client, n):

    while True:
        try:
            await client.publish(os.environ["TOPICO1"],
                            n.valor, 
                            qos=aiomqtt.QoS.AT_LEAST_ONCE)
            await asyncio.sleep(5)
        except:
            pass


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
            asyncio.create_task(contador(client,cont.value), name="contador")
            asyncio.create_task(publicar_contador(client, cont), name="publicar contador")
            
    except KeyboardInterrupt:
        print("Programa finalizado")

if __name__ == "__main__":
    asyncio.run(main())
