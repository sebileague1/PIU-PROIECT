"""
Widget pentru grafice interactive de temperatură și precipitații
Responsabil: Moscalu Sebastian
"""

import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from datetime import datetime
from typing import List, Dict, Optional

class WeatherChartWidget(QWidget):
    """
    Widget care afișează grafice interactive de temperatură și precipitații.
    """
    
    def __init__(self, data_processor, parent=None):
        super().__init__(parent)
        self.data_processor = data_processor # Referința sigură
        
        self.temp_unit = "°C" 
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMaximumHeight(450)
        
        self.init_ui()
        
    def init_ui(self):
        """Inițializează interfața widget-ului"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title = QLabel("📊 Grafice Meteo Interactive")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: white;")
        layout.addWidget(title)
        
        charts_layout = QHBoxLayout()
        
        # ==== GRAFICUL TEMPERATURII ====
        temp_container = QWidget()
        temp_layout = QVBoxLayout()
        temp_container.setLayout(temp_layout)
        
        temp_label = QLabel("🌡️ Temperatură")
        temp_label.setStyleSheet("font-weight: bold; color: white;")
        temp_layout.addWidget(temp_label)
        
        self.temp_plot = pg.PlotWidget()
        self.temp_plot.setBackground('#2b2b2b')
        self.temp_plot.setLabel('left', 'Temperatură', units='') 
        self.temp_plot.setLabel('bottom', 'Timp')
        self.temp_plot.showGrid(x=True, y=True, alpha=0.3)
        self.temp_plot.getAxis('left').setTextPen('w')
        self.temp_plot.getAxis('bottom').setTextPen('w')
        
        legend_temp = self.temp_plot.addLegend()
        legend_temp.setLabelTextColor('w')
        
        temp_layout.addWidget(self.temp_plot)
        charts_layout.addWidget(temp_container)
        
        # ==== GRAFICUL PRECIPITAȚIILOR ====
        precip_container = QWidget()
        precip_layout = QVBoxLayout()
        precip_container.setLayout(precip_layout)
        
        precip_label = QLabel("💧 Precipitații")
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
        
        # Label pentru statistici
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("padding: 10px; background-color: #3d3d3d; border-radius: 5px; color: #ffffff;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
    def update_charts(self, weather_data: Optional[Dict], schedule_entries: Optional[List[Dict]] = None):
        if not weather_data or "hourly" not in weather_data:
            self.clear_charts()
            self.stats_label.setText("Nu există date meteo disponibile pentru grafice.")
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
                if reference_time is None: reference_time = dt
                timestamps.append((dt - reference_time).total_seconds() / 3600)
                temperatures.append(entry.get("temperature", 0))
                precip_probabilities.append(entry.get("precipitation_probability", 0))
                precip_amounts.append(entry.get("precipitation", 0))
            except Exception: continue
                
        self.temp_unit = self.data_processor.temp_unit_symbol 
        
        self._plot_temperature(timestamps, temperatures)
        self._plot_precipitation(timestamps, precip_probabilities, precip_amounts)
        
        # Transmitem weather_data pentru a putea calcula referința orară corect
        if schedule_entries and weather_data:
            self._mark_schedule_intervals(schedule_entries, weather_data)
            
        self._update_statistics(temperatures, precip_probabilities, precip_amounts, self.data_processor, schedule_entries)
        
    def _plot_temperature(self, timestamps: List[float], temperatures: List[float]):
        self.temp_plot.clear()
        if not timestamps or not temperatures: return
            
        self.temp_plot.setLabel('left', f'Temperatură ({self.temp_unit})', units='')
        
        pen_temp = pg.mkPen(color=(220, 50, 50), width=2)
        self.temp_plot.plot(
            timestamps, 
            temperatures, 
            pen=pen_temp, 
            name=f'Temperatură {self.temp_unit}',
            symbol='o',
            symbolSize=5,
            symbolBrush=(220, 50, 50)
        )
        
        if len(temperatures) > 1:
            avg_temp = sum(temperatures) / len(temperatures)
            self.temp_plot.addLine(y=avg_temp, pen=pg.mkPen('r', style=Qt.PenStyle.DashLine, width=1))
            
    def _plot_precipitation(self, timestamps: List[float], probabilities: List[float], amounts: List[float]):
        self.precip_plot.clear()
        if not timestamps: return
        if probabilities:
            pen_prob = pg.mkPen(color=(50, 120, 220), width=2)
            self.precip_plot.plot(timestamps, probabilities, pen=pen_prob, name='Probabilitate (%)', fillLevel=0, fillBrush=(50, 120, 220, 100))
        if amounts:
            rain_times = [timestamps[i] for i, amount in enumerate(amounts) if amount > 0 and i < len(probabilities)]
            rain_amounts = [probabilities[i] for i, amount in enumerate(amounts) if amount > 0 and i < len(probabilities)]
            if rain_times:
                scatter = pg.ScatterPlotItem(rain_times, rain_amounts, symbol='t', size=15, brush=pg.mkBrush(50, 50, 220, 200), pen=pg.mkPen('b', width=2), name='Precipitații efective')
                self.precip_plot.addItem(scatter)
                
    # === MODIFICARE ÎN SEMNĂTURĂ: Primim weather_data direct ===
    def _mark_schedule_intervals(self, schedule_entries: List[Dict], weather_data: Dict):
        
        if not weather_data or not weather_data.get("hourly"):
            return
            
        try:
            # Calculăm timpul de referință din datele primite de la API
            reference_time = datetime.fromisoformat(weather_data["hourly"][0]["datetime"]).astimezone()
        except Exception:
            return

        for entry in schedule_entries:
            if entry.get("date") is None or "-" not in entry.get("time", ""): continue
            try:
                start_str, end_str = entry["time"].split("-")
                entry_date = datetime.fromisoformat(entry["date"]).date()
                start_time = datetime.strptime(f"{entry_date} {start_str.strip()}", "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(f"{entry_date} {end_str.strip()}", "%Y-%m-%d %H:%M")
                
                # Asigurăm același fus orar
                start_hours = (start_time.replace(tzinfo=reference_time.tzinfo) - reference_time).total_seconds() / 3600
                end_hours = (end_time.replace(tzinfo=reference_time.tzinfo) - reference_time).total_seconds() / 3600
                
                region_color = (100, 200, 100, 50)
                for plot in [self.temp_plot, self.precip_plot]:
                    region = pg.LinearRegionItem(values=(start_hours, end_hours), brush=region_color, movable=False)
                    plot.addItem(region)
            except Exception: continue
                
    # === MODIFICARE ÎN SEMNĂTURĂ: Ștergem referințele la main_window ===
    def _update_statistics(self, temperatures: List[float], probabilities: List[float], amounts: List[float], data_processor, schedule_entries: List[Dict]):
        """Actualizează etichetele de statistici folosind unitatea corectă"""
        if not temperatures:
            self.stats_label.setText("Nu există suficiente date pentru statistici.")
            return
            
        # Folosim schedule_entries primit direct
        stats = data_processor.calculate_statistics(schedule_entries)
        
        unit = stats['unit']
        avg_temp = stats['avg_temperature']
        min_temp = stats['min_temperature'] if 'min_temperature' in stats else '-'
        max_temp = stats['max_temperature'] if 'max_temperature' in stats else '-'
        
        stats_text = f"""
        📊 <b>Statistici:</b> 
        Temperatură medie: {avg_temp:.1f}{unit} | 
        Min: {min_temp:.1f}{unit} | 
        Max: {max_temp:.1f}{unit} | 
        Risc maxim ploaie: {max(probabilities):.0f}% | 
        Total precipitații: {stats['total_precipitation']:.1f}mm | 
        Perioade cu risc ploaie: {stats['rainy_periods']}
        """
        
        self.stats_label.setText(stats_text)
        
    def clear_charts(self):
        self.temp_plot.clear()
        self.precip_plot.clear()
        self.stats_label.setText("Graficele vor fi actualizate după încărcarea datelor meteo.")
        
    def export_chart_images(self, temp_path: str, precip_path: str) -> bool:
        return True