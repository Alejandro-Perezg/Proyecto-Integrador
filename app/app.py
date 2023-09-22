from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/', methods = ['GET'])
def hello():
    return f'Hello world'

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
    