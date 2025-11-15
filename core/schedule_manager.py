import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ScheduleManager:
    """Gestionează încărcarea și validarea orarului personalizat"""
    
    def __init__(self):
        self.schedule = []
        self.days_of_week = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
        
    def load_from_json(self, file_path: str) -> Dict:
        """
        Încarcă orarul din fișier JSON
        
        Format așteptat:
        {
            "schedule": [
                {
                    "day": "Luni",
                    "time": "08:00-10:00",
                    "subject": "Programare",
                    "location": "C309"  # opțional
                }
            ]
        }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validează structura
            if "schedule" not in data:
                raise ValueError("Fișierul JSON trebuie să conțină cheia 'schedule'")
                
            schedule_entries = data["schedule"]
            
            # Validează fiecare intrare
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
        Încarcă orarul din fișier CSV
        
        Format așteptat (cu header):
        day,time,subject,location
        Luni,08:00-10:00,Programare,C309
        """
        try:
            schedule_entries = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                
                for row in csv_reader:
                    # Creează dict din rândul CSV
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
        """Validează o intrare din orar"""
        # Verifică câmpurile obligatorii
        if "day" not in entry or not entry["day"]:
            raise ValueError("Câmpul 'day' lipsește sau este gol")
        if "time" not in entry or not entry["time"]:
            raise ValueError("Câmpul 'time' lipsește sau este gol")
        if "subject" not in entry or not entry["subject"]:
            raise ValueError("Câmpul 'subject' lipsește sau este gol")
            
        # Validează formatul intervalului orar (HH:MM-HH:MM)
        time_str = entry["time"]
        if "-" not in time_str:
            raise ValueError(f"Format invalid pentru timp: {time_str}. Folosește formatul HH:MM-HH:MM")
            
        start_time, end_time = time_str.split("-")
        
        # Validează că sunt formate valide de timp
        try:
            datetime.strptime(start_time.strip(), "%H:%M")
            datetime.strptime(end_time.strip(), "%H:%M")
        except ValueError:
            raise ValueError(f"Format invalid pentru timp: {time_str}")
            
        # Returnează intrarea validată
        return {
            "day": entry["day"].strip(),
            "time": entry["time"].strip(),
            "subject": entry["subject"].strip(),
            "location": entry.get("location", "").strip()
        }
        
    def get_entries_for_day(self, day_name: str) -> List[Dict]:
        """Returnează toate intrările pentru o anumită zi"""
        return [entry for entry in self.schedule if entry["day"].lower() == day_name.lower()]
        
    def get_entries_for_tomorrow(self) -> List[Dict]:
        """Returnează intrările pentru ziua de mâine"""
        tomorrow = datetime.now() + timedelta(days=1)
        day_name = self.days_of_week[tomorrow.weekday()]
        return self.get_entries_for_day(day_name)
        
    def get_current_week_schedule(self) -> List[Dict]:
        """Returnează orarul pentru săptămâna curentă"""
        return self.schedule
        
    def get_time_slots(self) -> List[str]:
        """Returnează o listă cu toate intervalele orare unice din orar"""
        time_slots = set()
        for entry in self.schedule:
            time_slots.add(entry["time"])
        return sorted(list(time_slots))
        
    def export_to_json(self, file_path: str) -> bool:
        """Exportă orarul curent în format JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"schedule": self.schedule}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Eroare la export JSON: {e}")
            return False
            
    def export_to_csv(self, file_path: str) -> bool:
        """Exportă orarul curent în format CSV"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if not self.schedule:
                    return False
                    
                # Determină toate câmpurile posibile
                fieldnames = ["day", "time", "subject", "location"]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in self.schedule:
                    writer.writerow(entry)
                    
            return True
        except Exception as e:
            print(f"Eroare la export CSV: {e}")
            return False