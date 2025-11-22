import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from datetime import datetime
from typing import List, Dict, Optional

class WeatherChartWidget(QWidget):
    """
    Widget care afiseaza grafice interactive pentru:
    - Temperatura pe parcursul zilei/saptamanii
    - Probabilitatea de precipitatii
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
       
        self.setMaximumHeight(450) 
        self.init_ui()
        
    def init_ui(self):
        """Initializeaza interfata widget-ului"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title = QLabel("📊 Grafice Meteo Interactive")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: white;")
        layout.addWidget(title)
        
        charts_layout = QHBoxLayout()
        
        temp_container = QWidget()
        temp_layout = QVBoxLayout()
        temp_container.setLayout(temp_layout)
        
        temp_label = QLabel("🌡️ Temperatura")
        temp_label.setStyleSheet("font-weight: bold; color: white;")
        temp_layout.addWidget(temp_label)
        
        self.temp_plot = pg.PlotWidget()
        self.temp_plot.setBackground('#2b2b2b')
        self.temp_plot.setLabel('left', 'Temperatură', units='°C')
        self.temp_plot.setLabel('bottom', 'Timp')
        self.temp_plot.showGrid(x=True, y=True, alpha=0.3)
        
        self.temp_plot.getAxis('left').setTextPen('w')
        self.temp_plot.getAxis('bottom').setTextPen('w')
        
        legend_temp = self.temp_plot.addLegend()
        legend_temp.setLabelTextColor('w')
       
        temp_layout.addWidget(self.temp_plot)
        charts_layout.addWidget(temp_container)
        
        precip_container = QWidget()
        precip_layout = QVBoxLayout()
        precip_container.setLayout(precip_layout)
        
        precip_label = QLabel("💧 Precipitatii")
        precip_label.setStyleSheet("font-weight: bold; color: white;")
        precip_layout.addWidget(precip_label)
        
        self.precip_plot = pg.PlotWidget()
        self.precip_plot.setBackground('#2b2b2b')
        self.precip_plot.setLabel('left', 'Probabilitate', units='%')
        self.precip_plot.setLabel('bottom', 'Timp')
        self.precip_plot.showGrid(x=True, y=True, alpha=0.3)
        
        self.precip_plot.getAxis('left').setTextPen('w')
        self.precip_plot.getAxis('bottom').setTextPen('w')
        
        legend_precip = self.precip_plot.addLegend()
        legend_precip.setLabelTextColor('w')
        
        precip_layout.addWidget(self.precip_plot)
        charts_layout.addWidget(precip_container)
        
        layout.addLayout(charts_layout)
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("padding: 10px; background-color: #3d3d3d; border-radius: 5px; color: #ffffff;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
    def update_charts(self, weather_data: Optional[Dict], schedule_entries: Optional[List[Dict]] = None):
        """
        Actualizeaza graficele cu noile date meteo
        """
        if not weather_data or "hourly" not in weather_data:
            self.clear_charts()
            self.stats_label.setText("Nu exista date meteo disponibile pentru grafice.")
            return
            
        hourly_data = weather_data["hourly"]
        
        if not hourly_data:
            self.clear_charts()
            return
            
        timestamps = []
        temperatures = []
        precip_probabilities = []
        precip_amounts = []
        
        reference_time = None
        
        for entry in hourly_data:
            try:
                dt = datetime.fromisoformat(entry["datetime"])
                
                if reference_time is None:
                    reference_time = dt
                    
                hours_from_start = (dt - reference_time).total_seconds() / 3600
                timestamps.append(hours_from_start)
                
                temperatures.append(entry.get("temperature", 0))
                precip_probabilities.append(entry.get("precipitation_probability", 0))
                precip_amounts.append(entry.get("precipitation", 0))
                
            except (ValueError, KeyError) as e:
                print(f"Eroare la procesarea intrarii meteo: {e}")
                continue
                
        self._plot_temperature(timestamps, temperatures)
        self._plot_precipitation(timestamps, precip_probabilities, precip_amounts)
        
        if schedule_entries and reference_time:
            self._mark_schedule_intervals(schedule_entries, reference_time)
            
        self._update_statistics(temperatures, precip_probabilities, precip_amounts)
        
    def _plot_temperature(self, timestamps: List[float], temperatures: List[float]):
        """Deseneaza graficul temperaturii"""
        self.temp_plot.clear()
        
        if not timestamps or not temperatures:
            return
            
        pen_temp = pg.mkPen(color=(220, 50, 50), width=2)
        self.temp_plot.plot(
            timestamps, 
            temperatures, 
            pen=pen_temp, 
            name='Temperatura',
            symbol='o',
            symbolSize=5,
            symbolBrush=(220, 50, 50)
        )
        
        if len(temperatures) > 1:
            avg_temp = sum(temperatures) / len(temperatures)
            fill_brush = pg.mkBrush(220, 50, 50, 50)
            
            self.temp_plot.addLine(y=avg_temp, pen=pg.mkPen('r', style=Qt.PenStyle.DashLine, width=1))
            
    def _plot_precipitation(self, timestamps: List[float], probabilities: List[float], amounts: List[float]):
        """Deseneaza graficul precipitatiilor"""
        self.precip_plot.clear()
        
        if not timestamps:
            return
            
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
            
        if amounts:
            rain_times = []
            rain_amounts = []
            
            for i, amount in enumerate(amounts):
                if amount > 0 and i < len(probabilities):
                    rain_times.append(timestamps[i])
                    rain_amounts.append(probabilities[i])
                    
            if rain_times:
                scatter = pg.ScatterPlotItem(
                    rain_times,
                    rain_amounts,
                    symbol='t',
                    size=15,
                    brush=pg.mkBrush(50, 50, 220, 200),
                    pen=pg.mkPen('b', width=2),
                    name='Precipitatii efective'
                )
                self.precip_plot.addItem(scatter)
                
    def _mark_schedule_intervals(self, schedule_entries: List[Dict], reference_time: datetime):
        """
        Marcheaza intervalele orare din orar pe grafice cu zone colorate
        """
        for entry in schedule_entries:
            if "date" not in entry or "time" not in entry:
                continue
                
            time_range = entry.get("time", "")
            if "-" not in time_range:
                continue
                
            try:
                start_str, end_str = time_range.split("-")
                entry_date = datetime.fromisoformat(entry["date"])
                
                start_time = datetime.strptime(f"{entry_date.date()} {start_str.strip()}", "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(f"{entry_date.date()} {end_str.strip()}", "%Y-%m-%d %H:%M")
                
                start_hours = (start_time - reference_time).total_seconds() / 3600
                end_hours = (end_time - reference_time).total_seconds() / 3600
                
                region_color = (100, 200, 100, 50)
                
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
        """Calculeaza si afiseaza statistici despre date"""
        if not temperatures:
            self.stats_label.setText("Nu exista suficiente date pentru statistici.")
            return
            
        avg_temp = sum(temperatures) / len(temperatures)
        min_temp = min(temperatures)
        max_temp = max(temperatures)
        
        max_precip_prob = max(probabilities) if probabilities else 0
        total_precip = sum(amounts) if amounts else 0
        
        rainy_periods = sum(1 for p in probabilities if p > 30)
        
        stats_text = f"""
        📊 <b>Statistici:</b> 
        Temperatură medie: {avg_temp:.1f}°C | 
        Min: {min_temp:.1f}°C | 
        Max: {max_temp:.1f}°C | 
        Risc maxim ploaie: {max_precip_prob:.0f}% | 
        Total precipitatii: {total_precip:.1f}mm | 
        Perioade cu risc ploaie: {rainy_periods}
        """
        
        self.stats_label.setText(stats_text)
        
    def clear_charts(self):
        """Sterge continutul graficelor"""
        self.temp_plot.clear()
        self.precip_plot.clear()
        self.stats_label.setText("Graficele vor fi actualizate dupa incarcarea datelor meteo.")
        
    def export_chart_images(self, temp_path: str, precip_path: str) -> bool:
        """
        Exporta graficele ca imagini PNG
        """
        try:
            exporter_temp = pg.exporters.ImageExporter(self.temp_plot.plotItem)
            exporter_temp.parameters()['width'] = 800
            exporter_temp.export(temp_path)
            
            exporter_precip = pg.exporters.ImageExporter(self.precip_plot.plotItem)
            exporter_precip.parameters()['width'] = 800
            exporter_precip.export(precip_path)
            
            return True
        except Exception as e:
            print(f"Eroare la exportul graficelor: {e}")
            return False