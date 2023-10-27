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
            return render_template('menu_inicio.html')
        elif rol == "administrador":
            Usuario = usuario
            return render_template('menu_inicio_administracion.html', Usuario=Usuario)
        else:
            Usuario = usuario
            return render_template('menu_inicio_propietario.html', Usuario=Usuario)
    else:
        return redirect(url_for('login'))
    

    
@app.route('/administracion')
def administracion():
    return render_template('clubes_admin.html')

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
            message = "¡La contraseña no concide con la confirmación de contraseña!"
            return render_template('registro.html', message=message)
        
        elif (password == "" or repetirPassword == "" or username == ""):
            message = "Tienes que llenar todos los campos"
            return render_template('registro.html', message=message)
        
        elif validar_correo(correoElectronico) == False:
            message = "El correo electronico no es válido."
            return render_template('registro.html', message=message)
        
        else:
            data = {
            'username': username,
            'password': password,
            'correoElectronico': correoElectronico,
            'fechaNacimiento': fechaNacimiento,
            'club': club,
            'rol': 'socio'
            }
            if usuario_existente("Users", username, correoElectronico) == "El usuario no existe":
                doc_ref = db.collection('Users').document(username)
                doc_ref.set(data)
                return redirect('/')
            elif usuario_existente("Users", username, correoElectronico) == "El nombre de usuario o correo electronico no estan disponibles":
                message = "El nombre de usuario o correo electronico no estan disponibles"
                return render_template('registro.html', message = message)
            else:
                message = "Hubo un problema con el registrop"
                return render_template('registro.html', message = message)

    else:
        message = ""
        clubes = get_documentos("Clubes", "club")
        print(clubes)
        return render_template('registro.html', message=message, clubes = clubes)
    

@app.route('/info', methods = ['GET', 'POST'])
    

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
    lista_clubes = []
    for doc in docs:
        club = doc.get(value)
        lista_clubes.append(club)

    print(lista_clubes)
    return lista_clubes
 
    
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


def crear_club(collection_name, nombre, usuarios, admin):
    data = {"club":nombre}
    doc_ref = db.collection(collection_name).document(nombre)
    doc_ref.set(data)
    collecion_usuarios_club = db.collection(collection_name).document(nombre).collection("Users")
    collecion_usuarios_club.add({"administrador": admin})
    for usuario in usuarios:
        collecion_usuarios_club.add({
            "username":usuario
        })
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
    