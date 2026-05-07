from flask import Flask, request, redirect
import psycopg2

app = Flask(__name__)

# Conexión a PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="forratech",
    user="postgres",
    password="1234",
    options="-c client_encoding=UTF8"
)

# Ruta principal
@app.route("/")
def inicio():
    try:
        cur = conn.cursor()

        cur.execute("SELECT * FROM forrajeo")
        datos = cur.fetchall()

        cur.close()

        resultado = """
        <h1>🌱 Datos de Forrajeo</h1>

        <a href='/agregar'>
            <button>Agregar nuevo dato</button>
        </a>

        <br><br>

        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Descripción</th>
                <th>PH</th>
                <th>Humedad</th>
                <th>Altitud</th>
                <th>Temperatura</th>
            </tr>
        """

        for d in datos:
            resultado += f"""
            <tr>
                <td>{d[0]}</td>
                <td>{d[1]}</td>
                <td>{d[2]}</td>
                <td>{d[3]} - {d[4]}</td>
                <td>{d[5]} - {d[6]}</td>
                <td>{d[7]} - {d[8]}</td>
                <td>{d[9]} - {d[10]}</td>
            </tr>
            """

        resultado += "</table>"
        return resultado

    except Exception as e:
        return f"<h2>Error:</h2><p>{e}</p>"


# Ruta para agregar datos
@app.route("/agregar", methods=["GET", "POST"])
def agregar():

    if request.method == "POST":

        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]

        ph_min = request.form["ph_min"]
        ph_max = request.form["ph_max"]

        humedad_min = request.form["humedad_min"]
        humedad_max = request.form["humedad_max"]

        altitud_min = request.form["altitud_min"]
        altitud_max = request.form["altitud_max"]

        temperatura_min = request.form["temperatura_min"]
        temperatura_max = request.form["temperatura_max"]

        try:
            cur = conn.cursor()

            sql = """
            INSERT INTO forrajeo
            (
                nombre,
                descripcion,
                ph_min,
                ph_max,
                humedad_min,
                humedad_max,
                altitud_min,
                altitud_max,
                temperatura_min,
                temperatura_max
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """

            valores = (
                nombre,
                descripcion,
                ph_min,
                ph_max,
                humedad_min,
                humedad_max,
                altitud_min,
                altitud_max,
                temperatura_min,
                temperatura_max
            )

            cur.execute(sql, valores)
            conn.commit()

            cur.close()

            return redirect("/")

        except Exception as e:
            return f"Error al guardar: {e}"

    return """
    <h1>Agregar Forraje</h1>

    <form method="POST">

        <label>Nombre:</label><br>
        <input type="text" name="nombre"><br><br>

        <label>Descripción:</label><br>
        <input type="text" name="descripcion"><br><br>

        <label>PH mínimo:</label><br>
        <input type="number" step="0.1" name="ph_min"><br><br>

        <label>PH máximo:</label><br>
        <input type="number" step="0.1" name="ph_max"><br><br>

        <label>Humedad mínima:</label><br>
        <input type="number" name="humedad_min"><br><br>

        <label>Humedad máxima:</label><br>
        <input type="number" name="humedad_max"><br><br>

        <label>Altitud mínima:</label><br>
        <input type="number" name="altitud_min"><br><br>

        <label>Altitud máxima:</label><br>
        <input type="number" name="altitud_max"><br><br>

        <label>Temperatura mínima:</label><br>
        <input type="number" name="temperatura_min"><br><br>

        <label>Temperatura máxima:</label><br>
        <input type="number" name="temperatura_max"><br><br>

        <button type="submit">Guardar</button>

    </form>
    """


# Ejecutar Flask
if __name__ == "__main__":
    app.run(debug=True)
