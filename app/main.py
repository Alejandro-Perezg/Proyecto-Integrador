from flask import Flask, request, render_template, redirect, session, url_for
import re

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter,Or, And

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = '76bfc11478402f680540614ce08e8f76'
db = firestore.client()

@app.route('/', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        session['username'] = username
        data = getDocumentsForLogin("Users", username, password)
        print(data)
        if data == "Las credenciales ingresadas son incorrectas":
            message = "Las credenciales ingresadas son incorrectas"
            return render_template('inicio_sesion.html', message = message)
        
        elif data == "Hubo un problema iniciando sesión":
            message = "Hubo un problema iniciando sesión"
            return render_template('inicio_sesion.html', message = message)
        else:
            rol = data["rol"]
            usuario = data["username"]
            return redirect(f'/home/{usuario}/{rol}')
    else:
        return render_template('inicio_sesion.html')

    
    
@app.route('/home/<string:usuario>/<string:rol>')
def home(usuario, rol):
    if 'username' in session:
        if rol == "socio":
            print(usuario, rol)
            return render_template('menu_inicio_socio.html', usuario = usuario)
        elif rol == "administrador":
            usuario = usuario
            return render_template('menu_inicio.html', usuario=usuario)
        else:
            usuario = usuario
            return render_template('menu_inicio_administracion.html', usuario=usuario)
    else:
        return redirect(url_for('login'))
    
@app.route('/sesiones_activas/<string:usuario>')
def sesiones_activas(usuario):
    sesiones_activas = traer_sesiones_activas(usuario)
    print(sesiones_activas)
    return render_template("sesiones_activas.html", sesiones = sesiones_activas, usuario = usuario)

@app.route('/informacion_personal')
def informacion_personal():
    return render_template("informacion_personal.html")

@app.route('/participar_sesion/<string:sesion>/<string:usuario>', methods = ['GET', 'POST'])
def participar_sesion(sesion, usuario):
    if request.method == "POST":
        etapa = request.form.get("etapa")
        message = participar_en_sesion(sesion, usuario, etapa)
        sesion_activa = get_sesion_activa(sesion)
        if sesion_activa == "Hubo un problema cargando la sesión":
            return render_template("participar_sesion_1.html", sesion = sesion_activa, message = sesion_activa, usuario = usuario)
        else:
            return render_template("participar_sesion_1.html", sesion = sesion_activa, message = message, usuario = usuario)

    else:
        sesion_activa = get_sesion_activa(sesion)
        primera_etapa = get_participantes(sesion, "primera_etapa")
        segunda_etapa = get_participantes(sesion, "segunda_etapa")
        tercera_etapa = get_participantes(sesion, "tercera_etapa")
        cuarta_etapa = get_participantes(sesion, "cuarta_etapa")
        if sesion_activa == "Hubo un problema cargando la sesión":
            return render_template("participar_sesion_1.html", sesion = sesion_activa, message = sesion_activa, usuario = usuario)
        else:
            return render_template("participar_sesion_1.html", sesion = sesion_activa,
                                    message = "",
                                    usuario = usuario,
                                    primera_etapa = primera_etapa,
                                    segunda_etapa = segunda_etapa,
                                    tercera_etapa = tercera_etapa,
                                    cuarta_etapa = cuarta_etapa)

@app.route('/clubes')
def clubes():
    return render_template("clubes.html")

@app.route('/noticias')
def noticias():
    return render_template("noticias.html")

@app.route('/aviso_de_privacidad')
def aviso_de_privacidad():
    return render_template("aviso_privacidad.html")

@app.route('/info', methods = ['GET', 'POST'])
def info():
    return render_template('informacion_personal.html')

    
@app.route('/administracion')
def administracion():
    clubes = get_documentos("Clubes", "club")
    return render_template('clubes_admin.html', clubes = clubes)

@app.route('/usuarios_administracion')
def usuarios_administracion():
    users = get_documentos("Users", "username")
    return render_template('usuarios_club.html', users = users)

@app.route('/club/<string:club>')
def club(club):
    usuarios = obtener_usuarios_de_club(club)
    print(usuarios)
    return render_template('info_club.html', usuarios = usuarios, club = club)


@app.route('/cambios_usuario/<string:usuario>', methods = ['GET', 'POST'])
def cambios_usuario(usuario):
    if request.method == "POST":
        mensaje = request.form.get('mensaje')
        if mensaje == "eliminar usuario":
            borrar_usuario(usuario)
            return redirect("/administracion")
        else:
            mensaje = request.form.get('mensaje')
            club = request.form.get('club')
            rol = request.form.get('rol')
            if rol == "rol" or club == "club":
                mensaje = ""
                clubes = get_documentos("Clubes", "club")
                return render_template('cambios_usuario.html', usuario = usuario, clubes = clubes, mensaje = mensaje)
            else:
                clubes = get_documentos("Clubes", "club")
                cambios_usuario(usuario, club, rol)
                return render_template('cambios_usuario.html', usuario = usuario, clubes = clubes, mensaje = mensaje)
    else:
        clubes = get_documentos("Clubes", "club")
        return render_template('cambios_usuario.html', usuario = usuario, clubes = clubes)


@app.route('/agendar_sesion/<string:usuario>', methods= ['GET','POST'])
def agendar_sesion(usuario):
    if request.method == 'POST':
        titulo = request.form['titulo']
        fecha = request.form['fecha']
        hora = request.form['hora']
        acceso = request.form['acceso']
        tema = request.form['tema']
        palabra = request.form['palabra']
        definicion = request.form['definicion_y_ejemplo']
        invitacion = request.form['invitacion']
        club = request.form['club']
        numero = request.form['numero']
        data = {'username':usuario,
                'titulo':titulo,
                'fecha':fecha,
                'hora':hora,
                'acceso':acceso,
                'tema':tema,
                'palabra':palabra,
                'numero': numero,
                'definicion':definicion,
                'invitacion':invitacion,
                'club': club,
                "primera_etapa": [],
                "segunda_etapa": [],
                "tercera_etapa": [],
                "cuarta_etapa": []}

        mensaje = agendar(data)
        clubes = traer_clubes_admin(usuario)
        horas = obtener_lista_de_horas()
        return render_template('agendar_sesion.html', mensaje = mensaje, usuario = usuario, clubes = clubes, horas = horas)
    else:
        clubes = traer_clubes_admin(usuario)
        if clubes == "Hubo un problema trayendo los clubes":
            return render_template('agendar_sesion.html', mensaje = clubes, usuario = usuario, clubes = clubes)
        else:
            horas = obtener_lista_de_horas()
            return render_template('agendar_sesion.html', mensaje = "", usuario = usuario, clubes = clubes, horas = horas)
 

#Crear club
@app.route('/crear_club', methods = ['GET', 'POST'])
def crear_club():
    if request.method == 'POST':
        club = request.form['nombre_club']
        admin = request.form['administradores']
        usuarios_club = request.form.getlist('miembros')
        if club == "":
            message = "Tienes que ponerle un nombre al club"
            admins = get_admins("Users")
            usuarios = get_documentos("Users", "username")
            return render_template("/crear_club.html", administradores = admins, usuarios = usuarios, message= message)
        elif admin == "administrador":
            message = "Tienes que elegir un administrador"
            admins = get_admins("Users")
            usuarios = get_documentos("Users", "username")
            return render_template("/crear_club.html", administradores = admins, usuarios = usuarios, message= message)     
        else:
            crear_club("Clubes", club, usuarios_club, admin)
            admins = get_admins("Users")
            usuarios = get_documentos("Users", "username")
            message = "El club se ha creado correctamente"
            return render_template("crear_club.html", administradores = admins, usuarios = usuarios, message= message)
    else:
       admins = get_admins("Users")
       usuarios = get_documentos("Users", "username")
       message = ""
       return render_template('crear_club.html', administradores = admins, usuarios = usuarios, message = message)



@app.route('/register', methods = ['GET', 'POST'])
def register():
    #Si el metodo llamado es Post se guardan los datos del formulario y se validan
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repetirPassword = request.form['repetirPassword']
        correoElectronico = request.form['correoElectronico']
        fechaNacimiento = request.form['fechaNacimiento']
        club = request.form.get('club')

        if (password != repetirPassword):
            lista_clubes = get_documentos("Clubes", "club")
            message = "¡La contraseña no concide con la confirmación de contraseña!"
            return render_template('registro.html', message=message, clubes= lista_clubes)
        
        elif (password == "" or repetirPassword == "" or username == ""):
            message = "Tienes que llenar todos los campos"
            lista_clubes = get_documentos("Clubes", "club")
            return render_template('registro.html', message=message, clubes = lista_clubes)
        
        elif validar_correo(correoElectronico) == False:
            message = "El correo electronico no es válido."
            lista_clubes = get_documentos("Clubes", "club")
            return render_template('registro.html', message=message, clubes = lista_clubes)
        
        else:
            user = {
            'username': username,
            'password': password,
            'correoElectronico': correoElectronico,
            'fechaNacimiento': fechaNacimiento,
            'club': club,
            'rol': 'socio'
            }
            if usuario_existente("Users", username, correoElectronico) == "El usuario no existe": 
                register_user(user)
                return redirect('/')
                
            elif usuario_existente("Users", username, correoElectronico) == "El nombre de usuario o correo electronico no estan disponibles":
                lista_clubes = get_documentos("Clubes", "club")
                return render_template('registro.html', message="El nombre de usuario o correo electronico no estan disponibles", clubes = lista_clubes)
            else:
                message = "Hubo un problema con el registro"
                lista_clubes = get_documentos("Clubes", "club")
                return render_template('registro.html', message=message, clubes = lista_clubes)
    else:
        message = ""
        lista_clubes = get_documentos("Clubes", "club")
        print(lista_clubes)
        return render_template('registro.html', message=message, clubes = lista_clubes)
    
    

def getDocumentsForLogin(collection_name, username, password):
        try:
            doc_ref = db.collection(collection_name)
            #Filtros para el query
            filter_username = FieldFilter("username", "==", username)
            filter_password = FieldFilter("password", "==", password)
            and_filter = And(filters=[filter_username, filter_password])

            #Query con los filtros, este query busca si hay un usuario con el usuario y la contraseña especificado
            docs = doc_ref.where(filter=and_filter).get()
            if not docs:
                return "Las credenciales ingresadas son incorrectas"
            else:
                user = docs[0].to_dict()
                return(user)
        except:
            return "Hubo un problema iniciando sesión"

def validar_correo(correo):
    # Define una expresión regular para validar correos electrónicos
    patron = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    # Intenta hacer coincidir el patrón con el correo proporcionado
    if re.match(patron, correo):
        return True
    else:
        return False
#Funcion que trae un valor específico de los documentos de una colección
def get_documentos(collection_name, value):
    docs = (
        db.collection(collection_name).get()
            )
    lista_docs = []
    for doc in docs:
        club = doc.get(value)
        lista_docs.append(club)

    print(lista_docs)
    return lista_docs
 
    
#Funcion que verifica si el usario registrado existe
def usuario_existente(collectionName, username, coreoElectronico):
    try:
        doc_ref = db.collection(collectionName)
        #Filtros para el query
        filter_username = FieldFilter("username", "==", username)
        filter_email = FieldFilter("correoElectronico", "==", coreoElectronico)
        and_filter = Or(filters=[filter_username, filter_email])

        #Query con los filtros, este query busca si hay un usuario con el usuario y la contraseña especificado
        docs = doc_ref.where(filter=and_filter).get()
        if not docs:
            return "El usuario no existe"
        else:
            return "El nombre de usuario o correo electronico no estan disponibles"
    except:
        return "Hubo un problema con el registro"
    
#Funcion que registra un usuario
def register_user(user):
    doc_ref = db.collection('Users').document(user["username"])
    doc_ref.set(user)
    collecion_usuarios_club = db.collection("Clubes").document(user["club"]).collection("Users").document(user["username"])
    collecion_usuarios_club.set({"username": user["username"]})
    

#funcion que trae los usuarios que tienen el rol de administrador
def get_admins(collection_name):
    doc_ref = db.collection(collection_name)
    filter_admin = FieldFilter("rol", "==", "administrador")
    docs = doc_ref.where(filter = filter_admin).get()
    admin_list = []
    for doc in docs:
        admin = doc.get("username")
        admin_list.append(admin)
    return admin_list

#Funcion para crear un club
def crear_club(collection_name, nombre, usuarios, admin):
    data = {"club":nombre}
    doc_ref = db.collection(collection_name).document(nombre)
    doc_ref.set(data)
    doc_ref_admin = db.collection(collection_name).document(nombre).collection("Users").document(admin)
    doc_ref_admin.set({"administrador":admin})
    for usuario in usuarios:
        if usuario != admin:
            doc_ref_user = db.collection(collection_name).document(nombre).collection("Users").document(usuario)
            doc_ref_user.set({"username":usuario})
        else:
            print("El usuario elegido no se añadira, ya es el administrador del club")
#Funcion para borrar un usuario
def borrar_usuario(user):
    doc_ref = db.collection("Users").document(user)
    doc_ref.delete()

    lista_clubes = get_documentos("Clubes", "club")
    for doc in lista_clubes:
        doc_ref = db.collection("Clubes").document(doc).collection("Users").document(user)
        doc_ref.delete()
    
def cambios_usuario(user, club, rol):
    user_ref = db.collection("Users").document(user)
    user_ref.update({'club': "Sin club"})
    if club == "sacar_de_clubes":
        lista_clubes = get_documentos("Clubes", "club")
        for doc in lista_clubes:
            doc_ref = db.collection("Clubes").document(doc).collection("Users").document(user)
            doc_ref.delete()
    else:
        doc_ref = db.collection("Users").document(user)
        doc_ref.update({'club':club})
        doc_ref.update({'rol':rol})
        if rol == "socio":
            doc_ref_club = db.collection("Clubes").document(club).collection("Users").document(user)
            doc_ref_club.set({'username':user})
        else:
            doc_ref_club = db.collection("Clubes").document(club).collection("Users").document(user)
            doc_ref_club.set({'administrador':user})

def agendar(data):
        try:
            doc_ref = db.collection("Sesiones")
            #Filtros para el query
            filter_hora = FieldFilter("hora", "==", data["hora"])
            filter_fecha = FieldFilter("fecha", "==", data["fecha"])
            filter_club = FieldFilter("club", "==", data["club"])
            and_filter = And(filters=[filter_hora, filter_fecha, filter_club])

            docs = doc_ref.where(filter=and_filter).get()
            if not docs:
                doc_ref = db.collection("Sesiones").document(data["titulo"])
                doc_ref.set(data)
                return "Se agendó la cita con exito"
            else:
                return "Ya existe una cita para esa fecha a esa hora"
        except:
            return "Hubo un problema agendando la sesión"

    


#Esta funcion recibe un administrador y trae los clubes del administrador
def traer_clubes_admin(admin):
        try:
            # Obtiene una referencia a la colección "Clubes"
            clubes_ref = db.collection("Clubes")
            clubes_con_admin = []
            # Itera sobre los clubes
            for club in clubes_ref.stream():
                # Obtiene una referencia a la subcolección "Users" dentro de cada club
                users_ref = clubes_ref.document(club.id).collection("Users")
                
                # Realiza la consulta para encontrar usuarios con un administrador específico
                filter = FieldFilter("administrador", "==", admin)
                query = users_ref.where(filter = filter).get()
                
                # Si hay usuarios con ese administrador en la subcolección "Users" del club
                if query:
                    clubes_con_admin.append(club.id)
            return clubes_con_admin
        except:
            return "Hubo un problema trayendo los clubes"
        

def traer_sesiones_activas(usuario):
    clubes = db.collection("Clubes")
    clubes_con_usuario = []
    for club in clubes.stream():
        users_ref = clubes.document(club.id).collection("Users")
        filter_username = FieldFilter("username", "==", usuario)
        filter_admin = FieldFilter("administrador", "==", usuario)
        filter_or = Or(filters=[filter_username, filter_admin])
        query = users_ref.where(filter = filter_or).get()
        if query:
            clubes_con_usuario.append(club.id)
    print(clubes_con_usuario)
    sesiones = []
    for club in clubes_con_usuario:
        sesion = db.collection("Sesiones")
        filter = FieldFilter("club", "==", club)
        query = sesion.where(filter = filter).get()
        for sesion in query:
            sesiones.append(sesion.to_dict())
    print(sesiones)
    return sesiones

def get_sesion_activa(titulo):
    try:
        sesion = db.collection("Sesiones")
        filter = FieldFilter("titulo", "==", titulo)
        query = sesion.where(filter = filter).get()
        return query[0].to_dict()
    except:
        return "Hubo un problema cargando la sesión"
    
def obtener_usuarios_de_club(club):
    # Hacer el query a la colección "Clubes" y la subcolección "Users"
    club_ref = db.collection('Clubes').document(club).collection('Users')
    
    # Obtener los documentos de la subcolección "Users"
    docs = club_ref.stream()
    
    # Inicializar una lista para almacenar los usuarios
    usuarios = []
    
    # Iterar sobre los documentos y agregarlos a la lista
    for doc in docs:
        usuario = doc.to_dict()
        if "administrador" in usuario:
            usuario["rol"] = "1"
            usuario["username"] = usuario["administrador"]
            usuarios.append(usuario)
        else:
            usuario["rol"] = "2"
            usuarios.append(usuario)
    return usuarios


def obtener_lista_de_horas():
    # Hacer el query a la colección "Horas"
    horas_ref = db.collection('Horarios')
    
    # Obtener los documentos de la colección "Horas"
    docs = horas_ref.stream()
    
    # Inicializar una lista para almacenar las horas
    horas = []
    
    # Iterar sobre los documentos y obtener el campo "hora"
    for doc in docs:
        hora = doc.get('hora')
        horas.append(hora)
    
    return horas


def participar_en_sesion(sesion, usuario, etapa):
        # Obtén una referencia a la colección "Sesiones" y a la sesión específica
        db = firestore.client()
        sesion_ref = db.collection("Sesiones").document(sesion)

        # Verificar si el usuario ya está en alguna etapa
        sesion_data = sesion_ref.get().to_dict()

        for etapa_key in ["primera_etapa", "segunda_etapa", "tercera_etapa", "cuarta_etapa"]:
            if sesion_data.get(etapa_key):
                for participante in sesion_data[etapa_key]:
                    if participante.get("username") == usuario:
                        # El usuario ya está en esta etapa, no se añade nuevamente
                        return "Ya tienes un rol en la sesión"

        # Añade el usuario a la lista de la etapa correspondiente
        sesion_ref.update({
            etapa: firestore.ArrayUnion([{u'username': usuario}])
        })
        return "Participación registrada"

def get_participantes(sesion, etapa):
    sesion_ref = db.collection("Sesiones").document(sesion)

    # Obtiene los datos de la sesión
    sesion_data = sesion_ref.get().to_dict()

    # Verifica si la lista "primera_etapa" existe y obtén los usernames
    usernames = [etapa.get('username') for etapa in sesion_data[etapa]]
    return usernames
    
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
    