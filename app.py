from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
import os
import requests
from datetime import datetime

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
            'fecha_hora': self.fecha_hora
        }

def importar_datos_excel():
    file_path = 'C:\\Users\\rales\\Documents\\proyecto-login\\Gestión_Tickets_Unidades_Médicas.xlsx'
    df = pd.read_excel(file_path)

    for _, row in df.iterrows():
        estado = str(row['Estado']) if pd.notna(row['Estado']) else 'Desconocido'
        prefix = estado[:2].upper()
        last_ticket = Problema.query.filter(Problema.ticket_id.like(f"{prefix}%")).order_by(Problema.ticket_id.desc()).first()
        if last_ticket:
            last_ticket_number = int(last_ticket.ticket_id[2:])
            ticket_id = f"{prefix}{last_ticket_number + 1:05d}"
        else:
            ticket_id = f"{prefix}00001"

        problema = Problema(
            estado=estado,
            unidad_medica=str(row['Unidad Médica']) if pd.notna(row['Unidad Médica']) else 'Desconocido',
            categoria=str(row['Categoría del Problema']) if pd.notna(row['Categoría del Problema']) else 'Desconocido',
            subcategoria=str(row['Subcategoría']) if pd.notna(row['Subcategoría']) else '',
            descripcion=str(row['Descripción del Problema']) if pd.notna(row['Descripción del Problema']) else 'No especificado',
            nivel_riesgo=str(row['Nivel de Riesgo']) if pd.notna(row['Nivel de Riesgo']) else 'Bajo',
            lat=23.634501,  # Placeholder, ajustar según los datos reales
            lon=-102.552784,  # Placeholder, ajustar según los datos reales,
            ticket_id=ticket_id,
            reportado_por_operativo=False,
            fecha_hora=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(problema)
    db.session.commit()

@app.before_request
def before_request():
    if not hasattr(app, 'first_request_done'):
        db.create_all()
        importar_datos_excel()
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
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user_info = user_roles.get(username)
    if user_info and user_info['password'] == password:
        session['username'] = username
        session['role'] = user_info['role']
        session['state'] = user_info.get('state')
        return redirect(url_for('dashboard'))
    else:
        return 'Usuario o contraseña incorrectos'

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    user_info = user_roles.get(session['username'])
    if user_info and user_info['role'] == 'operativo':
        problemas = Problema.query.filter_by(estado=user_info['state']).filter_by(reportado_por_operativo=True).order_by(Problema.id.desc()).all()
        unidades_medicas = Problema.query.with_entities(Problema.unidad_medica).filter_by(estado=user_info['state']).distinct().all()
        unidades_medicas = [um[0] for um in unidades_medicas]
        return render_template('dashboard_operativo.html', problemas=[problema.to_dict() for problema in problemas], unidades_medicas=unidades_medicas)
    elif user_info and user_info['role'] == 'admin':
        problemas = Problema.query.filter_by(reportado_por_operativo=True).filter(Problema.estado_problema == 'Pendiente').all()
        estados = sorted(set([estado[0] for estado in db.session.query(Problema.estado).distinct().all() if estado[0] not in ["Ciudad de México", "CDMX - Zona Norte", "CDMX - Zona Poniente", "CDMX - Zona Oriente", "CDMX - Zona Sur"]] + ["CDMX Zona Norte", "CDMX Zona Poniente", "CDMX Zona Oriente", "CDMX Zona Sur"]))
        return render_template('dashboard_admin.html', problemas=[problema.to_dict() for problema in problemas], estados=estados)
    elif user_info and user_info['role'] == 'superadmin':
        problemas = Problema.query.filter(Problema.estado_problema == 'Pendiente').order_by(Problema.id.desc()).all()
        estados = sorted(set([estado[0] for estado in db.session.query(Problema.estado).distinct().all() if estado[0] not in ["Ciudad de México", "CDMX - Zona Norte", "CDMX - Zona Poniente", "CDMX - Zona Oriente", "CDMX - Zona Sur"]] + ["CDMX Zona Norte", "CDMX Zona Poniente", "CDMX Zona Oriente", "CDMX Zona Sur"]))
        return render_template('dashboard_superadmin.html', problemas=[problema.to_dict() for problema in problemas], estados=estados)
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

    return     redirect(url_for('gestionar_usuarios'))

@app.route('/reportar_problema', methods=['POST'])
def reportar_problema():
    if 'username' not in session:
        return redirect(url_for('index'))

    try:
        estado = request.form['estado']
        unidad_medica = request.form['unidad_medica']
        categoria_problema = request.form['categoria_problema']
        subcategoria_problema = request.form['subcategoria']
        nivel_riesgo = request.form['nivel_riesgo']
        descripcion = request.form['descripcion']
        fecha_hora = request.form['fecha_hora']
    except KeyError as e:
        return f"Falta el campo {str(e)} en el formulario", 400

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
        lat=lat if lat else 23.634501,  # Usar lat y lon obtenidos de la geocodificación
        lon=lon if lon else -102.552784,
        ticket_id=ticket_id,
        reportado_por_operativo=True,  # Marcamos que es reportado por operativo
        fecha_hora=fecha_hora
    )
    db.session.add(problema)
    db.session.commit()

    return redirect(url_for('dashboard', mensaje='Problema reportado exitosamente'))

@app.route('/actualizar_ticket', methods=['POST'])
def actualizar_ticket():
    if 'username' not in session:
        return redirect(url_for('index'))

    ticket_id = request.form['ticket_id']
    nueva_actualizacion = request.form['nueva_actualizacion']
    fecha_hora_actualizacion = request.form['fecha_hora_actualizacion']

    problema = Problema.query.filter_by(ticket_id=ticket_id).first()
    if problema:
        if problema.actualizaciones:
            problema.actualizaciones += f"\n{fecha_hora_actualizacion}: {nueva_actualizacion}"
        else:
            problema.actualizaciones = f"{fecha_hora_actualizacion}: {nueva_actualizacion}"
        db.session.commit()
    
    return redirect(url_for('dashboard', mensaje='Ticket actualizado exitosamente'))

@app.route('/filtrar_datos_ajax', methods=['POST'])
def filtrar_datos_ajax():
    estado = request.form.get('estado')
    categoria = request.form.get('categoria')
    query = Problema.query.filter_by(reportado_por_operativo=True)  # Solo problemas reportados

    if estado:
        query = query.filter_by(estado=estado)
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    resultados = [problema.to_dict() for problema in query.all()]

    return jsonify({'datos': resultados})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/mapas')
def mapas():
    return render_template('mapas.html')

@app.route('/api/estadisticas')
def get_estadisticas():
    problemas = Problema.query.all()

    problemas_por_estado = {
        'Nuevos': sum(1 for p in problemas if p.estado_problema == 'Pendiente'),
        'No Solucionados': sum(1 for p in problemas if p.estado_problema == 'No Solucionado'),
        'Solucionados': sum(1 for p in problemas if p.estado_problema == 'Solucionado'),
        'En Proceso': sum(1 for p in problemas if p.estado_problema == 'En Proceso')
    }

    problemas_scatter = [{'x': p.estado, 'y': p.nivel_riesgo} for p in problemas]

    problemas_por_categoria = {
        'labels': list(set(p.categoria for p in problemas)),
        'data': [sum(1 for p in problemas if p.categoria == cat) for cat in set(p.categoria for p in problemas)]
    }

    return jsonify({
        'problemas_por_estado': list(problemas_por_estado.values()),
        'problemas_scatter': problemas_scatter,
        'problemas_por_categoria': problemas_por_categoria
    })

@app.route('/estadisticas')
def estadisticas():
    return render_template('estadisticas.html')

@app.route('/elevadores')
def elevadores():
    # Cargar datos del archivo CSV
    file_path = 'C:\\Users\\rales\\Documents\\proyecto-login\\elevadores2.csv'
    df = pd.read_csv(file_path)

    # Filtrar las columnas necesarias
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

    # Asegurarse de que las columnas se lean correctamente
    df.columns = df.columns.str.strip()

    if request.method == 'POST':
        estado_representacion = request.form['estado_representacion']
        unidad_medica = request.form['unidad_medica']
        marca = request.form['marca']
        modelo = request.form['modelo']
        tipo_equipo = request.form['tipo_equipo']
        estatus = request.form['estatus']

        # Realizar la geocodificación usando la API de Google Maps
        api_key = "AIzaSyAhPtAHcRPnNIzo9-1Ab_Qxn7HFTRjPK9s"
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={unidad_medica},+{estado_representacion},+Mexico&key={api_key}"
        response = requests.get(geocode_url)
        geocode_data = response.json()

        if geocode_data['status'] == 'OK':
            lat = geocode_data['results'][0]['geometry']['location']['lat']
            lon = geocode_data['results'][0]['geometry']['location']['lng']
        else:
            lat, lon = None, None  # Manejar el caso donde la geocodificación falla

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
    except KeyError as e:
        return f"Falta el campo {str(e)} en el formulario", 400

    if not ticket_id or not nuevo_estado:
        return 'Faltan datos en el formulario', 400

    problema = Problema.query.filter_by(ticket_id=ticket_id).first()
    if problema:
        problema.estado_problema = nuevo_estado
        db.session.commit()
    
    return redirect(url_for('dashboard', mensaje='Estado del problema actualizado exitosamente'))

@app.route('/problemas_solucionados')
def problemas_solucionados():
    problemas = Problema.query.filter_by(estado_problema='Solucionado').all()
    return render_template('problemas_solucionados.html', problemas=[problema.to_dict() for problema in problemas])

@app.route('/problemas_no_solucionados')
def problemas_no_solucionados():
    problemas = Problema.query.filter_by(estado_problema='No Solucionado').all()
    return render_template('problemas_no_solucionados.html', problemas=[problema.to_dict() for problema in problemas])

@app.route('/problemas_en_proceso')
def problemas_en_proceso():
    problemas = Problema.query.filter_by(estado_problema='En Proceso').all()
    return render_template('problemas_en_proceso.html', problemas=[problema.to_dict() for problema in problemas])

if __name__ == '__main__':
    app.run(debug=True)



