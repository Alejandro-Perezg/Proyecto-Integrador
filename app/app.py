from flask import Flask, request, render_template, redirect

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter,Or, And

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
db = firestore.client()

@app.route('/', methods = ['GET', 'POST'])
def hello():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = getDocumentsForLogin("Users", username, password)
        print(data)
        return redirect('/home')
    else:
        return render_template('inicio_sesion.html')
    
@app.route('/home')
def home():
    return f'Welcome Home'

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repetirPassword = request.form['repetirPassword']
        correoElectronico = request.form['correoElectronico']
        fechaNacimiento = request.form['fechaNacimiento']
        club = request.form['club']
        if password == repetirPassword:
            data = {
            'username': username,
            'password': password,
            'correoElectronico': correoElectronico,
            'fechaNacimiento': fechaNacimiento,
            'club': club
            }
            doc_ref = db.collection('Users').document()
            doc_ref.set(data)
            return redirect('/')
        else: 
            print("La contraseña no concide con la confirmación de contraseña")
            return redirect('/register')
    else:
        return render_template('registro.html')
    

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


            
        



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
    