"""
Serviciu pentru obținerea datelor meteo de la API
Responsabil: Danalache Sebastian
"""

from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer # Am adăugat QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class WeatherService(QObject):
    """
    Serviciu pentru comunicarea cu API-ul meteo Open-Meteo (gratuit, fără API key)
    Folosește QNetworkAccessManager pentru cereri HTTP asincrone
    """
    
    # Semnale pentru comunicarea cu UI
    weather_data_ready = pyqtSignal(dict)
    weather_error = pyqtSignal(str)
    
    def __init__(self):
        """
        Inițializează serviciul meteo
        """
        super().__init__()
        
        self.latitude = 44.4268  # Default
        self.longitude = 26.1025 # Default
        self.city_name = "București" # Default
        
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)
        
        # Cache pentru datele meteo
        self.cached_weather = None
        self.cache_timestamp = None
        self.cache_duration = 1800  # 30 minute în secunde
        
        # Preferințe utilizator
        self.temperature_unit = "celsius"  # sau "fahrenheit"
        
        self.pending_days_request = 0 # Stochează numărul de zile cerute
        
    def set_location(self, city_name: str):
        """Setează locația pentru care se cer datele meteo"""
        self.city_name = city_name
        self.cached_weather = None  # Invalidează cache-ul la schimbarea locației
        
    def set_temperature_unit(self, unit: str):
        """Setează unitatea de măsură pentru temperatură (celsius/fahrenheit)"""
        if unit.lower() in ["celsius", "fahrenheit"]:
            self.temperature_unit = unit.lower()
            self.cached_weather = None
            
    def fetch_weather_data(self, days: int = 7):
        """
        Pornește procesul de preluare a vremii:
        1. Obține coordonatele pentru self.city_name
        2. Apelează _fetch_weather_for_coords cu coordonatele găsite
        """
        self.pending_days_request = days
        
        # 1. Construiește URL-ul pentru geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={self.city_name}&count=1&language=ro&format=json"
        
        request = QNetworkRequest(QUrl(geo_url))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "WeatherScheduler/1.0")
        
        # AM ȘTERS: request.setProperty("request_type", "geocoding")
        
        print(f"Caut coordonatele pentru {self.city_name}...")
        self.network_manager.get(request)

    def _fetch_weather_for_coords(self, lat, lon, days):
        """Funcție ajutătoare care preia vremea DUPĂ ce avem coordonatele."""
        if self.is_cache_valid():
            print("Folosim datele din cache")
            self.weather_data_ready.emit(self.cached_weather)
            return
            
        base_url = "https://api.open-meteo.com/v1/forecast"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability,precipitation,weathercode,windspeed_10m",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "Europe/Bucharest",
            "forecast_days": min(days, 16)
        }
        
        if self.temperature_unit == "fahrenheit":
            params["temperature_unit"] = "fahrenheit"
            
        url_parts = [f"{base_url}?"]
        for key, value in params.items():
            url_parts.append(f"{key}={value}&")
        url_string = "".join(url_parts).rstrip("&")
        
        request = QNetworkRequest(QUrl(url_string))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, 
                         "WeatherScheduler/1.0")
                         
        # AM ȘTERS: request.setProperty("request_type", "weather")
        
        print(f"Solicit date meteo pentru {days} zile la {lat}, {lon}...")
        self.network_manager.get(request)
        
    def handle_response(self, reply: QNetworkReply):
        """Procesează răspunsul de la API (fie geocoding, fie weather)"""
        
        # === MODIFICARE AICI: Verificăm URL-ul ===
        url_string = reply.url().toString()

        if "geocoding-api.open-meteo.com" in url_string:
            # Acesta este un răspuns de la Geocoding
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                try:
                    geo_json = json.loads(bytes(data))
                    if not geo_json.get("results"):
                        self.weather_error.emit(f"Orașul '{self.city_name}' nu a fost găsit.")
                        return
                    
                    result = geo_json["results"][0]
                    self.latitude = result["latitude"]
                    self.longitude = result["longitude"]
                    print(f"Am găsit coordonatele: {self.latitude}, {self.longitude}")
                    
                    # Folosim QTimer.singleShot(0, ...) pentru a porni
                    # următoarea cerere DUPĂ ce funcția curentă se termină.
                    # Asta previne blocarea.
                    QTimer.singleShot(0, lambda: self._fetch_weather_for_coords(
                        self.latitude, 
                        self.longitude, 
                        self.pending_days_request
                    ))
                    
                except json.JSONDecodeError as e:
                    self.weather_error.emit(f"Eroare la parsarea geocoding: {str(e)}")
            else:
                self.weather_error.emit(f"Eroare la geocoding: {reply.errorString()}")

        elif "api.open-meteo.com/v1/forecast" in url_string:
            # Acesta este un răspuns de la Weather API
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                try:
                    weather_json = json.loads(bytes(data))
                    processed_data = self.process_weather_data(weather_json)
                    self.cached_weather = processed_data
                    self.cache_timestamp = datetime.now()
                    self.save_weather_to_file(processed_data)
                    self.weather_data_ready.emit(processed_data)
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Eroare la parsarea răspunsului JSON: {str(e)}"
                    print(error_msg)
                    self.weather_error.emit(error_msg)
            else:
                error_msg = f"Eroare la solicitarea datelor meteo: {reply.errorString()}"
                print(error_msg)
                self.weather_error.emit(error_msg)
        
        # Ștergem obiectul reply la final
        reply.deleteLater()
        
    def process_weather_data(self, raw_data: Dict) -> Dict:
        """
        Procesează datele brute de la API într-un format util pentru aplicație
        """
        processed = {
            "hourly": [],
            "daily": [],
            "location": {
                "latitude": raw_data.get("latitude"),
                "longitude": raw_data.get("longitude")
            }
        }
        
        # Procesează datele orare
        hourly_data = raw_data.get("hourly", {})
        times = hourly_data.get("time", [])
        temperatures = hourly_data.get("temperature_2m", [])
        precip_prob = hourly_data.get("precipitation_probability", [])
        precip = hourly_data.get("precipitation", [])
        weather_codes = hourly_data.get("weathercode", [])
        wind_speeds = hourly_data.get("windspeed_10m", [])
        
        for i in range(len(times)):
            hourly_entry = {
                "datetime": times[i],
                "temperature": temperatures[i] if i < len(temperatures) else None,
                "precipitation_probability": precip_prob[i] if i < len(precip_prob) else 0,
                "precipitation": precip[i] if i < len(precip) else 0,
                "weather_code": weather_codes[i] if i < len(weather_codes) else 0,
                "weather_description": self.get_weather_description(
                    weather_codes[i] if i < len(weather_codes) else 0
                ),
                "wind_speed": wind_speeds[i] if i < len(wind_speeds) else 0
            }
            processed["hourly"].append(hourly_entry)
            
        # Procesează datele zilnice
        daily_data = raw_data.get("daily", {})
        daily_times = daily_data.get("time", [])
        temp_max = daily_data.get("temperature_2m_max", [])
        temp_min = daily_data.get("temperature_2m_min", [])
        daily_precip = daily_data.get("precipitation_sum", [])
        daily_codes = daily_data.get("weathercode", [])
        
        for i in range(len(daily_times)):
            daily_entry = {
                "date": daily_times[i],
                "temperature_max": temp_max[i] if i < len(temp_max) else None,
                "temperature_min": temp_min[i] if i < len(temp_min) else None,
                "precipitation_sum": daily_precip[i] if i < len(daily_precip) else 0,
                "weather_code": daily_codes[i] if i < len(daily_codes) else 0,
                "weather_description": self.get_weather_description(
                    daily_codes[i] if i < len(daily_codes) else 0
                )
            }
            processed["daily"].append(daily_entry)
            
        return processed
        
    def get_weather_description(self, code: int) -> str:
        """
        Convertește codul WMO în descriere text
        """
        weather_codes = {
            0: "Senin",
            1: "Predominant senin",
            2: "Parțial înorat",
            3: "Înorat",
            45: "Ceață",
            48: "Ceață cu chiciură",
            51: "Burniță ușoară",
            53: "Burniță moderată",
            55: "Burniță densă",
            61: "Ploaie ușoară",
            63: "Ploaie moderată",
            65: "Ploaie torențială",
            71: "Ninsoare ușoară",
            73: "Ninsoare moderată",
            75: "Ninsoare puternică",
            77: "Fulgi de zăpadă",
            80: "Averse ușoare",
            81: "Averse moderate",
            82: "Averse puternice",
            85: "Averse de zăpadă ușoare",
            86: "Averse de zăpadă puternice",
            95: "Furtună",
            96: "Furtună cu grindină ușoară",
            99: "Furtună cu grindină puternică"
        }
        
        return weather_codes.get(code, "Necunoscut")
        
    def check_rain_risk_for_tomorrow(self, schedule_entries: List[Dict]) -> List[Dict]:
        """
        Verifică dacă există risc de ploaie pentru intervalele din ziua următoare
        """
        risky_entries = []
        
        if not self.cached_weather:
            return risky_entries
            
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        for entry in schedule_entries:
            time_range = entry.get("time", "")
            if "-" not in time_range:
                continue
                
            start_time_str = time_range.split("-")[0].strip()
            
            try:
                entry_datetime = datetime.strptime(
                    f"{tomorrow} {start_time_str}", 
                    "%Y-%m-%d %H:%M"
                )
            except ValueError:
                continue
                
            for hourly in self.cached_weather["hourly"]:
                hourly_dt = datetime.fromisoformat(hourly["datetime"])
                time_diff = abs((hourly_dt - entry_datetime).total_seconds())
                
                if time_diff <= 1800:  # 30 minute
                    precip_prob = hourly.get("precipitation_probability", 0)
                    precip_amount = hourly.get("precipitation", 0)
                    
                    if precip_prob > 30 or precip_amount > 0:
                        risky_entry = entry.copy()
                        risky_entry["weather_data"] = hourly
                        risky_entries.append(risky_entry)
                        break
                        
        return risky_entries
        
    def convert_temperature(self, temp: float, from_unit: str, to_unit: str) -> float:
        """Convertește temperatura între Celsius și Fahrenheit"""
        if from_unit == to_unit:
            return temp
            
        if from_unit.lower() == "celsius" and to_unit.lower() == "fahrenheit":
            return (temp * 9/5) + 32
        elif from_unit.lower() == "fahrenheit" and to_unit.lower() == "celsius":
            return (temp - 32) * 5/9
        else:
            return temp
            
    def is_cache_valid(self) -> bool:
        """Verifică dacă cache-ul este încă valid"""
        if not self.cached_weather or not self.cache_timestamp:
            return False
            
        elapsed = (datetime.now() - self.cache_timestamp).total_seconds()
        return elapsed < self.cache_duration
        
    def save_weather_to_file(self, data: Dict):
        """Salvează datele meteo în fișier JSON pentru persistență"""
        try:
            with open("resources/weather_cache.json", "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Nu s-au putut salva datele meteo: {e}")
            
    def load_weather_from_file(self) -> Optional[Dict]:
        """Încarcă datele meteo din fișier dacă există"""
        try:
            with open("resources/weather_cache.json", "r", encoding="utf-8") as f:
                cached = json.load(f)
                
            timestamp = datetime.fromisoformat(cached["timestamp"])
            elapsed = (datetime.now() - timestamp).total_seconds()
            
            if elapsed < self.cache_duration:
                self.cached_weather = cached["data"]
                self.cache_timestamp = timestamp
                return cached["data"]
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
            
        return None