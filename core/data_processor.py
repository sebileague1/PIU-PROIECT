from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class DataProcessor:
    """
    Combina datele din orar cu datele meteo pentru a crea un set complet
    de informatii pentru afisare in tabel
    """
    
    def __init__(self):
        self.day_mapping = {
            "luni": 0,
            "marti": 1,
            "miercuri": 2,
            "joi": 3,
            "vineri": 4,
            "sambata": 5,
            "duminica": 6
        }
        
    def merge_schedule_with_weather(
        self, 
        schedule_entries: List[Dict], 
        weather_data: Dict
    ) -> List[Dict]:
        """
        Combina intrarile din orar cu datele meteo corespunzatoare
        
        Args:
            schedule_entries: Lista cu intrari din orar
            weather_data: Datele meteo procesate de la API
            
        Returns:
            Lista cu intrari imbogatite cu date meteo
        """
        enriched_entries = []
        
        today = datetime.now().date()
        
        for entry in schedule_entries:
            enriched_entry = entry.copy()
            
            entry_date = self._calculate_entry_date(entry["day"], today)
            
            if entry_date:
                weather_info = self._find_weather_for_entry(
                    entry_date,
                    entry["time"],
                    weather_data
                )
                
                enriched_entry["weather"] = weather_info
                enriched_entry["date"] = entry_date.isoformat()
            else:
                enriched_entry["weather"] = None
                enriched_entry["date"] = None
                
            enriched_entries.append(enriched_entry)
            
        return enriched_entries
        
    def _calculate_entry_date(self, day_name: str, reference_date) -> Optional[datetime.date]:
        """
        Calculeaza data exacta pentru o zi din orar bazata pe ziua curenta
        
        Args:
            day_name: Numele zilei (ex: "Luni", "Marti")
            reference_date: Data de referinta (de obicei ziua curenta)
            
        Returns:
            Data calculata sau None daca ziua nu este valida
        """
        day_normalized = day_name.lower().strip()
        
        if day_normalized not in self.day_mapping:
            return None
            
        target_weekday = self.day_mapping[day_normalized]
        current_weekday = reference_date.weekday()
        
        days_ahead = target_weekday - current_weekday
        
        if days_ahead < 0:
            days_ahead += 7
            
        return reference_date + timedelta(days=days_ahead)
        
    def _find_weather_for_entry(
        self, 
        entry_date: datetime.date, 
        time_range: str,
        weather_data: Dict
    ) -> Optional[Dict]:
        """
        Gaseste datele meteo pentru o anumita data si interval orar
        
        Args:
            entry_date: Data pentru care cautam datele meteo
            time_range: Intervalul orar (ex: "08:00-10:00")
            weather_data: Datele meteo complete
            
        Returns:
            Dict cu date meteo sau None daca nu gasim
        """
        if not weather_data or "hourly" not in weather_data:
            return None
            
        if "-" not in time_range:
            return None
            
        start_time_str = time_range.split("-")[0].strip()
        
        try:
            target_datetime = datetime.strptime(
                f"{entry_date} {start_time_str}",
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            return None
            
        closest_weather = None
        min_time_diff = float('inf')
        
        for hourly_entry in weather_data["hourly"]:
            try:
                hourly_datetime = datetime.fromisoformat(hourly_entry["datetime"])
            except (ValueError, KeyError):
                continue
                
            time_diff = abs((hourly_datetime - target_datetime).total_seconds())
            
            if time_diff <= 1800 and time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_weather = hourly_entry
                
        return closest_weather
        
    def get_weather_summary_for_day(
        self,
        date: datetime.date,
        weather_data: Dict
    ) -> Optional[Dict]:
        """
        Obtine un rezumat meteo pentru o zi intreaga
        
        Returns:
            Dict cu temperatura min/max, precipitatii totale, conditii dominante
        """
        if not weather_data or "daily" not in weather_data:
            return None
            
        date_str = date.isoformat()
        
        for daily_entry in weather_data["daily"]:
            if daily_entry.get("date") == date_str:
                return {
                    "temperature_max": daily_entry.get("temperature_max"),
                    "temperature_min": daily_entry.get("temperature_min"),
                    "precipitation_total": daily_entry.get("precipitation_sum"),
                    "weather_description": daily_entry.get("weather_description"),
                    "weather_code": daily_entry.get("weather_code")
                }
                
        return None
        
    def filter_entries_by_date_range(
        self,
        entries: List[Dict],
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[Dict]:
        """
        Filtreaza intrarile pentru un interval de date
        """
        filtered = []
        
        for entry in entries:
            if "date" not in entry or entry["date"] is None:
                continue
                
            try:
                entry_date = datetime.fromisoformat(entry["date"]).date()
                
                if start_date <= entry_date <= end_date:
                    filtered.append(entry)
            except (ValueError, TypeError):
                continue
                
        return filtered
        
    def get_entries_for_tomorrow(self, entries: List[Dict]) -> List[Dict]:
        """
        Filtreaza doar intrarile pentru ziua de maine
        """
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        return self.filter_entries_by_date_range(entries, tomorrow, tomorrow)
        
    def detect_rain_conditions(self, weather_info: Optional[Dict]) -> Tuple[bool, str]:
        """
        Detecteaza daca exista conditii de ploaie
        
        Returns:
            Tuple (is_rainy: bool, severity: str)
            severity poate fi: "none", "light", "moderate", "heavy"
        """
        if not weather_info:
            return False, "none"
            
        precip_prob = weather_info.get("precipitation_probability", 0)
        precip_amount = weather_info.get("precipitation", 0)
        weather_code = weather_info.get("weather_code", 0)

        rain_codes = [61, 63, 65, 80, 81, 82]
        
        if weather_code in rain_codes or precip_amount > 0 or precip_prob > 30:
            if precip_amount > 5 or weather_code in [65, 82]:
                return True, "heavy"
            elif precip_amount > 1 or weather_code in [63, 81]:
                return True, "moderate"
            else:
                return True, "light"
                
        return False, "none"
        
    def format_weather_for_table(self, weather_info: Optional[Dict]) -> Dict[str, str]:
        """
        Formateaza datele meteo pentru afisare in tabel
        
        Returns:
            Dict cu chei: temperature, conditions, precipitation, wind
        """
        if not weather_info:
            return {
                "temperature": "-",
                "conditions": "-",
                "precipitation": "-",
                "wind": "-"
            }
            
        temp = weather_info.get("temperature")
        temp_str = f"{temp:.1f}°C" if temp is not None else "-"

        conditions = weather_info.get("weather_description", "-")

        precip_prob = weather_info.get("precipitation_probability", 0)
        precip_amount = weather_info.get("precipitation", 0)
        
        if precip_amount > 0:
            precip_str = f"{precip_prob}% ({precip_amount:.1f}mm)"
        else:
            precip_str = f"{precip_prob}%"

        wind_speed = weather_info.get("wind_speed", 0)
        wind_str = f"{wind_speed:.1f} km/h" if wind_speed else "-"
        
        return {
            "temperature": temp_str,
            "conditions": conditions,
            "precipitation": precip_str,
            "wind": wind_str
        }
        
    def calculate_statistics(self, entries: List[Dict]) -> Dict:
        """
        Calculeaza statistici pentru un set de intrari cu date meteo
        """
        if not entries:
            return {
                "avg_temperature": None,
                "max_temperature": None,
                "min_temperature": None,
                "rainy_periods": 0,
                "total_precipitation": 0
            }
            
        temperatures = []
        rainy_count = 0
        total_precip = 0
        
        for entry in entries:
            weather = entry.get("weather")
            if not weather:
                continue
                
            temp = weather.get("temperature")
            if temp is not None:
                temperatures.append(temp)
                
            is_rainy, _ = self.detect_rain_conditions(weather)
            if is_rainy:
                rainy_count += 1
                
            precip = weather.get("precipitation", 0)
            total_precip += precip
            
        return {
            "avg_temperature": sum(temperatures) / len(temperatures) if temperatures else None,
            "max_temperature": max(temperatures) if temperatures else None,
            "min_temperature": min(temperatures) if temperatures else None,
            "rainy_periods": rainy_count,
            "total_precipitation": total_precip
        }