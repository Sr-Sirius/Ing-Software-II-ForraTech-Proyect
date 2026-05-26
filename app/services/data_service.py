import pg8000

def get_forrajeo_data():
    """
    Conecta a PostgreSQL y obtiene todos los datos de la tabla 'forrajeo'.
    Retorna una lista de filas o una lista vacía si hay error.
    """
    try:
        # Conexión
        conexion = pg8000.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="TU_CONTRASEÑA",  # Reemplaza con tu contraseña real
            database="forrratech"
        )
        
        cursor = conexion.cursor()
        
        # Consulta
        cursor.execute("SELECT * FROM forrajeo;")
        
        # Obtener datos
        datos = cursor.fetchall()
        
        # Cerrar conexión
        cursor.close()
        conexion.close()
        
        return datos  # Retorna la lista de filas
    
    except Exception as e:
        print(f"Error al conectar o consultar la base de datos: {e}")
        return []  # Retorna lista vacía en caso de error


OVINOS = [
    {"name": "Sheep Criolla", "description": "Adapted to cold climates"}
]

CAPRINOS = [
    {"name": "Boer Goat", "description": "Good meat production"}
]

FORRAJES = [
    {"name": "Kikuyu Grass", "description": "High altitude grass"}
]