from flask import Flask, request, render_template, redirect

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
def hello():
    if request.method == 'POST':
        db = firestore.client()
        username = request.form['username']
        password = request.form['password']
        return redirect('/home')
    else:
        return render_template('inicio_sesion.html')
    
@app.route('/home')
def home():
    return f'Welcome Home'

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = firestore.client()
        username = request.form['username']
        password = request.form['password']
        repetirPassword = request.form['repetirPassword']
        correoElectronico = request.form['correoElectronico']
        fechaNacimiento = request.form['fechaNacimiento']
        club = request.form['club']
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
        return render_template('registro.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
    