from flask import Flask, request, render_template, redirect, session, url_for
import re
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from operator import itemgetter
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
            return render_template('menu_inicio_socio.html', usuario = usuario, rol = rol)
        elif rol == "administrador":
            usuario = usuario
            clubes = traer_clubes_admin(usuario)
            return render_template('menu_inicio.html', usuario=usuario, clubes = clubes, rol = rol)
        else:
            usuario = usuario
            return render_template('menu_inicio_administracion.html', usuario=usuario, rol = rol )
    else:
        return redirect(url_for('login'))
    
@app.route('/sesiones_activas/<string:usuario>')
def sesiones_activas(usuario):
    sin_club = verificar_si_el_usuario_tiene_club(usuario)
    propietario = verificar_si_el_usuario_es_propietario(usuario)
    if sin_club:
        print("El usuario no tiene club")
        sesiones = traer_sesiones()
        return render_template("sesiones_activas_invitado.html", sesiones = sesiones, usuario = usuario)
    else:
        if propietario:
            sesiones = traer_sesiones()
            return render_template("sesiones_activas_invitado.html", sesiones = sesiones, usuario = usuario)
        sesiones_activas = traer_sesiones_activas(usuario)
        print("El usuario tiene club")
        return render_template("sesiones_activas.html", sesiones = sesiones_activas, usuario = usuario)

@app.route('/sesiones_pasadas/<string:usuario>')
def sesiones_pasadas(usuario):
    if verificar_si_el_usuario_es_propietario(usuario):
        sesiones_pasadas = traer_sesiones_pasadas_propietario()
        return render_template("sesiones_pasadas.html", sesiones = sesiones_pasadas, usuario = usuario)
    else:
        sesiones_activas = traer_sesiones_pasadas(usuario)
        return render_template("sesiones_pasadas.html", sesiones = sesiones_activas, usuario = usuario)



@app.route('/informacion_personal/<string:usuario>')
def informacion_personal(usuario):
    user = get_info_usuario(usuario)

    return render_template("informacion_personal.html", usuario = user)

@app.route('/participar_sesion/<string:sesion>/<string:usuario>', methods = ['GET', 'POST'])
def participar_sesion(sesion, usuario):
    if request.method == "POST":
        etapa = request.form.get("etapa")
        rol = request.form.get("rol")
        message = participar_en_sesion(sesion, usuario, etapa, rol)
        sesion_activa = get_sesion_activa(sesion)
        roles = traer_roles_sesion(sesion)
        if sesion_activa == "Hubo un problema cargando la sesión":
            return render_template("participar_sesion_1.html", sesion = sesion_activa, message = sesion_activa, usuario = usuario)
        else:
            return render_template("participar_sesion_1.html", sesion = sesion_activa, message = message, usuario = usuario, roles = roles)

    else:
        sesion_activa = get_sesion_activa(sesion)
        primera_etapa = get_participantes(sesion, "primera_etapa")
        segunda_etapa = get_participantes(sesion, "segunda_etapa")
        tercera_etapa = get_participantes(sesion, "tercera_etapa")
        cuarta_etapa = get_participantes(sesion, "cuarta_etapa")
        roles1 = traer_roles_sesion(sesion)
        roles2 = traer_roles_sesion2(sesion)
        roles3 = traer_roles_sesion3(sesion)
        roles4 = traer_roles_sesion4(sesion)

        if sesion_activa == "Hubo un problema cargando la sesión":
            return render_template("participar_sesion_1.html", sesion = sesion_activa, message = sesion_activa, usuario = usuario)
        else:
            return render_template("participar_sesion_1.html", sesion = sesion_activa,
                                    message = "",
                                    usuario = usuario,
                                    primera_etapa = primera_etapa,
                                    segunda_etapa = segunda_etapa,
                                    tercera_etapa = tercera_etapa,
                                    cuarta_etapa = cuarta_etapa,
                                    roles1 = roles1,
                                    roles2 = roles2,
                                    roles3 = roles3,
                                    roles4 = roles4)
        
@app.route('/sesion_pasada/<string:sesion>/<string:usuario>', methods = ['GET', 'POST'])
def sesion_pasada(sesion, usuario):
    sesion_activa = get_sesion_activa(sesion)
    primera_etapa = get_participantes(sesion, "primera_etapa")
    segunda_etapa = get_participantes(sesion, "segunda_etapa")
    tercera_etapa = get_participantes(sesion, "tercera_etapa")
    cuarta_etapa = get_participantes(sesion, "cuarta_etapa")
    if sesion_activa == "Hubo un problema cargando la sesión":
        return render_template("sesion_pasada.html", sesion = sesion_activa, message = sesion_activa, usuario = usuario)
    else:
        return render_template("sesion_pasada.html", sesion = sesion_activa,
                                message = "",
                                usuario = usuario,
                                primera_etapa = primera_etapa,
                                segunda_etapa = segunda_etapa,
                                tercera_etapa = tercera_etapa,
                                cuarta_etapa = cuarta_etapa)

@app.route('/clubes')
def clubes():
    clubes = get_descripciones_clubes()
    return render_template("clubes.html", clubes = clubes)

@app.route('/noticias')
def noticias():
    noticias = obtener_noticias_de_todos_los_clubes()
    print(noticias)
    return render_template("noticias.html", noticias = noticias)

@app.route('/aviso_de_privacidad')
def aviso_de_privacidad():
    return render_template("aviso_privacidad.html")
  
@app.route('/administracion/<string:usuario>/<string:rol>')
def administracion(usuario, rol):
    clubes = get_documentos("Clubes", "club")
    return render_template('clubes_admin.html', clubes = clubes, usuario = usuario, rol = rol)

@app.route('/usuarios_administracion/<string:usuario>/<string:rol>')
def usuarios_administracion(usuario, rol):
    users = get_documentos("Users", "username")
    return render_template('usuarios_club.html', users = users, usuario = usuario, rol = rol)

@app.route('/club/<string:club>')
def club(club):
    usuarios = obtener_usuarios_de_club(club)
    print(usuarios)
    return render_template('info_club.html', usuarios = usuarios, club = club)

@app.route('/club_admin/<string:usuario>/<string:club>/<string:rol>', methods = ['GET', 'POST'])
def club_admin(usuario, club, rol):
    if request.form.get("valor") == "1":
        usuarios = obtener_usuarios_de_club_admin(club)
        print(usuarios)
        return render_template('info_club_admin.html', usuarios = usuarios, club = club, message = "", usuario = usuario, rol = rol)
    else:
        usuario_eliminado = request.form.get("usuario_eliminado")
        message = eliminar_usuario_de_club(usuario_eliminado, club)
        usuarios = obtener_usuarios_de_club_admin(club)
        return render_template('info_club_admin.html', usuarios = usuarios, club = club, message = message, usuario = usuario, rol = rol)
    

@app.route('/descripcion_club/<string:usuario>/<string:club>/<string:rol>', methods = ['GET', 'POST'])
def descripcion_club(usuario, club, rol):
    if request.method == "POST":
        if request.form.get("valor") == "1":
            descripcion = request.form.get("descripcion")
            if descripcion == "":
                message = "Tienes que agregar una descripción"
                return render_template('descripcion_club.html', usuario = usuario, club = club, rol = rol, message = message)
            else:
                message = agregar_actualizar_descripcion(club, descripcion)
                return render_template('descripcion_club.html', usuario = usuario, club = club, rol = rol, message = message)
        else:
            titulo = request.form.get("titulo")
            contenido = request.form.get("contenido")
            if titulo == "" or contenido == "":
                message = "Tienes que escribir el titulo y el contenido"
                return render_template('descripcion_club.html', usuario = usuario, club = club, rol = rol, message = message)
            else:
                fecha_formateada = datetime.now().strftime("%Y-%m-%d")
                noticia = {
                    "titulo": titulo,
                    "contenido": contenido,
                    "fecha": fecha_formateada
                }
                message = agregar_noticia_a_club(club, noticia)
                return render_template('descripcion_club.html', usuario = usuario, club = club, rol = rol, message = message)

    return render_template('descripcion_club.html', usuario = usuario, club = club, rol = rol)



@app.route('/usuarios_admin/<string:usuario>/<string:club>/<string:rol>', methods = ['GET', 'POST'])
def usuarios_admin(usuario, club, rol):
    if request.method == 'POST':
        if request.form.get("valor") == "1":
            usuarios = get_documentos("Users", "username")
            return render_template("usuarios_admin.html", usuarios = usuarios, usuario = usuario, club = club, message = "", rol = rol)
        else:
            usuarios = get_documentos("Users", "username")
            usuario_agregado = request.form.get("usuario_agregado")
            message = agregar_usuario_a_club(usuario_agregado, club)
            return render_template("usuarios_admin.html", usuarios = usuarios, usuario = usuario, club = club, message = message, rol = rol)


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
        toastmaster = request.form['toastmaster']
        numero_proyectos = request.form['numero_proyectos']
        fecha_datetime = datetime.strptime(fecha, "%Y-%m-%d")
        hora = request.form['hora']
        tema = request.form['tema']
        palabra = request.form['palabra']
        definicion = request.form['definicion_y_ejemplo']
        club = request.form['club']
        numero = request.form['numero']
        roles = {}
        roles3 = {}

        for rol in range(1, int(numero_proyectos) + 1):
            roles3['rol1_proyecto' + str(rol)] = 'Introducción del Orador' + str(rol)
            roles3['rol2_proyecto' + str(rol)] = 'Evaluación del Orador' + str(rol)

        for key, value in request.form.items():
            if key.startswith('rol'):
                roles[key] = value

        for key, value in roles.items():
            print(f'{key}: {value}')

        data = {'username':usuario,
                'titulo':titulo,
                'toastmaster':toastmaster,
                'fecha':fecha_datetime,
                'hora':hora,
                'tema':tema,
                'palabra':palabra,
                'numero': numero,
                'numero_proyectos':  numero_proyectos,
                'definicion':definicion,
                'club': club,
                "primera_etapa": [],
                "segunda_etapa": [],
                "tercera_etapa": [],
                "cuarta_etapa": [],
                "roles1": {"Rol1":"Apertura del Oficial de Asambleas","Rol2":"Bienvenida del Presidente y / o Representante", "Rol3":"Autopresentación de invitados y socios","Rol4":"Apertura del Toastmaster de la sesión", "Rol5": "Presentación del equipo de Evaluación", "Rol6": "Sección Educativa"},
                "roles2":{"Rol1":"Introducción a la dinámica", "Rol2": "Sección de Table Topics®", "Rol3": "Evaluación de Table Topics®", "Rol4": "Concurso de Mejor Discurso de Table Topics®"},
                "roles3":roles3,
                "roles4": {"Rol1":"Introducción a la Dinámica","Rol2":"Introducción del Evaluador General", "Rol3":"Evaluación de Muletillas","Rol4":"Evaluación de Lenguaje Corporal", "Rol5": "Evaluación de Variedad Local", "Rol6": "Evaluación Gramatical", "Rol7": "Evaluación de Tiempo", "Rol8": "Evaluación General", "Rol9": "Concurso de Mejor Rol de la Sesión"},
                "roles_extra": roles}

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
@app.route('/crear_club/<string:usuario>/<string:rol>', methods = ['GET', 'POST'])
def crear_club(usuario, rol):
    if request.method == 'POST':
        club = request.form['nombre_club']
        admin = request.form['administradores']
        usuarios_club = request.form.getlist('miembros')
        if club == "":
            message = "Tienes que ponerle un nombre al club"
            admins = get_admins("Users")
            usuarios = get_documentos("Users", "username")
            return render_template("/crear_club.html", administradores = admins, usuarios = usuarios, message= message, usuario= usuario, rol = rol)
        elif admin == "administrador":
            message = "Tienes que elegir un administrador"
            admins = get_admins("Users")
            usuarios = get_documentos("Users", "username")
            return render_template("/crear_club.html", administradores = admins, usuarios = usuarios, message= message, usuario = usuario, rol = rol)     
        else:
            crear_club("Clubes", club, usuarios_club, admin)
            admins = get_admins("Users")
            usuarios = get_documentos("Users", "username")
            message = "El club se ha creado correctamente"
            return render_template("crear_club.html", administradores = admins, usuarios = usuarios, message= message, usuario = usuario, rol = rol)
    else:
       admins = get_admins("Users")
       usuarios = get_documentos("Users", "username")
       message = ""
       return render_template('crear_club.html', administradores = admins, usuarios = usuarios, message = message, usuario = usuario, rol = rol)



@app.route('/register', methods = ['GET', 'POST'])
def register():
    #Si el metodo llamado es Post se guardan los datos del formulario y se validan
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repetirPassword = request.form['repetirPassword']
        correoElectronico = request.form['correoElectronico']
        fechaNacimiento = request.form['fechaNacimiento']

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
            'club': 'Sin club',
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
    if club == "sacar_de_clubes":
        user_ref = db.collection("Users").document(user)
        user_ref.update({'club': "Sin club"})
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

def agregar_usuario_a_club(user, club):
    try:
        doc_ref_club = db.collection("Clubes").document(club).collection("Users").document(user)
        doc_ref_club.set({'username':user})
        user_ref = db.collection("Users").document(user)
        user_ref.update({'club': club})
        return "Se añadio el usuario " + user + " al club " + club
    except:
        return "Hubo un problema añadiendo al usuario"
    
def eliminar_usuario_de_club(user, club):
    doc_ref_club = db.collection("Clubes").document(club).collection("Users").document(user)
    doc_ref_club.delete()
    # Referencia a la colección "Clubes"
    clubes_ref = db.collection('Clubes')

    # Obtener todos los documentos de la colección "Clubes"
    documentos_clubes = clubes_ref.stream()

    # Variable para verificar si el usuario está en algún club
    usuario_en_otro_club = False

    # Verificar si el usuario está en alguna subcolección "Users" de algún club
    for clup in documentos_clubes:
        subcoleccion_users = clup.reference.collection('Users')
        user_doc = subcoleccion_users.document(user).get()
        
        # Si el documento existe, el usuario aún está en otro club
        if user_doc.exists:
            usuario_en_otro_club = True
            print("El usuario aún está en otro club.")
            break

    # Si no se encontró el usuario en ninguna subcolección "Users", imprimir el mensaje
    if not usuario_en_otro_club:
        user_ref = db.collection("Users").document(user)
        user_ref.update({'club': "Sin club"})
        print(f"El usuario con ID {user} no tiene club.")

    return "Se eliminó el usuario" + user + " del club " + club



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
        filter_club = FieldFilter("club", "==", club)
        fecha_actual = datetime.now()
        print(fecha_actual)
        filter_fecha = FieldFilter('fecha', '>', fecha_actual)
        filter_and = And(filters=[filter_club, filter_fecha])
        query = sesion.where(filter = filter_and).get()
        print(f"Club: {club}, Query Result: {query}")
        for sesion in query:
            sesiones.append(sesion.to_dict())
    print(sesiones)
    return sesiones

def traer_sesiones_pasadas(usuario):
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
        filter_club = FieldFilter("club", "==", club)
        fecha_actual = datetime.now()
        print(fecha_actual)
        filter_fecha = FieldFilter('fecha', '<', fecha_actual)
        filter_and = And(filters=[filter_club, filter_fecha])
        query = sesion.where(filter = filter_and).get()
        print(f"Club: {club}, Query Result: {query}")
        for sesion in query:
            sesiones.append(sesion.to_dict())
    print(sesiones)
    return sesiones

def traer_sesiones():
    sesiones = []
    fecha_actual = datetime.now()
    filter_fecha = FieldFilter('fecha', '>', fecha_actual)
    sesiones_ref = db.collection("Sesiones").where(filter = filter_fecha).get()
    for sesion in sesiones_ref:
        sesiones.append(sesion.to_dict())
    return sesiones

def traer_sesiones_pasadas_propietario():
    sesiones = []
    fecha_actual = datetime.now()
    filter_fecha = FieldFilter('fecha', '<', fecha_actual)
    sesiones_ref = db.collection("Sesiones").where(filter = filter_fecha).get()
    for sesion in sesiones_ref:
        sesiones.append(sesion.to_dict())
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

def obtener_usuarios_de_club_admin(club):
    # Hacer el query a la colección "Clubes" y la subcolección "Users"
    club_ref = db.collection('Clubes').document(club).collection('Users')
    
    # Obtener los documentos de la subcolección "Users"
    docs = club_ref.stream()
    
    # Inicializar una lista para almacenar los usuarios
    usuarios = []
    for doc in docs:
        usuario = doc.to_dict()
        if "username" in usuario:
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


def participar_en_sesion(sesion, usuario, etapa, rol):
        # Obtén una referencia a la colección "Sesiones" y a la sesión específica
        db = firestore.client()
        sesion_ref = db.collection("Sesiones").document(sesion)


        # Añade el usuario a la lista de la etapa correspondiente
        sesion_ref.update({
            etapa: firestore.ArrayUnion([{u'user': {'username': usuario, 'rol': rol}}])
        })
        return "Participación registrada"

def traer_roles_sesion(sesion):
    try:
        # Referencia a la sesión específica
        sesion_ref = db.collection("Sesiones").document(sesion)

        # Obtiene el diccionario de roles para la sesión específica
        sesion = sesion_ref.get()
        if sesion.exists:
            # Obtiene el diccionario de roles existentes
            roles = sesion.to_dict().get("roles1", {})
            
            # Obtiene la lista de roles extra
            roles_extra = sesion.to_dict().get("roles_extra", [])
            
            # Combina los roles y roles_extra en una sola lista
            roles.update(roles_extra)
            
            # Obtiene los nombres de los roles combinados
            nombres_roles = list(roles.values())
            
            print(f"Nombres de roles en la sesión {sesion}: {nombres_roles}")
            return nombres_roles
        else:
            print(f"No se encontró la sesión con ID {sesion}.")
        
    except:
        return "Hubo un problema trayendo los roles"
    

def traer_roles_sesion2(sesion):
    try:
        # Referencia a la sesión específica
        sesion_ref = db.collection("Sesiones").document(sesion)

        # Obtiene el diccionario de roles para la sesión específica
        sesion = sesion_ref.get()
        if sesion.exists:
            # Obtiene el diccionario de roles existentes
            roles = sesion.to_dict().get("roles2", {})
            
            # Obtiene la lista de roles extra
            roles_extra = sesion.to_dict().get("roles_extra", [])
            
            # Combina los roles y roles_extra en una sola lista
            roles.update(roles_extra)
            
            # Obtiene los nombres de los roles combinados
            nombres_roles = list(roles.values())
            
            print(f"Nombres de roles en la sesión {sesion}: {nombres_roles}")
            return nombres_roles
        else:
            print(f"No se encontró la sesión con ID {sesion}.")
        
    except:
        return "Hubo un problema trayendo los roles"
    

def traer_roles_sesion3(sesion):
    try:
        # Referencia a la sesión específica
        sesion_ref = db.collection("Sesiones").document(sesion)

        # Obtiene el diccionario de roles para la sesión específica
        sesion = sesion_ref.get()
        if sesion.exists:
            # Obtiene el diccionario de roles existentes
            roles = sesion.to_dict().get("roles3", {})
            
            # Obtiene la lista de roles extra
            roles_extra = sesion.to_dict().get("roles_extra", [])
            
            # Combina los roles y roles_extra en una sola lista
            roles.update(roles_extra)
            
            # Obtiene los nombres de los roles combinados
            nombres_roles = list(roles.values())
            
            print(f"Nombres de roles en la sesión {sesion}: {nombres_roles}")
            return nombres_roles
        else:
            print(f"No se encontró la sesión con ID {sesion}.")
        
    except:
        return "Hubo un problema trayendo los roles"
    

def traer_roles_sesion4(sesion):
    try:
        # Referencia a la sesión específica
        sesion_ref = db.collection("Sesiones").document(sesion)

        # Obtiene el diccionario de roles para la sesión específica
        sesion = sesion_ref.get()
        if sesion.exists:
            # Obtiene el diccionario de roles existentes
            roles = sesion.to_dict().get("roles4", {})
            
            # Obtiene la lista de roles extra
            roles_extra = sesion.to_dict().get("roles_extra", [])
            
            # Combina los roles y roles_extra en una sola lista
            roles.update(roles_extra)
            
            # Obtiene los nombres de los roles combinados
            nombres_roles = list(roles.values())
            
            print(f"Nombres de roles en la sesión {sesion}: {nombres_roles}")
            return nombres_roles
        else:
            print(f"No se encontró la sesión con ID {sesion}.")
        
    except:
        return "Hubo un problema trayendo los roles"
    


        

def get_participantes(sesion, etapa):
    sesion_ref = db.collection("Sesiones").document(sesion)

    # Obtiene los datos de la sesión
    sesion_data = sesion_ref.get().to_dict()
    usernames1 = []
    print(sesion_data[etapa])
    for user in sesion_data[etapa]:
        usuario = {"user":{"username": "", "rol": ""}}
        username = user.get('user',{}).get("username")
        usuario["user"]["username"] = username
        rol = user.get('user',{}).get("rol")
        usuario["user"]["rol"] = rol
        usernames1.append(usuario)
    print(usernames1)    
    return usernames1

def agregar_actualizar_descripcion(club, nueva_descripcion):
    # Referencia al documento del club
    club_ref = db.collection('Clubes').document(club)

    # Si existe, actualiza la descripción
    club_ref.update({'descripcion': nueva_descripcion})
    return f'Descripción actualizada para el club con ID {club}'

def agregar_noticia_a_club(club_id, nueva_noticia):
    # Referencia al documento del club
    club_ref = db.collection('Clubes').document(club_id)

    # Obtiene el documento del club
    club_doc = club_ref.get()

    # Obtiene la lista actual de noticias del club o crea una lista vacía si no existe
    noticias_actuales = club_doc.to_dict().get('noticias', [])

    # Agrega la nueva noticia a la lista
    noticias_actuales.append(nueva_noticia)

    # Actualiza la lista de noticias en Firestore
    club_ref.update({'noticias': noticias_actuales})
    return f'Noticia agregada al club con ID {club_id}'

def get_descripciones_clubes():
    coleccion_clubes = 'Clubes'

    # Realiza el query para obtener los IDs y descripciones de los clubes
    clubes_ref = db.collection(coleccion_clubes)
    clubes_docs = clubes_ref.stream()

    # Crea una lista para almacenar los resultados
    resultados = []

    # Itera sobre los documentos y agrega los resultados a la lista
    for club in clubes_docs:
        id_club = club.id
        descripcion = club.to_dict().get('descripcion', None)
        resultados.append({'club': id_club, 'descripcion': descripcion})

    # Imprime la lista de resultados
    return resultados


def get_info_usuario(usuario):
    doc_ref = db.collection("Users").document(usuario)
    usuario = doc_ref.get().to_dict()
    return usuario

def obtener_noticias_de_todos_los_clubes():
    # Referencia a la colección de clubes
    clubes_ref = db.collection('Clubes')

    # Obtiene todos los documentos de la colección
    clubes_docs = clubes_ref.stream()

    # Diccionario para almacenar noticias de todos los clubes
    noticias_list = [] 

    # Itera sobre todos los clubes
    for club_doc in clubes_docs:
        # Obtiene el ID del club y la lista de noticias
        club_id = club_doc.id
        noticias_actuales = club_doc.to_dict().get('noticias', []) 
        for noticia in noticias_actuales:
            titulo = noticia.get('titulo', '')
            contenido = noticia.get('contenido', '')
            fecha = noticia.get('fecha', '')
            noticias_list.append({'titulo': titulo, 'contenido': contenido, 'fecha': fecha})

    # Ordena la lista de noticias por la fecha
    noticias_ordenadas = sorted(noticias_list, key=lambda x: x['fecha'])

    # Imprime las noticias ordenadas
    print(noticias_ordenadas)

     # Invierte el orden de la lista
    noticias_ordenadas.reverse()

     # Imprime las noticias ordenadas
    print(noticias_ordenadas)

    return noticias_ordenadas

def verificar_si_el_usuario_tiene_club(user_id):

    # Referencia al documento del usuario
    user_ref = db.collection('Users').document(user_id)

    # Obtiene el snapshot del documento
    user_snapshot = user_ref.get()

    # Verifica si el documento existe y si el atributo "club" es igual a "Sin Club"
    if user_snapshot.exists:
        user_data = user_snapshot.to_dict()
        if user_data.get('club') == 'Sin club':
            return True
        else:
            return False
    else:
        print(f"El usuario con ID {user_id} no existe.")
        return False
    

def verificar_si_el_usuario_es_propietario(user_id):

    # Referencia al documento del usuario
    user_ref = db.collection('Users').document(user_id)

    # Obtiene el snapshot del documento
    user_snapshot = user_ref.get()

    # Verifica si el documento existe y si el atributo "club" es igual a "Sin Club"
    if user_snapshot.exists:
        user_data = user_snapshot.to_dict()
        if user_data.get('rol') == 'propietario':
            return True
        else:
            return False
    else:
        print(f"El usuario con ID {user_id} no existe.")
        return False

    
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
    