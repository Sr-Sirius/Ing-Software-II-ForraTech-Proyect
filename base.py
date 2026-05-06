from flask import Flask
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

        # HTML tipo tabla
        resultado = """
        <h1>🌱 Datos de Forrajeo</h1>
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

# Ejecutar Flask
if __name__ == "__main__":
    app.run(debug=True)
