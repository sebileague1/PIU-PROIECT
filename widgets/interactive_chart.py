"""
Adaugă acest cod în fișierul care creează graficul de temperatură
(probabil în widgets/weather_chart.py sau similar)
"""

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


class InteractiveTemperatureChart(FigureCanvasQTAgg):
    """Grafic interactiv cu tooltips pentru punctele de temperatură"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#2b2b2b')
        
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Subplot-uri pentru temperatură și precipitații
        self.ax_temp = self.fig.add_subplot(121)
        self.ax_precip = self.fig.add_subplot(122)
        
        # Stilizare grafic
        for ax in [self.ax_temp, self.ax_precip]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, color='#3a3a3a', linestyle='-', linewidth=0.5)
        
        # Date pentru tooltips
        self.temp_data_points = []  # Lista cu (x, y, info_dict)
        self.current_annotation = None
        self.scatter_artists = []
        
        # Setări pentru unitatea de temperatură
        self.temperature_unit = 'celsius'  # sau 'fahrenheit'
        
        # Conectare evenimente mouse
        self.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.mpl_connect('button_press_event', self.on_mouse_click)
        
    def set_temperature_unit(self, unit):
        """Setează unitatea de temperatură ('celsius' sau 'fahrenheit')"""
        self.temperature_unit = unit
        
    def convert_temperature(self, celsius_temp):
        """Convertește temperatura în funcție de unitatea setată"""
        if self.temperature_unit == 'fahrenheit':
            return (celsius_temp * 9/5) + 32
        return celsius_temp
    
    def get_temp_symbol(self):
        """Returnează simbolul unității de temperatură"""
        return '°F' if self.temperature_unit == 'fahrenheit' else '°C'
    
    def update_chart(self, weather_data):
        """
        Actualizează graficul cu date noi
        
        weather_data trebuie să fie o listă de dicționare cu structura:
        [
            {
                'time': '08:00',
                'temperature': 5.2,  # în Celsius (va fi convertit automat)
                'precipitation': 0,
                'precipitation_prob': 10,
                'conditions': 'Ceata',
                'day': 'Luni'
            },
            ...
        ]
        """
        self.ax_temp.clear()
        self.ax_precip.clear()
        self.temp_data_points = []
        self.scatter_artists = []
        
        if not weather_data:
            self.draw()
            return
        
        # Extragere date
        times = list(range(len(weather_data)))
        temps_celsius = [d['temperature'] for d in weather_data]
        temps_display = [self.convert_temperature(t) for t in temps_celsius]
        precip_probs = [d.get('precipitation_prob', 0) for d in weather_data]
        precip_amounts = [d.get('precipitation', 0) for d in weather_data]
        
        # ===== GRAFICUL DE TEMPERATURĂ =====
        
        # Linie de temperatură
        line = self.ax_temp.plot(times, temps_display, color='#ff4444', 
                                 linewidth=2, marker='', zorder=1)[0]
        
        # Puncte roșii interactive (ACESTEA SUNT PUNCTELE IMPORTANTE!)
        scatter = self.ax_temp.scatter(times, temps_display, 
                                      color='#ff4444', 
                                      s=80,  # mărime punct
                                      zorder=2,  # deasupra liniei
                                      edgecolors='#ff6666',
                                      linewidths=1.5,
                                      picker=5)  # 5 pixels tolerance pentru picking
        
        self.scatter_artists.append(scatter)
        
        # Salvare date pentru tooltips
        for i, (time_idx, temp_display, data) in enumerate(zip(times, temps_display, weather_data)):
            self.temp_data_points.append({
                'x': time_idx,
                'y': temp_display,
                'time': data['time'],
                'temperature': temp_display,
                'temp_celsius': data['temperature'],
                'conditions': data.get('conditions', 'N/A'),
                'day': data.get('day', ''),
                'wind': data.get('wind', 'N/A'),
                'index': i
            })
        
        # Bare verzi pentru intervale de timp (exemple)
        self._add_time_bars(self.ax_temp, times)
        
        # Configurare axe temperatură
        self.ax_temp.set_xlabel('Timp', color='white', fontsize=10)
        temp_label = f'Temperatură {self.get_temp_symbol()}'
        self.ax_temp.set_ylabel(temp_label, color='white', fontsize=10)
        self.ax_temp.set_title('🌡️ Temperatură', color='white', fontsize=12, pad=10)
        
        # ===== GRAFICUL DE PRECIPITAȚII =====
        
        # Probabilitate (linie albastră)
        self.ax_precip.plot(times, precip_probs, color='#4488ff', 
                           linewidth=2, marker='o', markersize=4,
                           label='Probabilitate (%)')
        
        # Precipitații efective (bare albastre)
        if any(precip_amounts):
            self.ax_precip.bar(times, precip_amounts, color='#6699ff', 
                              alpha=0.6, width=0.8, label='Precipitații efective')
        
        # Bare verzi pentru intervale de timp
        self._add_time_bars(self.ax_precip, times)
        
        # Configurare axe precipitații
        self.ax_precip.set_xlabel('Timp', color='white', fontsize=10)
        self.ax_precip.set_ylabel('Probabilitate (%)', color='white', fontsize=10)
        self.ax_precip.set_title('💧 Precipitații', color='white', fontsize=12, pad=10)
        self.ax_precip.legend(loc='upper left', framealpha=0.8)
        
        # Ajustare layout
        self.fig.tight_layout()
        self.draw()
    
    def _add_time_bars(self, ax, times):
        """Adaugă bare verzi pentru intervale de timp"""
        if not times:
            return
            
        bar_positions = list(range(0, max(times) + 10, 10))
        for pos in bar_positions:
            ax.axvline(x=pos, color='#2d5c2d', linewidth=8, 
                      alpha=0.3, zorder=0)
    
    def on_mouse_move(self, event):
        """Handler pentru mișcarea mouse-ului - arată tooltip"""
        if event.inaxes != self.ax_temp:
            self._hide_tooltip()
            return
        
        if not self.temp_data_points:
            return
        
        # Găsește cel mai apropiat punct
        closest_point = None
        min_distance = float('inf')
        
        for point in self.temp_data_points:
            # Transformă coordonatele din date space în display space
            display_coords = self.ax_temp.transData.transform([[point['x'], point['y']]])
            mouse_coords = [event.x, event.y]
            
            # Calculează distanța
            distance = np.sqrt((display_coords[0][0] - mouse_coords[0])**2 + 
                             (display_coords[0][1] - mouse_coords[1])**2)
            
            if distance < min_distance and distance < 20:  # 20 pixels radius
                min_distance = distance
                closest_point = point
        
        if closest_point:
            self._show_tooltip(closest_point)
        else:
            self._hide_tooltip()
    
    def _show_tooltip(self, point):
        """Afișează tooltip-ul lângă punct"""
        # Șterge tooltip-ul anterior
        self._hide_tooltip()
        
        # Creează textul tooltip-ului
        temp_symbol = self.get_temp_symbol()
        tooltip_text = (
            f"{point['day']} {point['time']}\n"
            f"🌡️ {point['temperature']:.1f}{temp_symbol}\n"
            f"☁️ {point['conditions']}\n"
            f"💨 {point['wind']}"
        )
        
        # Creează annotation (tooltip)
        self.current_annotation = self.ax_temp.annotate(
            tooltip_text,
            xy=(point['x'], point['y']),
            xytext=(15, 15),  # offset de la punct
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.8',
                facecolor='#1a1a1a',
                edgecolor='#ff4444',
                linewidth=2,
                alpha=0.95
            ),
            color='white',
            fontsize=9,
            fontweight='bold',
            ha='left',
            zorder=1000,
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0.3',
                color='#ff4444',
                linewidth=2
            )
        )
        
        # Evidențiază punctul
        self.highlighted_point = self.ax_temp.scatter(
            [point['x']], [point['y']],
            color='#ffff00',  # galben
            s=150,
            zorder=999,
            edgecolors='#ff4444',
            linewidths=3
        )
        
        self.draw_idle()
    
    def _hide_tooltip(self):
        """Ascunde tooltip-ul"""
        if self.current_annotation:
            self.current_annotation.remove()
            self.current_annotation = None
        
        if hasattr(self, 'highlighted_point') and self.highlighted_point:
            self.highlighted_point.remove()
            self.highlighted_point = None
        
        self.draw_idle()
    
    def on_mouse_click(self, event):
        """Handler pentru click - opțional, poate fixa tooltip-ul"""
        if event.inaxes != self.ax_temp:
            return
        
        # Aici poți adăuga comportament pentru click
        # De exemplu, fixarea tooltip-ului până la următorul click
        pass


# =====================================================
# EXEMPLU DE UTILIZARE ÎN APLICAȚIA TA
# =====================================================

"""
În fișierul principal sau în widget-ul care afișează graficul:

from widgets.interactive_chart import InteractiveTemperatureChart

class WeatherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Creează graficul interactiv
        self.chart = InteractiveTemperatureChart(self, width=10, height=4)
        
        # Adaugă la layout
        layout = QVBoxLayout()
        layout.addWidget(self.chart)
        
        # ...
        
    def update_weather_display(self, weather_data):
        # weather_data trebuie să fie o listă de dicționare
        # Convertește datele tale în formatul corect
        formatted_data = []
        
        for entry in weather_data:
            formatted_data.append({
                'time': entry['interval_orar'].split('-')[0],  # "08:00-10:00" -> "08:00"
                'temperature': entry['temperatura'],  # în Celsius
                'precipitation': entry.get('precipitatii', 0),
                'precipitation_prob': entry.get('probabilitate_ploaie', 0),
                'conditions': entry['conditii'],
                'day': entry['zi'],
                'wind': entry.get('vant', 'N/A')
            })
        
        # Setează unitatea de temperatură
        temp_unit = self.settings.get('temperature_unit', 'celsius')
        self.chart.set_temperature_unit(temp_unit)
        
        # Actualizează graficul
        self.chart.update_chart(formatted_data)
"""


# =====================================================
# CE TREBUIE SĂ MODIFICI ÎN CODUL TĂU EXISTENT:
# =====================================================

"""
1. ÎNLOCUIEȘTE clasa ta actuală de grafic cu InteractiveTemperatureChart

2. ÎN FIȘIERUL CARE CREEAZĂ GRAFICUL (ex: widgets/weather_chart.py):
   
   # În loc de:
   # self.canvas = FigureCanvas(self.figure)
   
   # Folosește:
   self.canvas = InteractiveTemperatureChart(self, width=10, height=4)

3. CÂND ACTUALIZEZI DATELE METEO:
   
   # Convertește datele tale în formatul cerut
   formatted_data = self.format_weather_data_for_chart(self.weather_data)
   
   # Setează unitatea
   self.canvas.set_temperature_unit(self.current_temp_unit)
   
   # Actualizează
   self.canvas.update_chart(formatted_data)

4. CÂND SE SCHIMBĂ UNITATEA DE TEMPERATURĂ (din Settings):
   
   def on_temperature_unit_changed(self, new_unit):
       self.current_temp_unit = new_unit
       self.canvas.set_temperature_unit(new_unit)
       # Re-desenează graficul
       self.refresh_weather_display()
"""