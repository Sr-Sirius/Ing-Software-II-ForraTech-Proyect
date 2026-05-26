from app.db import get_connection

# =========================
# SHEEP
# =========================
def get_all_sheep():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM sheep
        ORDER BY breed
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


# =========================
# GOATS
# =========================
def get_all_goats():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM goats
        ORDER BY breed
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


# =========================
# FODDER / FORRAJE
# =========================
def get_all_fodder():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM forrajeo
        ORDER BY nombre
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data