from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, send_from_directory, send_file
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
import os
import requests
from datetime import datetime
import pdfkit
from weasyprint import HTML, CSS
import json
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')

# Configuración de la sesión
app.config["SECRET_KEY"] = 'una_clave_secreta_muy_segura'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///problemas.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# Asegúrate de que el directorio de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Cargar datos de unidades médicas desde el archivo JSON
def cargar_unidades_medicas():
    try:
        with open(os.path.join(app.static_folder, 'data/unidades_medicas.json'), 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error al cargar unidades médicas: {e}")
        return []

unidades_medicas_data = cargar_unidades_medicas()

# Configuración de pdfkit
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Cambia esto a la ruta donde está instalado wkhtmltopdf
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# Modelo Problema
class Problema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(100), nullable=False)
    unidad_medica = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    subcategoria = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.String(300), nullable=False)
    nivel_riesgo = db.Column(db.String(50), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    ticket_id = db.Column(db.String(10), unique=True, nullable=False)
    reportado_por_operativo = db.Column(db.Boolean, default=False)
    actualizaciones = db.Column(db.Text, nullable=True)
    estado_problema = db.Column(db.String(50), default='Pendiente')
    fecha_hora = db.Column(db.String(50), nullable=False, default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    aceptado = db.Column(db.String(50), default='Pendiente')
    nombre_reportante = db.Column(db.String(100), nullable=False, default='Desconocido')
    responsable_problema = db.Column(db.String(100), nullable=False, default='Desconocido')
    correo_electronico = db.Column(db.String(100), nullable=False, default='no_disponible@example.com')
    archivo = db.Column(db.String(300), nullable=True)  # Campo para el nombre del archivo subido
    origen = db.Column(db.String(50))  # nuevo campo

    def to_dict(self):
        return {
            'id': self.id,
            'estado': self.estado,
            'unidad_medica': self.unidad_medica,
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'descripcion': self.descripcion,
            'nivel_riesgo': self.nivel_riesgo,
            'lat': self.lat,
            'lon': self.lon,
            'ticket_id': self.ticket_id,
            'reportado_por_operativo': self.reportado_por_operativo,
            'actualizaciones': self.actualizaciones,
            'estado_problema': self.estado_problema,
            'fecha_hora': self.fecha_hora,
            'aceptado': self.aceptado,
            'nombre_reportante': self.nombre_reportante,
            'responsable_problema': self.responsable_problema,
            'correo_electronico': self.correo_electronico,
            'archivo': self.archivo,
            'origen': self.origen,
        }

def normalizar_estado(estado):
    estado = estado.strip()
    estado = " ".join(estado.split())
    estado = estado.upper()
    partes = estado.split()
    if partes[0] == "CDMX" and len(partes) > 2:
        return "CDMX " + " ".join(p.capitalize() for p in partes[1:])
    return " ".join(p.capitalize() for p in partes)

@app.before_request
def before_request():
    if not hasattr(app, 'first_request_done'):
        db.create_all()
        app.first_request_done = True

# Roles y estados asignados a los usuarios
user_roles = {
    'aguascalientes': {'role': 'operativo', 'state': 'Aguascalientes', 'password': 'pass123'},
    'bajacalifornia': {'role': 'operativo', 'state': 'Baja California', 'password': 'pass123'},
    'bajacaliforniasur': {'role': 'operativo', 'state': 'Baja California Sur', 'password': 'pass123'},
    'campeche': {'role': 'operativo', 'state': 'Campeche', 'password': 'pass123'},
    'chiapas': {'role': 'operativo', 'state': 'Chiapas', 'password': 'pass123'},
    'chihuahua': {'role': 'operativo', 'state': 'Chihuahua', 'password': 'pass123'},
    'cdmxn': {'role': 'operativo', 'state': 'CDMX Zona Norte', 'password': 'pass123'},
    'cdmxp': {'role': 'operativo', 'state': 'CDMX Zona Poniente', 'password': 'pass123'},
    'cdmxo': {'role': 'operativo', 'state': 'CDMX Zona Oriente', 'password': 'pass123'},
    'cdmxs': {'role': 'operativo', 'state': 'CDMX Zona Sur', 'password': 'pass123'},
    'coahuila': {'role': 'operativo', 'state': 'Coahuila', 'password': 'pass123'},
    'colima': {'role': 'operativo', 'state': 'Colima', 'password': 'pass123'},
    'durango': {'role': 'operativo', 'state': 'Durango', 'password': 'pass123'},
    'edomex': {'role': 'operativo', 'state': 'Estado de México', 'password': 'pass123'},
    'guanajuato': {'role': 'operativo', 'state': 'Guanajuato', 'password': 'pass123'},
    'guerrero': {'role': 'operativo', 'state': 'Guerrero', 'password': 'pass123'},
    'hidalgo': {'role': 'operativo', 'state': 'Hidalgo', 'password': 'pass123'},
    'jalisco': {'role': 'operativo', 'state': 'Jalisco', 'password': 'pass123'},
    'michoacan': {'role': 'operativo', 'state': 'Michoacán', 'password': 'pass123'},
    'morelos': {'role': 'operativo', 'state': 'Morelos', 'password': 'pass123'},
    'nayarit': {'role': 'operativo', 'state': 'Nayarit', 'password': 'pass123'},
    'nuevoleon': {'role': 'operativo', 'state': 'Nuevo León', 'password': 'pass123'},
    'oaxaca': {'role': 'operativo', 'state': 'Oaxaca', 'password': 'pass123'},
    'puebla': {'role': 'operativo', 'state': 'Puebla', 'password': 'pass123'},
    'queretaro': {'role': 'operativo', 'state': 'Querétaro', 'password': 'pass123'},
    'quintanaroo': {'role': 'operativo', 'state': 'Quintana Roo', 'password': 'pass123'},
    'sanluispotosi': {'role': 'operativo', 'state': 'San Luis Potosí', 'password': 'pass123'},
    'sinaloa': {'role': 'operativo', 'state': 'Sinaloa', 'password': 'pass123'},
    'sonora': {'role': 'operativo', 'state': 'Sonora', 'password': 'pass123'},
    'tabasco': {'role': 'operativo', 'state': 'Tabasco', 'password': 'pass123'},
    'tamaulipas': {'role': 'operativo', 'state': 'Tamaulipas', 'password': 'pass123'},
    'tlaxcala': {'role': 'operativo', 'state': 'Tlaxcala', 'password': 'pass123'},
    'veracruz': {'role': 'operativo', 'state': 'Veracruz', 'password': 'pass123'},
    'yucatan': {'role': 'operativo', 'state': 'Yucatán', 'password': 'pass123'},
    'zacatecas': {'role': 'operativo', 'state': 'Zacatecas', 'password': 'pass123'},
    'admin1': {'role': 'admin', 'password': 'admin123'},
    'DrCanekSerna': {'role': 'admin', 'password': 'admin123'},
    'DraEvelinGonzalez': {'role': 'admin', 'password': 'admin123'},
    'admin2': {'role': 'admin', 'password': 'admin123'},
    'admin3': {'role': 'admin', 'password': 'admin123'},
    'admin4': {'role': 'admin', 'password': 'admin123'},
    'admin5': {'role': 'admin', 'password': 'admin123'},
    'admin6': {'role': 'admin', 'password': 'admin123'},
    'admin7': {'role': 'admin', 'password': 'admin123'},
    'superadmin': {'role': 'superadmin', 'password': 'superadmin123'}  # Superadmin
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_info = user_roles.get(username)
        
        # Imprime las credenciales recibidas y las esperadas
        print(f"Received username: {username}")
        print(f"Received password: {password}")
        if user_info:
            print(f"Expected password: {user_info['password']}")

        if user_info and user_info['password'] == password:
            session['username'] = username
            session['role'] = user_info['role']
            session['state'] = user_info.get('state')
            
            if user_info['role'] == 'operativo':
                session['welcome_message'] = f'Bienvenido(a) {username}, Operativo de {session["state"]}'
            elif user_info['role'] == 'admin':
                session['welcome_message'] = f'Bienvenido(a) {username}, Administrador'
            elif user_info['role'] == 'superadmin':
                session['welcome_message'] = f'Bienvenido(a) {username}, Superadministrador'
            
            return redirect(url_for('bienvenida'))
        else:
            return "Credenciales incorrectas", 401
    
    # Si el método es GET, renderiza el formulario de login
    return render_template('login.html')

@app.route('/bienvenida')
def bienvenida():
    if 'username' in session:
        return render_template('bienvenida.html', welcome_message=session['welcome_message'], username=session['username'])
    else:
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    welcome_message = session.pop('welcome_message', None)
    username = session['username']  # Obtener el nombre de usuario de la sesión

    user_info = user_roles.get(username)
    if user_info and user_info['role'] in ['admin', 'superadmin']:
        problemas = Problema.query.filter_by(reportado_por_operativo=True).order_by(Problema.id.desc()).all()

        estados_vistos = set()
        estados = []
        for estado in db.session.query(Problema.estado).distinct().all():
            estado_normalizado = estado[0].strip().title()
            if not estado_normalizado.startswith('Cdmx - Zona') and estado_normalizado not in estados_vistos:
                estados_vistos.add(estado_normalizado)
                estados.append(estado_normalizado)

        return render_template('dashboard_admin.html', problemas=[problema.to_dict() for problema in problemas], estados=sorted(estados), welcome_message=welcome_message, username=username)
    
    elif user_info and user_info['role'] == 'operativo':
        estado_asignado = user_info['state']
        problemas_reportados = Problema.query.filter_by(reportado_por_operativo=True, estado=estado_asignado).order_by(Problema.id.desc()).all()
        
        # Cargar el archivo JSON y obtener todas las unidades médicas para el estado asignado
        try:
            with open('static/data/unidades_medicas.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            todas_unidades_medicas = []
            for estado, unidades in data.items():
                if estado_asignado.lower() in estado.lower():
                    todas_unidades_medicas.extend(unidades)
        except FileNotFoundError:
            print("El archivo unidades_medicas.json no fue encontrado.")
            todas_unidades_medicas = []
        except json.JSONDecodeError:
            print("Error al decodificar el archivo JSON.")
            todas_unidades_medicas = []
        except UnicodeDecodeError as e:
            print(f"Error de codificación al leer el archivo JSON: {e}")
            todas_unidades_medicas = []

        return render_template('dashboard_operativo.html', problemas=[problema.to_dict() for problema in problemas_reportados], estado_asignado=estado_asignado, unidades_medicas=sorted(set(todas_unidades_medicas)), welcome_message=welcome_message, username=username)

    else:
        return 'Acceso no autorizado'

@app.route('/gestionar_usuarios')
def gestionar_usuarios():
    if 'username' not in session or session['role'] not in ['admin', 'superadmin']:
        return redirect(url_for('index'))
    
    # Fetch the list of users
    users_operativos = [{'username': user, 'state': info.get('state', ''), 'role': info['role']} for user, info in user_roles.items() if info['role'] == 'operativo']
    users_admins = [{'username': user, 'role': info['role']} for user, info in user_roles.items() if info['role'] == 'admin']
    
    return render_template('gestionar_usuarios.html', users_operativos=users_operativos, users_admins=users_admins)

@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    username = request.form['username']
    password = request.form['password']
    state = request.form.get('state', '')
    role = request.form['role']

    # Add the new user to the user_roles dictionary (this should be saved to your persistent storage)
    user_roles[username] = {'role': role, 'password': password, 'state': state}

    return redirect(url_for('gestionar_usuarios'))

@app.route('/editar_usuario', methods=['POST'])
def editar_usuario():
    username = request.form['username']
    password = request.form.get('password')
    state = request.form.get('state')
    role = request.form.get('role')

    # Update the user in the user_roles dictionary (this should be saved to your persistent storage)
    if username in user_roles:
        if password:
            user_roles[username]['password'] = password
        if state:
            user_roles[username]['state'] = state
        if role:
            user_roles[username]['role'] = role

    return redirect(url_for('gestionar_usuarios'))

@app.route('/eliminar_usuario', methods=['POST'])
def eliminar_usuario():
    username = request.form['username']

    # Remove the user from the user_roles dictionary (this should be saved to your persistent storage)
    if username in user_roles:
        del user_roles[username]

    return redirect(url_for('gestionar_usuarios'))

@app.route('/reportar_problema', methods=['POST'])
def reportar_problema():
    if 'username' not in session:
        return redirect(url_for('index'))

    try:
        estado = normalizar_estado(request.form['estado'])
        unidad_medica = request.form['unidad_medica']
        categoria_problema = request.form['categoria_problema']
        subcategoria_problema = request.form['subcategoria']
        nivel_riesgo = request.form['nivel_riesgo']
        descripcion = request.form['descripcion']
        nombre_reportante = request.form['nombre_reportante']
        responsable_problema = request.form['responsable_problema']
        correo_electronico = request.form['correo_electronico']
        fecha_hora = request.form['fecha_hora']
        archivo = request.files.get('archivo')  # Obtener archivo
    except KeyError as e:
       print(f"Error: {e}")  # Para identificar el campo que falta
       return f"Falta el campo {str(e)} en el formulario", 400
    
    if not all([estado, unidad_medica, categoria_problema, subcategoria_problema, nivel_riesgo, descripcion, nombre_reportante, responsable_problema, correo_electronico]):
        return "Todos los campos son obligatorios", 400
    
     # Manejo del archivo PDF
    if archivo and archivo.filename != '':
        filename = secure_filename(archivo.filename)
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = None

    # Geocodificación de la unidad médica
    api_key = "AIzaSyAhPtAHcRPnNIzo9-1Ab_Qxn7HFTRjPK9s"
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={unidad_medica},+{estado},+Mexico&key={api_key}"
    response = requests.get(geocode_url)
    geocode_data = response.json()

    if geocode_data['status'] == 'OK':
        lat = geocode_data['results'][0]['geometry']['location']['lat']
        lon = geocode_data['results'][0]['geometry']['location']['lng']
    else:
        lat, lon = None, None  # Manejar el caso donde la geocodificación falla

    # Generar un nuevo ticket_id único
    prefix = session['username'][:2].upper()
    last_ticket = Problema.query.filter(Problema.ticket_id.like(f"{prefix}%")).order_by(Problema.ticket_id.desc()).first()
    if last_ticket:
        last_ticket_number = int(last_ticket.ticket_id[2:])
        ticket_id = f"{prefix}{last_ticket_number + 1:05d}"
    else:
        ticket_id = f"{prefix}00001"

    problema = Problema(
        estado=estado,
        unidad_medica=unidad_medica,
        categoria=categoria_problema,
        subcategoria=subcategoria_problema,
        descripcion=descripcion,
        nivel_riesgo=nivel_riesgo,
        lat=lat if lat else 23.634501,
        lon=lon if lon else -102.552784,
        ticket_id=ticket_id,
        reportado_por_operativo=True,
        nombre_reportante=nombre_reportante,
        responsable_problema=responsable_problema,
        correo_electronico=correo_electronico,
        fecha_hora=fecha_hora,
        archivo=filename  # Almacena el nombre del archivo en la base de datos
    )
    db.session.add(problema)
    db.session.commit()

    return redirect(url_for('dashboard', mensaje='Problema reportado exitosamente'))

@app.route('/obtener_unidades_medicas', methods=['GET'])
def obtener_unidades_medicas():
    estado = request.args.get('estado')
    if estado:
        estado_normalizado = normalizar_estado(estado)
        try:
            with open('static/data/unidades_medicas.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            unidades_medicas = data.get(estado_normalizado, [])
        except FileNotFoundError:
            print("El archivo unidades_medicas.json no fue encontrado.")
            unidades_medicas = []
        except json.JSONDecodeError:
            print("Error al decodificar el archivo JSON.")
            unidades_medicas = []
        
        return jsonify(unidades_medicas)
    return jsonify([])

# Agregar un diccionario con los detalles de los empleados
empleados = {
    '12345': {'nombre': 'Juan Perez', 'puesto': 'Médico'},
    '67890': {'nombre': 'Ana Gomez', 'puesto': 'Enfermera'},
    '10123': {'nombre': 'Carlos Varela', 'puesto': 'Jefe de Mantenimiento'}
}

@app.route('/get_employee_details/<numero_empleado>', methods=['GET'])
def get_employee_details(numero_empleado):
    empleado = empleados.get(numero_empleado)
    if empleado:
        return jsonify(empleado)
    else:
        return jsonify({'error': 'Empleado no encontrado'}), 404

@app.route('/actualizar_ticket', methods=['POST'])
def actualizar_ticket():
    if 'username' not in session:
        return redirect(url_for('index'))

    ticket_id = request.form['ticket_id']
    nueva_actualizacion = request.form['nueva_actualizacion']
    fecha_hora_actualizacion = request.form['fecha_hora_actualizacion']
    numero_empleado = request.form['numero_empleado']
    nombre_empleado = request.form['nombre_empleado']
    puesto_empleado = request.form['puesto_empleado']
    archivo = request.files.get('archivo')  # Obtener archivo

    problema = Problema.query.filter_by(ticket_id=ticket_id).first()
    if problema:
        nueva_actualizacion_formateada = f"{fecha_hora_actualizacion} ({nombre_empleado} - {puesto_empleado}): {nueva_actualizacion}"
        if problema.actualizaciones:
            problema.actualizaciones = f"{problema.actualizaciones}\n{nueva_actualizacion_formateada}"
        else:
            problema.actualizaciones = nueva_actualizacion_formateada

               # Manejo del archivo PDF en la actualización
        if archivo and archivo.filename != '':
            filename = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            problema.archivo = filename

        db.session.commit()
    
    return redirect(url_for('dashboard', mensaje='Ticket actualizado exitosamente'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/subir_archivo/<ticket_id>', methods=['POST'])
def subir_archivo(ticket_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    problema = Problema.query.filter_by(ticket_id=ticket_id).first()
    if not problema:
        return "Problema no encontrado", 404

    archivo = request.files['archivo']
    if archivo and archivo.filename != '':
        filename = secure_filename(archivo.filename)
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        problema.archivo = filename
        db.session.commit()

    return redirect(url_for('dashboard', mensaje='Archivo subido exitosamente'))


@app.route('/get_problem_details/<ticket_id>', methods=['GET'])
def get_problem_details(ticket_id):
    problema = Problema.query.filter_by(ticket_id=ticket_id).first()
    if problema:
        return jsonify(problema.to_dict())
    else:
        return jsonify({"error": "Problema no encontrado"}), 404

@app.route('/filtrar_datos_ajax', methods=['POST'])
def filtrar_datos_ajax():
    estado = normalizar_estado(request.form.get('estado'))
    query = Problema.query.filter_by(reportado_por_operativo=True)

    if estado:
        query = query.filter_by(estado=estado)
    
    resultados = [problema.to_dict() for problema in query.all()]

    return jsonify({'datos': resultados})

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('state', None)
    session.pop('welcome_message', None)
    return redirect(url_for('index'))

@app.route('/mapas')
def mapas():
    return render_template('mapas.html')

@app.route('/api/estadisticas', methods=['GET', 'POST'])
def get_estadisticas():
    try:
        estados_relevantes = ['Solucionado', 'No Solucionado', 'En Proceso', 'Sin Categorizar']
        query = Problema.query.filter(Problema.estado_problema.in_(estados_relevantes))

        if request.method == 'POST':
            filtros = request.json
            if 'estado' in filtros:
                query = query.filter(Problema.estado_problema == filtros['estado'])
            if 'categoria' in filtros:
                query = query.filter(Problema.categoria == filtros['categoria'])
            if 'fecha_inicio' in filtros and 'fecha_fin' in filtros:
                query = query.filter(Problema.fecha_hora.between(filtros['fecha_inicio'], filtros['fecha_fin']))
        
        problemas = query.all()

        problemas_por_estado = {estado: 0 for estado in estados_relevantes}
        problemas_scatter = []
        problemas_por_categoria = {}

        for problema in problemas:
            if problema.estado_problema in problemas_por_estado:
                problemas_por_estado[problema.estado_problema] += 1

            problemas_scatter.append({'x': problema.estado, 'y': problema.nivel_riesgo})

            categoria = problema.categoria or 'Sin Categorizar'
            if categoria in problemas_por_categoria:
                problemas_por_categoria[categoria] += 1
            else:
                problemas_por_categoria[categoria] = 1

        response = {
            'problemas_por_estado': list(problemas_por_estado.values()),
            'problemas_por_estado_labels': list(problemas_por_estado.keys()),
            'problemas_scatter': problemas_scatter,
            'problemas_por_categoria': {
                'labels': list(problemas_por_categoria.keys()),
                'data': list(problemas_por_categoria.values())
            }
        }
        return jsonify(response)

    except Exception as e:
        print(f"Error al generar las estadísticas: {e}")
        return jsonify({'error': 'Ocurrió un error al obtener las estadísticas'}), 500

@app.route('/estadisticas')
def estadisticas():
    return render_template('estadisticas.html')

@app.route('/elevadores')
def elevadores():
    file_path = 'C:\\Users\\rales\\Documents\\proyecto-login\\elevadores2.csv'
    df = pd.read_csv(file_path)

    elevadores = df[['Latitud', 'Longitud', 'Unidad_Medica', 'Marca', 'Uso', 'Estado']].to_dict(orient='records')

    return render_template('elevadores.html', elevadores=elevadores)

@app.route('/marcar_elevador', methods=['POST'])
def marcar_elevador():
    latitud = request.form['latitud']
    longitud = request.form['longitud']
    estado = request.form['estado']

    file_path = 'C:\\Users\\rales\\Documents\\proyecto-login\\elevadores2.csv'
    df = pd.read_csv(file_path)

    df.loc[(df['Latitud'] == float(latitud)) & (df['Longitud'] == float(longitud)), 'Estado'] = estado
    df.to_csv(file_path, index=False)

    return redirect(url_for('elevadores'))

@app.route('/aires', methods=['GET', 'POST'])
def aires():
    file_path = 'C:\\Users\\rales\\Documents\\proyecto-login\\Levantamiento_Aires_acondicionados.xlsx'
    df = pd.read_excel(file_path)

    df.columns = df.columns.str.strip()

    if request.method == 'POST':
        estado_representacion = request.form['estado_representacion']
        unidad_medica = request.form['unidad_medica']
        marca = request.form['marca']
        modelo = request.form['modelo']
        tipo_equipo = request.form['tipo_equipo']
        estatus = request.form['estatus']

        api_key = "AIzaSyAhPtAHcRPnNIzo9-1Ab_Qxn7HFTRjPK9s"
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={unidad_medica},+{estado_representacion},+Mexico&key={api_key}"
        response = requests.get(geocode_url)
        geocode_data = response.json()

        if geocode_data['status'] == 'OK':
            lat = geocode_data['results'][0]['geometry']['location']['lat']
            lon = geocode_data['results'][0]['geometry']['location']['lng']
        else:
            lat, lon = None, None

        nueva_fila = {
            'ESTADO /REPRESENTACIÓN': estado_representacion,
            'UNIDAD MÉDICA': unidad_medica,
            'MARCA': marca,
            'MODELO': modelo,
            'TIPO DE EQUIPO': tipo_equipo,
            'ESTATUS ESPECÍFICOS (SITUACIÓN ACTUAL/FALLA QUE PRESENTA)': estatus,
            'LATITUD': lat,
            'LONGITUD': lon
        }

        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
        df.to_excel(file_path, index=False)

    estado_representacion = request.args.get('estado_representacion')
    marca = request.args.get('marca')
    unidad_medica = request.args.get('unidad_medica')

    if estado_representacion:
        df = df[df['ESTADO /REPRESENTACIÓN'] == estado_representacion]
    if marca:
        df = df[df['MARCA'] == marca]
    if unidad_medica:
        df = df[df['UNIDAD MÉDICA'] == unidad_medica]

    aires = df[['LATITUD', 'LONGITUD', 'UNIDAD MÉDICA', 'MARCA', 'TIPO DE EQUIPO', 'ESTATUS ESPECÍFICOS (SITUACIÓN ACTUAL/FALLA QUE PRESENTA)', 'ESTADO /REPRESENTACIÓN']].dropna(subset=['LATITUD', 'LONGITUD']).to_dict(orient='records')
    unidades_medicas = df['UNIDAD MÉDICA'].dropna().unique().tolist()
    estados_representacion = df['ESTADO /REPRESENTACIÓN'].dropna().unique().tolist()
    marcas = df['MARCA'].dropna().unique().tolist()

    return render_template('aires.html', aires=aires, unidades_medicas=unidades_medicas, estados_representacion=estados_representacion, marcas=marcas)

@app.route('/editar_aire', methods=['POST'])
def editar_aire():
    file_path = 'C:\\Users\\rales\\Documents\\proyecto-login\\Levantamiento_Aires_acondicionados.xlsx'
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()

    index = int(request.form['index'])
    estado_representacion = request.form['estado_representacion']
    unidad_medica = request.form['unidad_medica']
    marca = request.form['marca']
    modelo = request.form['modelo']
    tipo_equipo = request.form['tipo_equipo']
    estatus = request.form['estatus']

    df.at[index, 'ESTADO /REPRESENTACIÓN'] = estado_representacion
    df.at[index, 'UNIDAD MÉDICA'] = unidad_medica
    df.at[index, 'MARCA'] = marca
    df.at[index, 'MODELO'] = modelo
    df.at[index, 'TIPO DE EQUIPO'] = tipo_equipo
    df.at[index, 'ESTATUS ESPECÍFICOS (SITUACIÓN ACTUAL/FALLA QUE PRESENTA)'] = estatus

    df.to_excel(file_path, index=False)
    return redirect(url_for('aires'))

@app.route('/eliminar_aire', methods=['POST'])
def eliminar_aire():
    file_path = 'C:\\Users\\rales\\Documents\\proyecto-login\\Levantamiento_Aires_acondicionados.xlsx'
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()

    index = int(request.form['index'])
    df = df.drop(index).reset_index(drop=True)

    df.to_excel(file_path, index=False)
    return redirect(url_for('aires'))

@app.route('/cambiar_estado_problema', methods=['POST'])
def cambiar_estado_problema():
    if 'username' not in session:
        return redirect(url_for('index'))

    try:
        ticket_id = request.form['ticket_id']
        nuevo_estado = request.form['nuevo_estado']
        origen = request.form['origen']
    except KeyError as e:
        return f"Falta el campo {str(e)} en el formulario", 400

    problema = Problema.query.filter_by(ticket_id=ticket_id).first()
    if problema:
        problema.estado_problema = nuevo_estado
        problema.origen = origen
        db.session.commit()

    return redirect(url_for('dashboard', mensaje='Estado del problema actualizado exitosamente'))

@app.route('/origen_problema')
def origen_problema():
    problemas = Problema.query.all()  # Ajustamos para mostrar todos los problemas
    return render_template('origen_problema.html', problemas=problemas)

@app.route('/problemas_en_proceso')
def problemas_en_proceso():
    problemas = Problema.query.filter_by(estado_problema='En Proceso').all()
    return render_template('problemas_en_proceso.html', problemas=problemas)

@app.route('/problemas_no_solucionados')
def problemas_no_solucionados():
    problemas = Problema.query.filter_by(estado_problema='No Solucionado').all()
    return render_template('problemas_no_solucionados.html', problemas=problemas)

@app.route('/problemas_solucionados')
def problemas_solucionados():
    problemas = Problema.query.filter_by(estado_problema='Solucionado').all()
    return render_template('problemas_solucionados.html', problemas=problemas)

@app.route('/aceptar_rechazar_problema', methods=['POST'])
def aceptar_rechazar_problema():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))

    try:
        ticket_id = request.form['ticket_id']
        decision = request.form['decision']
    except KeyError as e:
        return f"Falta el campo {str(e)} en el formulario", 400

    problema = Problema.query.filter_by(ticket_id=ticket_id).first()
    if problema:
        problema.aceptado = decision
        if decision == "Rechazado":
            problema.estado_problema = "Rechazado"
        db.session.commit()

    return redirect(url_for('dashboard', mensaje=f'Problema {decision.lower()} exitosamente'))

@app.route('/reporte_problemas')
def reporte_problemas():
    try:
        problemas = Problema.query.all()
        return render_template('reporte_problemas.html', problemas=problemas)
    except Exception as e:
        print(f"Error al cargar el reporte de problemas: {e}")
        return str(e), 500

@app.route('/generate_report_pdf')
def generate_report_pdf():
    try:
        problemas = Problema.query.filter(Problema.estado_problema.in_(['Solucionado', 'No Solucionado', 'En Proceso'])).all()

        rendered = render_template('reporte_problemas.html', problemas=problemas)

        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'custom-header': [('Accept-Encoding', 'gzip')],
            'no-outline': None,
            'enable-local-file-access': None  # Permite acceso a archivos locales
        }

        # Ruta donde se almacenará el PDF
        pdf_path = r'C:\Users\rales\Documents\proyecto-login\static\reports\ISSSTE_membretada_2024.pdf'

        pdfkit.from_string(rendered, pdf_path, options=options, configuration=config)

        return send_file(pdf_path, as_attachment=True, download_name='ISSSTE_REPORTE_2024.pdf')

    except Exception as e:
        print(f"Error al generar el PDF: {e}")
        return str(e), 500
    
if __name__ == '__main__':
    app.run(debug=True)
