import ssl
import logging
import os

import aiomqtt


logging.basicConfig(
    format='%(asctime)s - cliente mqtt - %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%d/%m/%Y %H:%M:%S %z'
)


class ClienteMqtt:

    def __init__(self):

        self.client = None

async def conectar(self):

    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    self.client = aiomqtt.Client(
        os.environ["SERVIDOR"],
        username=os.environ["MQTT_USR"],
        password=os.environ["MQTT_PASS"],
        port=int(os.environ["PUERTO_MQTTS"]),
        tls_context=tls_context
    )

    await self.client.__aenter__()

    logging.info("Conectado al broker MQTT")

async def publicar(self, topico, mensaje):

    await self.client.publish(
        topico,
        mensaje,
        qos=1
    )

    logging.info(
        f"Publicado en {topico}: {mensaje}"
    )

async def main():

    mqtt = ClienteMqtt()

    await mqtt.conectar()

    await mqtt.publicar(
        "iot/temperatura",
        "consulta"
    )

if __name__ == "__main__":
    asyncio.run(main())