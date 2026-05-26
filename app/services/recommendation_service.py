def get_recommendation(data):
    # ejemplo simple por ahora

    altitude = data.get("altitude")
    climate = data.get("climate")

    if not altitude or not climate:
        return "No data provided"

    # lógica básica (placeholder)
    return f"Recommended forage for altitude {altitude} and climate {climate}"