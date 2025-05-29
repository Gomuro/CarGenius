from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QPainterPath
import random # random is used in X-axis label generation, keep if that specific label format is desired

# Custom Widget for drawing a time-series line graph
class TimeSeriesLineGraphWidget(QWidget):
    def __init__(self, time_series_data=None, title="", parent=None):
        super().__init__(parent)
        # data = [(0, price1), (1, price2), ..., (n, price_n+1)] where x is month index
        self.series_data = time_series_data if time_series_data is not None else [] 
        self.graph_title = title
        self.setMinimumHeight(250)
        self.setMinimumWidth(400)

        # Style attributes for dark theme
        self.background_color = QColor("#2D2D2D") # Dark background
        self.line_color = QColor("#5D94FB") # A brighter blue for dark theme (similar to chat bubbles)
        self.axis_color = QColor("#6A6A6A")   # Medium gray for axes
        self.label_color = QColor("#E0E0E0")  # Light gray for text labels
        self.title_color = QColor("#5D94FB")  # Brighter blue for legend title
        self.grid_line_color = QColor("#3E3E3E") # Darker gray for subtle grid lines

        self.padding_top = 40 # Space for title/legend
        self.padding_bottom = 50 # Space for X-axis labels
        self.padding_left = 70  # Space for Y-axis labels
        self.padding_right = 20

    def setData(self, data, title):
        self.series_data = data if data is not None else []
        self.graph_title = title
        self.update() 

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.background_color)

        if not self.series_data or len(self.series_data) < 2:
            # Draw title even if no data
            painter.setPen(self.label_color)
            painter.setFont(QFont("Segoe UI", 10))
            if not self.series_data:
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.graph_title} - No data available")
            else:
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.graph_title} - Not enough data to plot line")
            return

        # Chart area calculation
        chart_width = self.width() - self.padding_left - self.padding_right
        chart_height = self.height() - self.padding_top - self.padding_bottom
        chart_origin_x = self.padding_left
        chart_origin_y = self.padding_top

        if chart_width <= 0 or chart_height <= 0:
            return

        # Data properties
        prices = [p for _, p in self.series_data]
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        if price_range == 0: price_range = 1 # Avoid division by zero

        num_points = len(self.series_data)
        x_step = chart_width / (num_points - 1) if num_points > 1 else chart_width

        # --- Draw Legend/Title ---
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(self.title_color)
        legend_x = self.padding_left
        legend_y = self.padding_top - 25 # Above the graph
        painter.drawEllipse(QPointF(legend_x, legend_y), 4, 4)
        painter.drawText(QPointF(legend_x + 10, legend_y + 4), self.graph_title)
        
        # --- Draw Y-axis and Grid Lines ---
        num_y_ticks = 5 # e.g., $25k, $26k, ...
        painter.setFont(QFont("Segoe UI", 8))
        fm = QFontMetrics(painter.font())

        for i in range(num_y_ticks + 1):
            y_pos = chart_origin_y + chart_height - (i * chart_height / num_y_ticks)
            price_label_val = min_price + (i * price_range / num_y_ticks)
            
            # Grid line
            painter.setPen(QPen(self.grid_line_color, 1, Qt.PenStyle.SolidLine))
            painter.drawLine(chart_origin_x, int(y_pos), chart_origin_x + chart_width, int(y_pos))

            # Y-axis label
            painter.setPen(self.label_color)
            label_text = f"${price_label_val/1000:.0f}k"
            text_width = fm.horizontalAdvance(label_text)
            painter.drawText(QPointF(chart_origin_x - text_width - 7, y_pos + fm.height() / 4), label_text)

        # --- Draw X-axis and Labels ---
        mock_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        painter.setPen(self.label_color)
        for i in range(num_points):
            x_pos = chart_origin_x + i * x_step
            month_label = mock_months[self.series_data[i][0] % len(mock_months)] # Use month index for label
            # The random.randint here makes the date label less predictable if desired, but can be simplified
            date_label = f"{month_label} {random.randint(1,28)} S{i}" 
            label_width = fm.horizontalAdvance(date_label)
            painter.drawText(QPointF(x_pos - label_width / 2, chart_origin_y + chart_height + fm.height() + 5), date_label)

        # --- Draw Price Line ---
        path = QPainterPath()
        first_point = self.series_data[0]
        start_x = chart_origin_x
        start_y = chart_origin_y + chart_height - ((first_point[1] - min_price) / price_range * chart_height)
        path.moveTo(start_x, start_y)

        for i in range(1, num_points):
            x_val_idx, y_val_price = self.series_data[i]
            px = chart_origin_x + i * x_step
            py = chart_origin_y + chart_height - ((y_val_price - min_price) / price_range * chart_height)
            path.lineTo(px, py)
        
        painter.setPen(QPen(self.line_color, 2)) # Thicker line
        painter.drawPath(path) 