from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class WeatherService(QObject):
    """
    Serviciu pentru comunicarea cu API-ul meteo Open-Meteo (gratuit, fara API key)
    Foloseste QNetworkAccessManager pentru cereri HTTP asincrone
    """
    
    weather_data_ready = pyqtSignal(dict)
    weather_error = pyqtSignal(str)
    
    def __init__(self):
        """
        Initializeaza serviciul meteo
        """
        super().__init__()
        
        self.latitude = 44.4268  
        self.longitude = 26.1025  
        self.city_name = "Bucuresti"    
        
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)
        
        self.cached_weather = None
        self.cache_timestamp = None
        self.cache_duration = 1800
        
        self.temperature_unit = "celsius"
        
        self.pending_days_request = 0 
        
    def set_location(self, city_name: str):
        """Seteaza locatia pentru care se cer datele meteo"""
        self.city_name = city_name
        self.cached_weather = None  
        
    def set_temperature_unit(self, unit: str):
        """Seteaza unitatea de masura pentru temperatura (celsius/fahrenheit)"""
        if unit.lower() in ["celsius", "fahrenheit"]:
            self.temperature_unit = unit.lower()
            self.cached_weather = None
            
    def fetch_weather_data(self, days: int = 7):
        """
        Porneste procesul de preluare a vremii:
        1. Obtine coordonatele pentru self.city_name
        2. Apeleaza _fetch_weather_for_coords cu coordonatele gasite
        """
        self.pending_days_request = days
        
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={self.city_name}&count=1&language=ro&format=json"
        
        request = QNetworkRequest(QUrl(geo_url))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "WeatherScheduler/1.0")
        
        print(f"Caut coordonatele pentru {self.city_name}...")
        self.network_manager.get(request)

    def _fetch_weather_for_coords(self, lat, lon, days):
        """Functie ajutatoare care preia vremea DUPA ce avem coordonatele."""
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
        
        print(f"Solicit date meteo pentru {days} zile la {lat}, {lon}...")
        self.network_manager.get(request)
        
    def handle_response(self, reply: QNetworkReply):
        """Proceseaza raspunsul de la API (fie geocoding, fie weather)"""
        
        url_string = reply.url().toString()

        if "geocoding-api.open-meteo.com" in url_string:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                try:
                    geo_json = json.loads(bytes(data))
                    if not geo_json.get("results"):
                        self.weather_error.emit(f"Orasul '{self.city_name}' nu a fost gasit.")
                        return
                    
                    result = geo_json["results"][0]
                    self.latitude = result["latitude"]
                    self.longitude = result["longitude"]
                    print(f"Am gasit coordonatele: {self.latitude}, {self.longitude}")
                    
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
                    error_msg = f"Eroare la parsarea raspunsului JSON: {str(e)}"
                    print(error_msg)
                    self.weather_error.emit(error_msg)
            else:
                error_msg = f"Eroare la solicitarea datelor meteo: {reply.errorString()}"
                print(error_msg)
                self.weather_error.emit(error_msg)
        
        reply.deleteLater()
        
    def process_weather_data(self, raw_data: Dict) -> Dict:
        """
        Proceseaza datele brute de la API intr-un format util pentru aplicatie
        """
        processed = {
            "hourly": [],
            "daily": [],
            "location": {
                "latitude": raw_data.get("latitude"),
                "longitude": raw_data.get("longitude")
            }
        }
        
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
        Converteste codul WMO in descriere text
        """
        weather_codes = {
            0: "Senin",
            1: "Predominant senin",
            2: "Partial inorat",
            3: "Inorat",
            45: "Ceata",
            48: "Ceata cu chiciura",
            51: "Burnita usoara",
            53: "Burnita moderata",
            55: "Burnita densa",
            61: "Ploaie usoara",
            63: "Ploaie moderata",
            65: "Ploaie torentiala",
            71: "Ninsoare usoara",
            73: "Ninsoare moderata",
            75: "Ninsoare puternica",
            77: "Fulgi de zapada",
            80: "Averse usoare",
            81: "Averse moderate",
            82: "Averse puternice",
            85: "Averse de zapada usoare",
            86: "Averse de zapada puternice",
            95: "Furtuna",
            96: "Furtuna cu grindina usoara",
            99: "Furtuna cu grindina puternica"
        }
        
        return weather_codes.get(code, "Necunoscut")
        
    def check_rain_risk_for_tomorrow(self, schedule_entries: List[Dict]) -> List[Dict]:
        """
        Verifica daca exista risc de ploaie pentru intervalele din ziua urmatoare
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
                
                if time_diff <= 1800: 
                    precip_prob = hourly.get("precipitation_probability", 0)
                    precip_amount = hourly.get("precipitation", 0)
                    
                    if precip_prob > 30 or precip_amount > 0:
                        risky_entry = entry.copy()
                        risky_entry["weather_data"] = hourly
                        risky_entries.append(risky_entry)
                        break
                        
        return risky_entries
        
    def convert_temperature(self, temp: float, from_unit: str, to_unit: str) -> float:
        """Converteste temperatura intre Celsius si Fahrenheit"""
        if from_unit == to_unit:
            return temp
            
        if from_unit.lower() == "celsius" and to_unit.lower() == "fahrenheit":
            return (temp * 9/5) + 32
        elif from_unit.lower() == "fahrenheit" and to_unit.lower() == "celsius":
            return (temp - 32) * 5/9
        else:
            return temp
            
    def is_cache_valid(self) -> bool:
        """Verifica daca cache-ul este inca valid"""
        if not self.cached_weather or not self.cache_timestamp:
            return False
            
        elapsed = (datetime.now() - self.cache_timestamp).total_seconds()
        return elapsed < self.cache_duration
        
    def save_weather_to_file(self, data: Dict):
        """Salveaza datele meteo in fisier JSON pentru persistenta"""
        try:
            with open("resources/weather_cache.json", "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Nu s-au putut salva datele meteo: {e}")
            
    def load_weather_from_file(self) -> Optional[Dict]:
        """Incarca datele meteo din fisier daca exista"""
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