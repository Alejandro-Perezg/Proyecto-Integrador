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
            return render_template('menu_inicio.html', usuario = usuario)
        elif rol == "administrador":
            Usuario = usuario
            return render_template('menu_inicio_administracion.html', usuario=usuario)
        else:
            Usuario = usuario
            return render_template('menu_inicio_propietario.html', usuario=usuario)
    else:
        return redirect(url_for('login'))
    
@app.route('/sesiones_activas/<string:usuario>')
def sesiones_activas(usuario):
    sesiones_activas = traer_sesiones_activas(usuario)
    print(sesiones_activas)
    return render_template("sesiones_activas.html", sesiones = sesiones_activas)

@app.route('/informacion_personal')
def informacion_personal():
    return render_template("informacion_personal.html")

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
            rol =request.form.get('rol')
            if rol == "rol" or club == "club":
                mensaje = ""
                return render_template('cambios_usuario.html', usuario = usuario, clubes = clubes, mensaje = mensaje)
            else:
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
        acceso = request.form['numero']
        tema = request.form['tema']
        palabra = request.form['palabra']
        definicion = request.form['definicion_y_ejemplo']
        invitacion = request.form['invitacion']
        data = {'username':usuario,
                'titulo':titulo,
                'fecha':fecha,
                'hora':hora,
                'acceso':acceso,
                'tema':tema,
                'palabra':palabra,
                'definicion':definicion,
                'invitacion':invitacion}
        
        mensaje = agendar(data)
        return render_template('agendar_sesion.html', mensaje = mensaje, usuario = usuario)
    else:
        mensaje = ""
        return render_template('agendar_sesion.html', mensaje = mensaje, usuario = usuario)

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
    doc_ref = db.collection("Users").document(user)
    doc_ref.update({'club':club})
    doc_ref.update({'rol':rol})
    doc_ref_club = db.collection("Clubes").document(club).collection("Users").document(user)
    doc_ref_club.set({'username':user})

def agendar(data):
    try:
        doc_ref = db.collection("Sesiones").document(data["titulo"])
        doc_ref.set(data)
        return "Se agendó la cita con exito"
    except:
        return "Hubo un problema al agendar la cita"
    
def traer_sesiones_activas(user):
    doc_ref = db.collection("Sesiones")
    filter_admin = FieldFilter("username", "==", user)
    docs = doc_ref.where(filter = filter_admin).get()
    sesiones = []
    for doc in docs:
        sesion = doc.to_dict()
        sesiones.append(sesion)
    return sesiones
    
    

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
    