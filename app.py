from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")  # Ruta principal
def home():
    return "¡Hola Mundo con Flask!"

@app.route("/saludo/<nombre>")  # Ruta con parámetro
def saludar(nombre):
    return f"Hola, {nombre}!"

@app.route("/template")  # Ruta que renderiza un HTML
def template():
    return render_template("index.html", titulo="Mi página Flask")

if __name__ == "__main__":
    app.run(debug=True)  # Inicia el servidor en modo desarrollo