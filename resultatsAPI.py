import openmeteo_requests
from datetime import datetime
import pandas as pd
import json
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 41.7281,
	"longitude": 1.824,
	"hourly": "temperature_2m",
	"timezone": "auto"
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m

hourly_dataframe = pd.DataFrame(data = hourly_data)
print(hourly_dataframe)

############## TEMPERATURES MANIPULADES ##############
def comprobar_temperatura_minima_maxima_mitjana(data):
        
    if isinstance(data, list) and len(data) == 0:
        print("No hi ha dades per llegir.")
        return
    
    temperatura_maxima = data[0]
    temperatura_minima = data[0]
    temperatura_mitjana = 0
    
    for temp in data:
        
        # Fer depuració
        if isinstance(temp, (int, float)):
            print("Valor incorrecte trobat.")
            
        # Sumar cada dada de temperatura
        temperatura_mitjana += temp
        
        # Guardar la temperatura Màxima a 'temperatura_maxima'
        if temp > temperatura_maxima:
            temperatura_maxima = temp
        
        # Guardar la temperatura Minima a 'temperatura_minima'
        if temp < temperatura_minima:
            temperatura_minima = temp

    return [temperatura_maxima, temperatura_minima, temperatura_mitjana / len(data)]

# Llista de temperatures extretes amb l'API
temperatures_data = hourly_data["temperature_2m"]

# Vars amb les dades demanades a la tasca
dades_calculades = comprobar_temperatura_minima_maxima_mitjana(temperatures_data)

if dades_calculades is not None:
    
    # Prints per mostrar la informació
    print("DADES DE CALCULADES:\n" + "="*30)
    print(f"La temperatura Màxima registrada és: {dades_calculades[0]}")
    print(f"La temperatura Minima registrada és: {dades_calculades[1]}")
    print(f"La temperatura Mitjana registrada és: {dades_calculades[2]}")

else:
    print(f"No hi ha dades disponibles a dades_calculades")

hourly_dataframe["date"] = hourly_dataframe["date"].astype(str)

datos_json = {
    "location": {
        "latitude": "41.75°N",
        "longitude": "1.8125°E",
        "elevation_m": 241,
        "timezone": "Europe/Madrid",
        "offset_seconds": 7200
    },
    "temperatura_datos":  [
        {
            "date": str(row["date"]),
            "temperature_2m": float(row["temperature_2m"])
        } for _, row in hourly_dataframe.iterrows()
    ],
    "resumen": {
        "max": str(dades_calculades[0]),
        "min": str(dades_calculades[1]),
        "promedio": str(dades_calculades[2])
    }
}

date = datetime.today().strftime("%Y-%m-%d")

with open(f"dades_json/temperatura_{date}.json", "w", encoding="utf-8") as f:
    json.dump(datos_json, f, indent=4, ensure_ascii=False)
