import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from datetime import datetime
from typing import List, Dict, Optional

class WeatherChartWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Inițializează interfața widget-ului"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Titlu
        title = QLabel("📊 Grafice Meteo Interactive")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Container pentru cele două grafice
        charts_layout = QHBoxLayout()
        
        # ==== GRAFICUL TEMPERATURII ====
        temp_container = QWidget()
        temp_layout = QVBoxLayout()
        temp_container.setLayout(temp_layout)
        
        temp_label = QLabel("🌡️ Temperatură")
        temp_label.setStyleSheet("font-weight: bold;")
        temp_layout.addWidget(temp_label)
        
        # Creăm graficul pentru temperatură
        self.temp_plot = pg.PlotWidget()
        self.temp_plot.setBackground('w')  # Fundal alb
        self.temp_plot.setLabel('left', 'Temperatură', units='°C')
        self.temp_plot.setLabel('bottom', 'Timp')
        self.temp_plot.showGrid(x=True, y=True, alpha=0.3)
        self.temp_plot.setMinimumHeight(250)
        
        # Adăugăm o legendă
        self.temp_plot.addLegend()
        
        temp_layout.addWidget(self.temp_plot)
        charts_layout.addWidget(temp_container)
        
        # ==== GRAFICUL PRECIPITAȚIILOR ====
        precip_container = QWidget()
        precip_layout = QVBoxLayout()
        precip_container.setLayout(precip_layout)
        
        precip_label = QLabel("💧 Precipitații")
        precip_label.setStyleSheet("font-weight: bold;")
        precip_layout.addWidget(precip_label)
        
        # Creăm graficul pentru precipitații
        self.precip_plot = pg.PlotWidget()
        self.precip_plot.setBackground('w')
        self.precip_plot.setLabel('left', 'Probabilitate', units='%')
        self.precip_plot.setLabel('bottom', 'Timp')
        self.precip_plot.showGrid(x=True, y=True, alpha=0.3)
        self.precip_plot.setMinimumHeight(250)
        self.precip_plot.addLegend()
        
        precip_layout.addWidget(self.precip_plot)
        charts_layout.addWidget(precip_container)
        
        layout.addLayout(charts_layout)
        
        # Label pentru statistici
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
    def update_charts(self, weather_data: Optional[Dict], schedule_entries: Optional[List[Dict]] = None):
        """
        Actualizează graficele cu noile date meteo
        
        Args:
            weather_data: Datele meteo procesate de la weather_service
            schedule_entries: Opțional - intrările din orar pentru a marca intervalele
        """
        if not weather_data or "hourly" not in weather_data:
            self.clear_charts()
            self.stats_label.setText("Nu există date meteo disponibile pentru grafice.")
            return
            
        hourly_data = weather_data["hourly"]
        
        if not hourly_data:
            self.clear_charts()
            return
            
        # Pregătim datele pentru grafice
        timestamps = []
        temperatures = []
        precip_probabilities = []
        precip_amounts = []
        
        # Timpul de referință (primul timestamp)
        reference_time = None
        
        for entry in hourly_data:
            try:
                # Parsează datetime-ul
                dt = datetime.fromisoformat(entry["datetime"])
                
                if reference_time is None:
                    reference_time = dt
                    
                # Calculează orele relative de la începutul perioadei
                hours_from_start = (dt - reference_time).total_seconds() / 3600
                timestamps.append(hours_from_start)
                
                # Extrage valorile
                temperatures.append(entry.get("temperature", 0))
                precip_probabilities.append(entry.get("precipitation_probability", 0))
                precip_amounts.append(entry.get("precipitation", 0))
                
            except (ValueError, KeyError) as e:
                print(f"Eroare la procesarea intrării meteo: {e}")
                continue
                
        # Actualizăm graficele
        self._plot_temperature(timestamps, temperatures)
        self._plot_precipitation(timestamps, precip_probabilities, precip_amounts)
        
        # Marcăm intervalele din orar dacă sunt furnizate
        if schedule_entries and reference_time:
            self._mark_schedule_intervals(schedule_entries, reference_time)
            
        # Calculăm și afișăm statistici
        self._update_statistics(temperatures, precip_probabilities, precip_amounts)
        
    def _plot_temperature(self, timestamps: List[float], temperatures: List[float]):
        """Desenează graficul temperaturii"""
        self.temp_plot.clear()
        
        if not timestamps or not temperatures:
            return
            
        # Linie principală pentru temperatură
        pen_temp = pg.mkPen(color=(220, 50, 50), width=2)
        self.temp_plot.plot(
            timestamps, 
            temperatures, 
            pen=pen_temp, 
            name='Temperatură',
            symbol='o',
            symbolSize=5,
            symbolBrush=(220, 50, 50)
        )
        
        # Adăugăm o zonă umbrită pentru a arăta variația
        if len(temperatures) > 1:
            avg_temp = sum(temperatures) / len(temperatures)
            fill_brush = pg.mkBrush(220, 50, 50, 50)  # Semi-transparent
            
            # Linie orizontală pentru media
            self.temp_plot.addLine(y=avg_temp, pen=pg.mkPen('r', style=Qt.PenStyle.DashLine, width=1))
            
    def _plot_precipitation(self, timestamps: List[float], probabilities: List[float], amounts: List[float]):
        """Desenează graficul precipitațiilor"""
        self.precip_plot.clear()
        
        if not timestamps:
            return
            
        # Grafic cu bare pentru probabilitatea de precipitații
        if probabilities:
            pen_prob = pg.mkPen(color=(50, 120, 220), width=2)
            self.precip_plot.plot(
                timestamps,
                probabilities,
                pen=pen_prob,
                name='Probabilitate (%)',
                fillLevel=0,
                fillBrush=(50, 120, 220, 100)
            )
            
        # Adăugăm markere pentru precipitațiile efective
        if amounts:
            # Filtrăm doar valorile > 0
            rain_times = []
            rain_amounts = []
            
            for i, amount in enumerate(amounts):
                if amount > 0 and i < len(probabilities):
                    rain_times.append(timestamps[i])
                    rain_amounts.append(probabilities[i])  # Afișăm pe scala probabilității
                    
            if rain_times:
                scatter = pg.ScatterPlotItem(
                    rain_times,
                    rain_amounts,
                    symbol='t',  # Triangle
                    size=15,
                    brush=pg.mkBrush(50, 50, 220, 200),
                    pen=pg.mkPen('b', width=2),
                    name='Precipitații efective'
                )
                self.precip_plot.addItem(scatter)
                
    def _mark_schedule_intervals(self, schedule_entries: List[Dict], reference_time: datetime):
        """
        Marchează intervalele orare din orar pe grafice cu zone colorate
        """
        for entry in schedule_entries:
            if "date" not in entry or "time" not in entry:
                continue
                
            # Extragem intervalul orar
            time_range = entry.get("time", "")
            if "-" not in time_range:
                continue
                
            try:
                start_str, end_str = time_range.split("-")
                entry_date = datetime.fromisoformat(entry["date"])
                
                # Construim datetime-urile complete
                start_time = datetime.strptime(f"{entry_date.date()} {start_str.strip()}", "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(f"{entry_date.date()} {end_str.strip()}", "%Y-%m-%d %H:%M")
                
                # Calculăm pozițiile relative
                start_hours = (start_time - reference_time).total_seconds() / 3600
                end_hours = (end_time - reference_time).total_seconds() / 3600
                
                # Adăugăm regiuni colorate pe ambele grafice
                region_color = (100, 200, 100, 50)  # Verde semi-transparent
                
                region_temp = pg.LinearRegionItem(
                    values=(start_hours, end_hours),
                    brush=region_color,
                    movable=False
                )
                self.temp_plot.addItem(region_temp)
                
                region_precip = pg.LinearRegionItem(
                    values=(start_hours, end_hours),
                    brush=region_color,
                    movable=False
                )
                self.precip_plot.addItem(region_precip)
                
            except (ValueError, KeyError) as e:
                print(f"Eroare la marcarea intervalului: {e}")
                continue
                
    def _update_statistics(self, temperatures: List[float], probabilities: List[float], amounts: List[float]):
        """Calculează și afișează statistici despre date"""
        if not temperatures:
            self.stats_label.setText("Nu există suficiente date pentru statistici.")
            return
            
        # Calculăm statisticile
        avg_temp = sum(temperatures) / len(temperatures)
        min_temp = min(temperatures)
        max_temp = max(temperatures)
        
        max_precip_prob = max(probabilities) if probabilities else 0
        total_precip = sum(amounts) if amounts else 0
        
        # Numărăm perioadele cu risc de ploaie (>30%)
        rainy_periods = sum(1 for p in probabilities if p > 30)
        
        # Formatăm textul statisticilor
        stats_text = f"""
        📊 <b>Statistici:</b> 
        Temperatură medie: {avg_temp:.1f}°C | 
        Min: {min_temp:.1f}°C | 
        Max: {max_temp:.1f}°C | 
        Risc maxim ploaie: {max_precip_prob:.0f}% | 
        Total precipitații: {total_precip:.1f}mm | 
        Perioade cu risc ploaie: {rainy_periods}
        """
        
        self.stats_label.setText(stats_text)
        
    def clear_charts(self):
        """Șterge conținutul graficelor"""
        self.temp_plot.clear()
        self.precip_plot.clear()
        self.stats_label.setText("Graficele vor fi actualizate după încărcarea datelor meteo.")
        
    def export_chart_images(self, temp_path: str, precip_path: str) -> bool:
        """
        Exportă graficele ca imagini PNG
        
        Args:
            temp_path: Calea pentru salvarea graficului de temperatură
            precip_path: Calea pentru salvarea graficului de precipitații
            
        Returns:
            True dacă exportul a reușit
        """
        try:
            # Exportăm graficul de temperatură
            exporter_temp = pg.exporters.ImageExporter(self.temp_plot.plotItem)
            exporter_temp.parameters()['width'] = 800
            exporter_temp.export(temp_path)
            
            # Exportăm graficul de precipitații
            exporter_precip = pg.exporters.ImageExporter(self.precip_plot.plotItem)
            exporter_precip.parameters()['width'] = 800
            exporter_precip.export(precip_path)
            
            return True
        except Exception as e:
            print(f"Eroare la exportul graficelor: {e}")
            return False