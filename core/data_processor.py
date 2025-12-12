"""
Procesează datele de la WeatherService și le combină cu orarul.
Responsabil: Danalache Sebastian
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class DataProcessor:
    def __init__(self):
        self.day_map = {
            "Luni": 0, "Marți": 1, "Miercuri": 2, "Joi": 3, "Vineri": 4, 
            "Sâmbătă": 5, "Duminică": 6
        }
        # VARIABILA STOCATĂ PENTRU SIMBOLUL UNITĂȚII
        self.temp_unit_symbol = "°C" 

    def set_temperature_unit(self, unit: str):
        """Setează simbolul unității de temperatură pentru formatare."""
        if unit.lower() == "fahrenheit":
            self.temp_unit_symbol = "°F"
        else:
            self.temp_unit_symbol = "°C"

    def merge_schedule_with_weather(self, schedule_entries: List[Dict], weather_data: Dict) -> List[Dict]:
        """
        Combină intrările din orar cu datele meteo cele mai relevante
        """
        if not weather_data or "hourly" not in weather_data:
            return schedule_entries

        enriched_entries = []
        hourly_data = weather_data["hourly"]
        
        # Obține data și ora curentă (cu fus orar)
        if hourly_data:
            current_datetime_str = hourly_data[0].get("datetime")
            try:
                current_datetime = datetime.fromisoformat(current_datetime_str).astimezone()
            except ValueError:
                current_datetime = datetime.now() # Fallback
        else:
            current_datetime = datetime.now()

        # Parcurge intrările din orar
        for entry in schedule_entries:
            enriched = entry.copy()
            
            day_name = entry.get("day")
            time_range = entry.get("time")

            if day_name and time_range:
                # 1. Calculează data reală (ziua curentă + zile rămase până la ziua din orar)
                try:
                    target_day_of_week = self.day_map[day_name]
                except KeyError:
                    enriched["weather"] = None
                    enriched_entries.append(enriched)
                    continue

                days_to_add = (target_day_of_week - current_datetime.weekday() + 7) % 7
                # Dacă ziua din orar este azi, dar ora a trecut, mergem la săptămâna viitoare
                if days_to_add == 0 and time_range.split('-')[0] < current_datetime.strftime("%H:%M"):
                    days_to_add = 7

                target_date = (current_datetime + timedelta(days=days_to_add)).date()
                
                # 2. Extrage ora de început
                try:
                    start_time_str = time_range.split('-')[0].strip()
                    target_datetime = datetime.strptime(f"{target_date} {start_time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=current_datetime.tzinfo)
                except ValueError:
                    enriched["weather"] = None
                    enriched_entries.append(enriched)
                    continue

                # 3. Găsește cea mai apropiată prognoză orară
                closest_forecast = None
                min_diff = timedelta(hours=24) # Mai mult de un interval orar
                
                for hourly in hourly_data:
                    try:
                        hourly_dt = datetime.fromisoformat(hourly["datetime"]).astimezone()
                    except ValueError:
                        continue
                        
                    # Calculăm diferența față de ora de început a activității
                    diff = abs(target_datetime - hourly_dt)
                    
                    if diff < min_diff:
                        min_diff = diff
                        closest_forecast = hourly
                        
                    # Deoarece datele sunt ordonate, putem opri când diferența reîncepe să crească
                    if hourly_dt > target_datetime and diff > min_diff:
                        break

                enriched["date"] = target_date.isoformat()
                enriched["weather"] = closest_forecast
            else:
                enriched["weather"] = None

            enriched_entries.append(enriched)

        return enriched_entries

    def format_weather_for_table(self, weather_data: Dict) -> Dict:
        """
        Formatează datele meteo pentru afișarea în tabel
        """
        temp = weather_data.get("temperature")
        precip_prob = weather_data.get("precipitation_probability")
        precip_amount = weather_data.get("precipitation")
        conditions = weather_data.get("weather_description")
        wind_speed = weather_data.get("wind_speed")
        
        # CORECȚIE: FOLOSIM VARIABILA STOCATĂ PENTRU SIMBOLUL UNITĂȚII
        temperature = f"{temp:.1f}{self.temp_unit_symbol}" if temp is not None else "-"
        
        precipitation = f"{precip_prob:.0f}%" if precip_prob is not None else "-"
        conditions_text = conditions if conditions else "-"
        wind = f"{wind_speed:.1f} km/h" if wind_speed is not None else "-"
        
        return {
            "temperature": temperature,
            "conditions": conditions_text,
            "precipitation": precipitation,
            "wind": wind,
            "precip_amount": precip_amount,
            "precip_prob": precip_prob
        }

    def calculate_statistics(self, enriched_entries: List[Dict]) -> Dict:
        """
        Calculează statistici (medie, min, max, risc de ploaie) pe baza datelor meteo
        """
        temperatures = []
        rainy_periods = 0
        total_precipitation = 0.0
        
        for entry in enriched_entries:
            weather = entry.get("weather")
            if weather:
                temp = weather.get("temperature")
                precip_prob = weather.get("precipitation_probability", 0)
                precip_amount = weather.get("precipitation", 0.0)
                
                if temp is not None:
                    temperatures.append(temp)
                
                if precip_prob > 30 or precip_amount > 0:
                    rainy_periods += 1
                
                total_precipitation += precip_amount
                
        if not temperatures:
            return {
                "avg_temperature": None,
                "min_temperature": None,
                "max_temperature": None,
                "rainy_periods": 0,
                "total_precipitation": 0.0
            }

        return {
            "avg_temperature": sum(temperatures) / len(temperatures),
            "min_temperature": min(temperatures),
            "max_temperature": max(temperatures),
            "rainy_periods": rainy_periods,
            "total_precipitation": total_precipitation
        }

    def detect_rain_conditions(self, weather_data: Dict) -> tuple:
        """
        Detectează condițiile de ploaie pentru colorarea rândurilor
        Returns: (bool is_rainy, str severity)
        """
        precip_prob = weather_data.get("precipitation_probability", 0)
        precip_amount = weather_data.get("precipitation", 0.0)
        
        if precip_prob > 20 or precip_amount > 0.1:
            if precip_prob >= 70 or precip_amount >= 1.0:
                return (True, "heavy")
            elif precip_prob >= 40 or precip_amount >= 0.3:
                return (True, "moderate")
            else:
                return (True, "light")
        return (False, "none")
        
    def get_entries_for_tomorrow(self, enriched_entries: List[Dict]) -> List[Dict]:
        """Filtrează intrările pentru ziua de mâine pentru alerte"""
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        return [entry for entry in enriched_entries if entry.get("date") == tomorrow]