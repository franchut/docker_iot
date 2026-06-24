from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import os, logging, ssl
import paho.mqtt.publish as publish
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
import json
import threading
import paho.mqtt.client as mqtt

logging.basicConfig(format='%(asctime)s - CRUD - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config["MYSQL_USER"] = os.environ["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = os.environ["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = os.environ["MYSQL_DB"]
app.config["MYSQL_HOST"] = os.environ["MYSQL_HOST"]
app.config['PERMANENT_SESSION_LIFETIME']=180
mysql = MySQL(app)

MQTT_BROKER = os.environ["SERVIDOR"]
MQTT_PORT = int(os.environ["PUERTO_MQTTS"])

MQTT_AUTH = {
    "username": os.environ["MQTT_USR"],
    "password": os.environ["MQTT_PASS"]
}

MQTT_TLS = {
    "ca_certs": None,
    "cert_reqs": ssl.CERT_REQUIRED,
    "tls_version": ssl.PROTOCOL_TLS_CLIENT,
    "ciphers": None
}

def on_connect(client, userdata, flags, rc, properties=None):

    logging.info("MQTT conectado")

    client.subscribe(f"{os.environ['ID_PICO']}/estado")


def on_message(client, userdata, msg):

    logging.info(f"TOPICO: {msg.topic}")
    logging.info(f"MENSAJE: {msg.payload.decode()}")

    try:

        datos = json.loads(msg.payload.decode())

        with app.app_context():

            cur = mysql.connection.cursor()

            cur.execute(
                """
                UPDATE estado_iot.estado_pico
                SET
                    temperatura=%s,
                    humedad=%s,
                    setpoint=%s,
                    periodo=%s,
                    modo=%s,
                    rele=%s
                WHERE id=1
                """,
                (
                    datos["temperatura"],
                    datos["humedad"],
                    datos["setpoint"],
                    datos["periodo"],
                    datos["modo"],
                    datos["rele"]
                )
            )

            mysql.connection.commit()

            cur.close()

        logging.info("Estado actualizado")

    except Exception as e:

        logging.error(f"Error MQTT: {e}")

# rutas

def iniciar_mqtt():

    client = mqtt.Client()

    client.username_pw_set(
        os.environ["MQTT_USR"],
        os.environ["MQTT_PASS"]
    )

    client.tls_set()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(
        os.environ["SERVIDOR"],
        int(os.environ["PUERTO_MQTTS"])
    )

    client.loop_forever()

mqtt_thread = threading.Thread(
    target=iniciar_mqtt,
    daemon=True
)

mqtt_thread.start()

logging.info("Hilo MQTT iniciado")

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    """Registrar usuario"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("usuario"):
            return "el campo usuario es oblicatorio"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "el campo contraseña es oblicatorio"

        passhash=generate_password_hash(request.form.get("password"), method='scrypt', salt_length=16)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (usuario, hash) VALUES (%s,%s)", (request.form.get("usuario"), passhash[17:]))
        if mysql.connection.affected_rows():
            flash('Se agregó un usuario')  # usa sesión
            logging.info("se agregó un usuario")
        mysql.connection.commit()
        return redirect(url_for('index'))

    return render_template('registrar.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("usuario"):
            return "el campo usuario es oblicatorio"
        # Ensure password was submitted
        elif not request.form.get("password"):
            return "el campo contraseña es oblicatorio"

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario LIKE %s", (request.form.get("usuario"),))
        rows=cur.fetchone()
        if(rows):
            if (check_password_hash('scrypt:32768:8:1$' + rows[2],request.form.get("password"))):
                session.permanent = True
                session["user_id"]=request.form.get("usuario")
                logging.info("se autenticó correctamente")
                return redirect(url_for('index'))
            else:
                flash('usuario o contraseña incorrecto')
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/')
@require_login
def index():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            temperatura,
            humedad,
            setpoint,
            periodo,
            modo,
            rele
        FROM estado_iot.estado_pico
        WHERE id = 1
    """)

    estado = cur.fetchone()

    cur.close()

    return render_template(
        'index.html',
        estado=estado
    )

@app.route('/add_contact', methods=['POST'])
@require_login
def add_contact():
    if request.method == 'POST':
        nombre = request.form['nombre']
        tel = request.form['tel']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO contactos (nombre, tel, email) VALUES (%s,%s,%s)"
                    , (nombre, tel, email))
        if mysql.connection.affected_rows():
            flash('Se agregó un contacto')  # usa sesión
            logging.info("se agregó un contacto")
            mysql.connection.commit()
    return redirect(url_for('index'))

@app.route('/borrar/<string:id>', methods = ['GET'])
@require_login
def borrar_contacto(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM contactos WHERE id = %s', (id,))
    if mysql.connection.affected_rows():
        flash('Se eliminó un contacto')  # usa sesión
        logging.info("se eliminó un contacto")
        mysql.connection.commit()
    return redirect(url_for('index'))

@app.route('/editar/<id>', methods = ['GET'])
@require_login
def conseguir_contacto(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM contactos WHERE id = %s', (id,))
    datos = cur.fetchone()
    logging.info(datos)
    return render_template('editar-contacto.html', contacto = datos)

@app.route('/actualizar/<id>', methods=['POST'])
@require_login
def actualizar_contacto(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        tel = request.form['tel']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE contactos SET nombre=%s, tel=%s, email=%s WHERE id=%s", (nombre, tel, email, id))
    if mysql.connection.affected_rows():
        flash('Se actualizó un contacto')  # usa sesión
        logging.info("se actualizó un contacto")
        mysql.connection.commit()
    return redirect(url_for('index'))

@app.route("/logout")
@require_login
def logout():
    session.clear()
    logging.info("el usuario {} cerró su sesión".format(session.get("user_id")))
    return redirect(url_for('index'))

@app.route("/tema/<modo>")
@require_login
def cambiar_tema(modo):
    if modo in ["light", "dark"]:
        session["tema"] = modo

    return redirect(request.referrer or url_for("index"))

@app.route('/destello')
@require_login
def destello():

    publish.single(
        topic=f"{os.environ['ID_PICO']}/destello",
        payload="1",
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        auth=MQTT_AUTH,
        tls=MQTT_TLS,
        qos=1
    )

    return redirect(url_for('index'))

@app.route('/rele/on')
@require_login
def rele_on():

    publish.single(
        topic=f"{os.environ['ID_PICO']}/rele",
        payload="1",
        hostname=MQTT_BROKER,
        port=int(os.environ["PUERTO_MQTTS"]),
        auth=MQTT_AUTH,
        tls=MQTT_TLS
    )

    flash("Relé activado")

    return redirect(url_for('index'))

@app.route('/rele/off')
@require_login
def rele_off():

    publish.single(
        topic=f"{os.environ['ID_PICO']}/rele",
        payload="0",
        hostname=MQTT_BROKER,
        port=int(os.environ["PUERTO_MQTTS"]),
        auth=MQTT_AUTH,
        tls=MQTT_TLS
    )

    flash("Relé desactivado")

    return redirect(url_for('index'))

@app.route('/periodo', methods=['POST'])
@require_login
def periodo():

    valor = request.form["periodo"]

    publish.single(
        topic=f"{os.environ['ID_PICO']}/periodo",
        payload=valor,
        hostname=MQTT_BROKER,
        port=int(os.environ["PUERTO_MQTTS"]),
        auth=MQTT_AUTH,
        tls=MQTT_TLS
    )

    return redirect(url_for('index'))

@app.route('/setpoint', methods=['POST'])
@require_login
def setpoint():

    valor = request.form["setpoint"]

    publish.single(
        topic=f"{os.environ['ID_PICO']}/setpoint",
        payload=valor,
        hostname=MQTT_BROKER,
        port=int(os.environ["PUERTO_MQTTS"]),
        auth=MQTT_AUTH,
        tls=MQTT_TLS
    )

    return redirect(url_for('index'))

@app.route('/modo/auto')
@require_login
def modo_auto():

    publish.single(
        topic=f"{os.environ['ID_PICO']}/modo",
        payload="auto",
        hostname=MQTT_BROKER,
        port=int(os.environ["PUERTO_MQTTS"]),
        auth=MQTT_AUTH,
        tls=MQTT_TLS
    )

    flash("Modo automático")

    return redirect(url_for('index'))

@app.route('/modo/manual')
@require_login
def modo_manual():

    publish.single(
        topic=f"{os.environ['ID_PICO']}/modo",
        payload="manual",
        hostname=MQTT_BROKER,
        port=int(os.environ["PUERTO_MQTTS"]),
        auth=MQTT_AUTH,
        tls=MQTT_TLS
    )

    flash("Modo manual")

    return redirect(url_for('index'))
