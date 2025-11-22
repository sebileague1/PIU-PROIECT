import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ScheduleManager:
    """Gestioneaza incarcarea si validarea orarului personalizat"""
    
    def __init__(self):
        self.schedule = []
        self.days_of_week = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
        
    def load_from_json(self, file_path: str) -> Dict:
        """
        Incarca orarul din fisier JSON
        
        Format asteptat:
        {
            "schedule": [
                {
                    "day": "Luni",
                    "time": "08:00-10:00",
                    "subject": "Programare",
                    "location": "C309"  # optional
                }
            ]
        }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "schedule" not in data:
                raise ValueError("Fisierul JSON trebuie sa contina cheia 'schedule'")
                
            schedule_entries = data["schedule"]
            
            validated_schedule = []
            for entry in schedule_entries:
                validated_entry = self._validate_entry(entry)
                validated_schedule.append(validated_entry)
                
            self.schedule = validated_schedule
            return {"status": "success", "schedule": validated_schedule}
            
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Eroare la citirea JSON: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Eroare: {str(e)}"}
            
    def load_from_csv(self, file_path: str) -> Dict:
        """
        Incarca orarul din fisier CSV
        
        Format asteptat (cu header):
        day,time,subject,location
        Luni,08:00-10:00,Programare,C309
        """
        try:
            schedule_entries = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                
                for row in csv_reader:
                    entry = {
                        "day": row.get("day", "").strip(),
                        "time": row.get("time", "").strip(),
                        "subject": row.get("subject", "").strip(),
                        "location": row.get("location", "").strip() if "location" in row else ""
                    }
                    
                    validated_entry = self._validate_entry(entry)
                    schedule_entries.append(validated_entry)
                    
            self.schedule = schedule_entries
            return {"status": "success", "schedule": schedule_entries}
            
        except Exception as e:
            return {"status": "error", "message": f"Eroare la citirea CSV: {str(e)}"}
            
    def _validate_entry(self, entry: Dict) -> Dict:
        """Valideaza o intrare din orar"""
        if "day" not in entry or not entry["day"]:
            raise ValueError("Campul 'day' lipseste sau este gol")
        if "time" not in entry or not entry["time"]:
            raise ValueError("Campul 'time' lipseste sau este gol")
        if "subject" not in entry or not entry["subject"]:
            raise ValueError("Campul 'subject' lipseste sau este gol")
            
        time_str = entry["time"]
        if "-" not in time_str:
            raise ValueError(f"Format invalid pentru timp: {time_str}. Foloseste formatul HH:MM-HH:MM")
            
        start_time, end_time = time_str.split("-")
        
        try:
            datetime.strptime(start_time.strip(), "%H:%M")
            datetime.strptime(end_time.strip(), "%H:%M")
        except ValueError:
            raise ValueError(f"Format invalid pentru timp: {time_str}")
            
        return {
            "day": entry["day"].strip(),
            "time": entry["time"].strip(),
            "subject": entry["subject"].strip(),
            "location": entry.get("location", "").strip()
        }
        
    def get_entries_for_day(self, day_name: str) -> List[Dict]:
        """Returneaza toate intrarile pentru o anumita zi"""
        return [entry for entry in self.schedule if entry["day"].lower() == day_name.lower()]
        
    def get_entries_for_tomorrow(self) -> List[Dict]:
        """Returneaza intrarile pentru ziua de maine"""
        tomorrow = datetime.now() + timedelta(days=1)
        day_name = self.days_of_week[tomorrow.weekday()]
        return self.get_entries_for_day(day_name)
        
    def get_current_week_schedule(self) -> List[Dict]:
        """Returneaza orarul pentru saptamana curenta"""
        return self.schedule
        
    def get_time_slots(self) -> List[str]:
        """Returneaza o lista cu toate intervalele orare unice din orar"""
        time_slots = set()
        for entry in self.schedule:
            time_slots.add(entry["time"])
        return sorted(list(time_slots))
        
    def export_to_json(self, file_path: str) -> bool:
        """Exporta orarul curent in format JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"schedule": self.schedule}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Eroare la export JSON: {e}")
            return False
            
    def export_to_csv(self, file_path: str) -> bool:
        """Exporta orarul curent in format CSV"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if not self.schedule:
                    return False
                    
                fieldnames = ["day", "time", "subject", "location"]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in self.schedule:
                    writer.writerow(entry)
                    
            return True
        except Exception as e:
            print(f"Eroare la export CSV: {e}")
            return False