from PyQt6.QtCore import QObject, pyqtSignal, QUrl
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
    
    def __init__(self, latitude: float = 44.4268, longitude: float = 26.1025):
        """
        Inițializează serviciul meteo
        Default: București (44.4268°N, 26.1025°E)
        """
        super().__init__()
        
        self.latitude = latitude
        self.longitude = longitude
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)
        
        # Cache pentru datele meteo
        self.cached_weather = None
        self.cache_timestamp = None
        self.cache_duration = 1800  # 30 minute în secunde
        
        # Preferințe utilizator
        self.temperature_unit = "celsius"  # sau "fahrenheit"
        
    def set_location(self, latitude: float, longitude: float):
        """Setează locația pentru care se cer datele meteo"""
        self.latitude = latitude
        self.longitude = longitude
        self.cached_weather = None  # Invalidează cache-ul la schimbarea locației
        
    def set_temperature_unit(self, unit: str):
        """Setează unitatea de măsură pentru temperatură (celsius/fahrenheit)"""
        if unit.lower() in ["celsius", "fahrenheit"]:
            self.temperature_unit = unit.lower()
            
    def fetch_weather_data(self, days: int = 7):
        """
        Solicită date meteo pentru următoarele zile
        
        Args:
            days: Numărul de zile pentru care se cer datele (max 16 pentru API gratuit)
        """
        # Verifică cache-ul
        if self.is_cache_valid():
            print("Folosim datele din cache")
            self.weather_data_ready.emit(self.cached_weather)
            return
            
        # Construiește URL-ul pentru API Open-Meteo
        # API-ul este gratuit și nu necesită API key
        base_url = "https://api.open-meteo.com/v1/forecast"
        
        # Parametrii cererii
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": "temperature_2m,precipitation_probability,precipitation,weathercode,windspeed_10m",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "Europe/Bucharest",
            "forecast_days": min(days, 16)
        }
        
        # Adaugă unitatea de temperatură
        if self.temperature_unit == "fahrenheit":
            params["temperature_unit"] = "fahrenheit"
            
        # Construiește URL-ul complet
        url_parts = [f"{base_url}?"]
        for key, value in params.items():
            url_parts.append(f"{key}={value}&")
        url_string = "".join(url_parts).rstrip("&")
        
        # Creează cererea
        request = QNetworkRequest(QUrl(url_string))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, 
                         "WeatherScheduler/1.0")
        
        # Trimite cererea asincronă
        print(f"Solicit date meteo pentru {days} zile...")
        self.network_manager.get(request)
        
    def handle_response(self, reply: QNetworkReply):
        """Procesează răspunsul de la API"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            # Citește datele JSON
            data = reply.readAll()
            try:
                weather_json = json.loads(bytes(data))
                
                # Procesează datele
                processed_data = self.process_weather_data(weather_json)
                
                # Salvează în cache
                self.cached_weather = processed_data
                self.cache_timestamp = datetime.now()
                
                # Salvează în fișier pentru persistență
                self.save_weather_to_file(processed_data)
                
                # Emite semnalul cu datele procesate
                self.weather_data_ready.emit(processed_data)
                
            except json.JSONDecodeError as e:
                error_msg = f"Eroare la parsarea răspunsului JSON: {str(e)}"
                print(error_msg)
                self.weather_error.emit(error_msg)
        else:
            error_msg = f"Eroare la solicitarea datelor meteo: {reply.errorString()}"
            print(error_msg)
            self.weather_error.emit(error_msg)
            
        reply.deleteLater()
        
    def process_weather_data(self, raw_data: Dict) -> Dict:
        """
        Procesează datele brute de la API într-un format util pentru aplicație
        
        Returns:
            Dict cu structura:
            {
                "hourly": [
                    {
                        "datetime": "2025-01-15T08:00",
                        "temperature": 18,
                        "precipitation_probability": 20,
                        "precipitation": 0.0,
                        "weather_description": "Însorit",
                        "weather_code": 0,
                        "wind_speed": 10
                    },
                    ...
                ],
                "daily": [...]
            }
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
        Codurile WMO: https://open-meteo.com/en/docs
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
        
        Returns:
            Lista cu intrări care au risc de ploaie
        """
        risky_entries = []
        
        if not self.cached_weather:
            return risky_entries
            
        # Obține data de mâine
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        for entry in schedule_entries:
            # Extrage ora de începere din intervalul orar
            time_range = entry.get("time", "")
            if "-" not in time_range:
                continue
                
            start_time_str = time_range.split("-")[0].strip()
            
            # Construiește datetime-ul complet
            try:
                entry_datetime = datetime.strptime(
                    f"{tomorrow} {start_time_str}", 
                    "%Y-%m-%d %H:%M"
                )
            except ValueError:
                continue
                
            # Caută datele meteo pentru acest datetime
            for hourly in self.cached_weather["hourly"]:
                hourly_dt = datetime.fromisoformat(hourly["datetime"])
                
                # Verifică dacă este în același interval orar (±30 min)
                time_diff = abs((hourly_dt - entry_datetime).total_seconds())
                
                if time_diff <= 1800:  # 30 minute
                    # Verifică dacă există risc de ploaie (>30% probabilitate sau ploaie efectivă)
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
                
            # Verifică dacă cache-ul din fișier este valid (< 30 min)
            timestamp = datetime.fromisoformat(cached["timestamp"])
            elapsed = (datetime.now() - timestamp).total_seconds()
            
            if elapsed < self.cache_duration:
                self.cached_weather = cached["data"]
                self.cache_timestamp = timestamp
                return cached["data"]
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
            
        return None