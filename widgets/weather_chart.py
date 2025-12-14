import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QPainter, QFont, QCursor
from PyQt6.QtCore import Qt, QPoint, QTimer, QPointF
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np

class HoverLabel(QLabel):
    """Etichetă tooltip simplă și stabilă."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.WindowType.ToolTip | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a; 
                color: white; 
                padding: 12px; 
                border: 3px solid #ff4444;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.hide()

    def show_text(self, pos: QPoint, text: str):
        """Afișează textul la poziția dată."""
        self.setText(text)
        self.adjustSize()
        
        # Poziționare
        offset_x = 25
        offset_y = -self.height() - 20
        
        self.move(pos.x() + offset_x, pos.y() + offset_y)
        self.show()
        self.raise_()

class WeatherChartWidget(QWidget):
    """Widget cu grafice interactive și tooltip-uri stabile."""
    
    def __init__(self, data_processor, parent=None):
        super().__init__(parent)
        self.data_processor = data_processor
        self.temp_unit = "°C" 
        self.full_weather_data = None 
        
        self.temp_data_points = []
        self.precip_data_points = []
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMaximumHeight(450)
        
        self.init_ui()
        
        main_window = self.window()
        self.hover_label = HoverLabel(main_window)
        
        self.mouse_timer = QTimer()
        self.mouse_timer.setInterval(30)
        self.mouse_timer.timeout.connect(self._check_mouse_position)
        self.mouse_timer.start()
        
    def init_ui(self):
        """Inițializează interfața widget-ului"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title = QLabel("📊 Grafice Meteo Interactive")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: white;")
        layout.addWidget(title)
        
        charts_layout = QHBoxLayout()
        
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
        self.temp_plot.setMouseTracking(True)
        
        legend_temp = self.temp_plot.addLegend()
        legend_temp.setLabelTextColor('w')
        
        temp_layout.addWidget(self.temp_plot)
        charts_layout.addWidget(temp_container)
        
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
        self.precip_plot.setMouseTracking(True)
        
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
        if not weather_data or "hourly" not in weather_data:
            self.clear_charts()
            self.stats_label.setText("Nu există date meteo disponibile pentru grafice.")
            return
        
        self.full_weather_data = weather_data 
            
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
        
        if schedule_entries and weather_data:
            self._mark_schedule_intervals(schedule_entries, weather_data)
            
        self._update_statistics(temperatures, precip_probabilities, precip_amounts, self.data_processor, schedule_entries)
        
    def _plot_temperature(self, timestamps: List[float], temperatures: List[float]):
        """Desenează graficul temperaturii și salvează punctele pentru hover."""
        self.temp_plot.clear()
        self.temp_data_points = []
        
        if not timestamps or not temperatures: return
            
        self.temp_plot.setLabel('left', f'Temperatură ({self.temp_unit})', units='')
        
        pen_temp = pg.mkPen(color=(220, 50, 50), width=2)
        line = pg.PlotDataItem(
            timestamps, 
            temperatures, 
            pen=pen_temp, 
            name=f'Temperatură {self.temp_unit}'
        )
        self.temp_plot.addItem(line)
        
        scatter = pg.ScatterPlotItem(
            timestamps,
            temperatures,
            size=10,
            pen=pg.mkPen('w', width=1.5),
            brush=pg.mkBrush(220, 50, 50)
        )
        self.temp_plot.addItem(scatter)
        
        for i, (x, y) in enumerate(zip(timestamps, temperatures)):
            self.temp_data_points.append((x, y, i))
        
        if len(temperatures) > 1:
            avg_temp = sum(temperatures) / len(temperatures)
            self.temp_plot.addLine(y=avg_temp, pen=pg.mkPen('r', style=Qt.PenStyle.DashLine, width=1))
            
    def _plot_precipitation(self, timestamps: List[float], probabilities: List[float], amounts: List[float]):
        """Desenează graficul precipitațiilor și salvează punctele pentru hover."""
        self.precip_plot.clear()
        self.precip_data_points = []
        
        if not timestamps: return
        
        if probabilities:
            line = pg.PlotDataItem(
                timestamps, 
                probabilities, 
                pen=pg.mkPen(color=(50, 120, 220), width=2), 
                name='Probabilitate (%)', 
                fillLevel=0, 
                fillBrush=(50, 120, 220, 100)
            )
            self.precip_plot.addItem(line)
            
            scatter = pg.ScatterPlotItem(
                timestamps,
                probabilities,
                size=10,
                pen=pg.mkPen('w', width=1.5),
                brush=pg.mkBrush(50, 120, 220),
                symbol='d'
            )
            self.precip_plot.addItem(scatter)
            
            for i, (x, y) in enumerate(zip(timestamps, probabilities)):
                self.precip_data_points.append((x, y, i))
            
        if amounts:
            rain_times = [timestamps[i] for i, amount in enumerate(amounts) if amount > 0 and i < len(probabilities)]
            rain_amounts = [probabilities[i] for i, amount in enumerate(amounts) if amount > 0 and i < len(probabilities)]
            if rain_times:
                scatter = pg.ScatterPlotItem(
                    rain_times, 
                    rain_amounts, 
                    symbol='t', 
                    size=15, 
                    brush=pg.mkBrush(50, 50, 220, 200), 
                    pen=pg.mkPen('b', width=2), 
                    name='Precipitații efective'
                )
                self.precip_plot.addItem(scatter)
    
    def _check_mouse_position(self):
        """Verifică constant poziția mouse-ului și afișează/ascunde tooltip-ul."""
        global_pos = QCursor.pos()
        found_point = False
        
        if self.temp_plot.underMouse() and self.temp_data_points:
            try:
                local_pos = self.temp_plot.mapFromGlobal(global_pos)
                
                view_box = self.temp_plot.plotItem.vb
                mouse_point = view_box.mapSceneToView(
                    view_box.mapFromView(view_box.mapToView(local_pos))
                )
                
                closest = self._find_closest_point(
                    mouse_point.x(), 
                    mouse_point.y(), 
                    self.temp_data_points,
                    threshold=3.5 
                )
                
                if closest is not None:
                    self._show_tooltip_for_index(closest, "temp", global_pos)
                    found_point = True
            except Exception as e:
                try:
                    view_range = self.temp_plot.plotItem.vb.viewRange()
                    x_range = view_range[0]
                    plot_width = self.temp_plot.width()
                    
                    x_ratio = local_pos.x() / plot_width
                    approx_x = x_range[0] + (x_range[1] - x_range[0]) * x_ratio
                    
                    closest = self._find_closest_point_x_only(
                        approx_x,
                        self.temp_data_points,
                        threshold=4.0
                    )
                    
                    if closest is not None:
                        self._show_tooltip_for_index(closest, "temp", global_pos)
                        found_point = True
                except:
                    pass
        
        elif self.precip_plot.underMouse() and self.precip_data_points:
            try:
                local_pos = self.precip_plot.mapFromGlobal(global_pos)
                
                view_box = self.precip_plot.plotItem.vb
                mouse_point = view_box.mapSceneToView(
                    view_box.mapFromView(view_box.mapToView(local_pos))
                )
                
                closest = self._find_closest_point(
                    mouse_point.x(), 
                    mouse_point.y(), 
                    self.precip_data_points,
                    threshold=4.5
                )
                
                if closest is not None:
                    self._show_tooltip_for_index(closest, "precip", global_pos)
                    found_point = True
            except Exception as e:
                try:
                    view_range = self.precip_plot.plotItem.vb.viewRange()
                    x_range = view_range[0]
                    plot_width = self.precip_plot.width()
                    
                    x_ratio = local_pos.x() / plot_width
                    approx_x = x_range[0] + (x_range[1] - x_range[0]) * x_ratio
                    
                    closest = self._find_closest_point_x_only(
                        approx_x,
                        self.precip_data_points,
                        threshold=5.0
                    )
                    
                    if closest is not None:
                        self._show_tooltip_for_index(closest, "precip", global_pos)
                        found_point = True
                except:
                    pass
        
        if not found_point:
            self.hover_label.hide()
    
    def _find_closest_point(self, mouse_x, mouse_y, data_points, threshold):
        """Găsește cel mai apropiat punct de mouse folosind doar distanța pe axa X."""
        if not data_points:
            return None
        
        min_distance = float('inf')
        closest_index = None
        
        for x, y, index in data_points:
            distance = abs(x - mouse_x)
            
            if distance < min_distance and distance < threshold:
                min_distance = distance
                closest_index = index
        
        return closest_index
    
    def _find_closest_point_x_only(self, mouse_x, data_points, threshold):
        """Metodă backup - găsește cel mai apropiat punct folosind doar coordonata X."""
        if not data_points:
            return None
        
        min_distance = float('inf')
        closest_index = None
        
        for x, y, index in data_points:
            distance = abs(x - mouse_x)
            
            if distance < min_distance and distance < threshold:
                min_distance = distance
                closest_index = index
        
        return closest_index
    
    def _show_tooltip_for_index(self, index, plot_type, global_pos):
        """Afișează tooltip-ul pentru un index dat."""
        if not self.full_weather_data or not self.full_weather_data.get("hourly"):
            return
        
        hourly_data = self.full_weather_data["hourly"]
        if index >= len(hourly_data):
            return
        
        data = hourly_data[index]
        
        dt_str = data.get("datetime", "")
        try:
            dt = datetime.fromisoformat(dt_str)
            days_ro = {
                'Monday': 'Luni', 'Tuesday': 'Marți', 'Wednesday': 'Miercuri',
                'Thursday': 'Joi', 'Friday': 'Vineri', 'Saturday': 'Sâmbătă', 'Sunday': 'Duminică'
            }
            day_name = days_ro.get(dt.strftime("%A"), dt.strftime("%A"))
            ora_formatata = f"{day_name}, {dt.strftime('%H:00')}"
        except:
            ora_formatata = "N/A"
        
        if plot_type == "temp":
            temp = data.get("temperature", 0)
            cond = data.get("weather_description", "-")
            wind = data.get("wind_speed", 0)
            
            text = (
                f"<div style='text-align: center;'>"
                f"<b style='font-size: 13px;'>{ora_formatata}</b><br><br>"
                f"<span style='font-size: 14px; color: #ff6666;'>🌡️ <b>{temp:.1f}{self.temp_unit}</b></span><br>"
                f"☁️ {cond}<br>"
                f"💨 {wind:.1f} km/h"
                f"</div>"
            )
        
        elif plot_type == "precip":
            prob = data.get("precipitation_probability", 0)
            amt = data.get("precipitation", 0)
            wind = data.get("wind_speed", 0)
            
            text = (
                f"<div style='text-align: center;'>"
                f"<b style='font-size: 13px;'>{ora_formatata}</b><br><br>"
                f"<span style='font-size: 14px; color: #66aaff;'>💧 <b>{prob:.0f}%</b></span><br>"
                f"🌧️ {amt:.1f} mm<br>"
                f"💨 {wind:.1f} km/h"
                f"</div>"
            )
        
        self.hover_label.show_text(global_pos, text)
    
    def _mark_schedule_intervals(self, schedule_entries: List[Dict], weather_data: Dict):
        if not weather_data or not weather_data.get("hourly"):
            return
            
        try:
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
                
                start_hours = (start_time.replace(tzinfo=reference_time.tzinfo) - reference_time).total_seconds() / 3600
                end_hours = (end_time.replace(tzinfo=reference_time.tzinfo) - reference_time).total_seconds() / 3600
                
                region_color = (100, 200, 100, 50)
                for plot in [self.temp_plot, self.precip_plot]:
                    region = pg.LinearRegionItem(values=(start_hours, end_hours), brush=region_color, movable=False)
                    plot.addItem(region)
            except Exception: continue
                
    def _update_statistics(self, temperatures: List[float], probabilities: List[float], amounts: List[float], data_processor, schedule_entries: List[Dict]):
        if not temperatures:
            self.stats_label.setText("Nu există suficiente date pentru statistici.")
            return
            
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
        self.temp_data_points = []
        self.precip_data_points = []
        self.hover_label.hide()
        self.stats_label.setText("Graficele vor fi actualizate după încărcarea datelor meteo.")
        
    def export_chart_images(self, temp_path: str, precip_path: str) -> bool:
        return True
    
    def closeEvent(self, event):
        """Oprește timer-ul când widget-ul se închide."""
        if hasattr(self, 'mouse_timer'):
            self.mouse_timer.stop()
        super().closeEvent(event)