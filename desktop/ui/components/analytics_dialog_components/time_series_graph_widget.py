from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QToolTip
from PyQt6.QtCore import Qt, QPointF, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QFontMetrics
from datetime import datetime
import math

# Custom Widget for drawing a time-series line graph
class TimeSeriesLineGraphWidget(QFrame):
    def __init__(self, time_series_data=None, title="", parent=None):
        super().__init__(parent)
        # data = [(0, price1), (1, price2), ..., (n, price_n+1)] where x is month index
        self.series_data = time_series_data if time_series_data is not None else [] 
        self.graph_title = title
        self.setMinimumHeight(280)
        self.setMinimumWidth(450)
        self.setObjectName("graph_widget")
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Store calculated data points for interaction
        self.data_points = []  # List of (x, y, data_index) for each rendered point
        self.hovered_point = None  # Index of currently hovered point
        
        # Animation properties
        self._animation_progress = 1.0  # Start with full graph visible
        self._animation_started = False
        self.animation = QPropertyAnimation(self, b"animationProgress")
        self.animation.setDuration(1500)  # 1.5 seconds animation
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self._on_animation_finished)

        # Style attributes for dark theme
        self.background_color = QColor("#2D2D2D") # Dark background
        self.line_color = QColor("#5D94FB") # A brighter blue for dark theme (similar to chat bubbles)
        self.axis_color = QColor("#6A6A6A")   # Medium gray for axes
        self.label_color = QColor("#E0E0E0")  # Light gray for text labels
        self.title_color = QColor("#5D94FB")  # Brighter blue for legend title
        self.grid_line_color = QColor("#3E3E3E") # Darker gray for subtle grid lines
        self.point_color = QColor("#5D94FB")  # Color for data points
        self.point_hover_color = QColor("#7DA6FD")  # Lighter blue for hovered points

        self.padding_top = 40 # Space for title/legend
        self.padding_bottom = 50 # Space for X-axis labels
        self.padding_left = 80  # Increased space for Y-axis price labels
        self.padding_right = 20

    @pyqtProperty(float)
    def animationProgress(self):
        return self._animation_progress
    
    @animationProgress.setter
    def animationProgress(self, value):
        self._animation_progress = value
        self.update()  # Trigger repaint
    
    def setData(self, data, title):
        self.series_data = data if data is not None else []
        self.graph_title = title
        # Reset animation state when new data is set
        self._animation_started = False
        self._animation_progress = 1.0  # Show full graph by default
        self.update()  # Update display
    
    def _start_animation(self):
        """Start the drawing animation."""
        if not self.series_data:
            print(f"[GraphWidget] Cannot start animation - no data for {self.graph_title}")
            return
            
        if self._animation_started:
            print(f"[GraphWidget] Animation already started for {self.graph_title}")
            return
            
        if self.animation.state() == QPropertyAnimation.State.Running:
            print(f"[GraphWidget] Animation already running for {self.graph_title}")
            return
            
        print(f"[GraphWidget] Starting animation for {self.graph_title}")
        # Mark as started and reset progress for animation
        self._animation_started = True
        self.animation.stop()  # Ensure clean state
        self._animation_progress = 0.0  # Reset for animation
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
    
    def _on_animation_finished(self):
        """Called when animation completes."""
        print(f"[GraphWidget] Animation finished for {self.graph_title}")
        self._animation_progress = 1.0
        self._animation_started = True  # Mark as completed
        self.update() 

    def paintEvent(self, event):
        super().paintEvent(event)
        
        if not self.series_data:
            self._draw_empty_state()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # --- Draw Title ---
        if self.graph_title:
            painter.setPen(self.title_color)
            title_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
            painter.setFont(title_font)
            
            title_rect = QRectF(self.padding_left, 0, self.width() - self.padding_left - self.padding_right, self.padding_top)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.graph_title)

        # Chart dimensions
        chart_width = self.width() - self.padding_left - self.padding_right
        chart_height = self.height() - self.padding_top - self.padding_bottom
        chart_origin_x = self.padding_left
        chart_origin_y = self.padding_top
        
        if chart_width <= 0 or chart_height <= 0:
            return
        
        # Data properties
        prices = [p for _, p, _ in self.series_data]
        min_price, max_price = min(prices), max(prices)
        
        # --- Draw Y-axis and get scaling factors ---
        min_price_for_scaling, max_price_for_scaling = self._draw_y_axis(painter, min_price, max_price, chart_origin_x, chart_origin_y, chart_height)
        price_range_for_scaling = max_price_for_scaling - min_price_for_scaling
        if price_range_for_scaling == 0: price_range_for_scaling = 1

        # --- Draw X-axis ---
        self._draw_x_axis(painter, chart_origin_x, chart_origin_y, chart_width, chart_height)
        
        # --- Draw Price Line with Animation ---
        num_points = len(self.series_data)
        if num_points < 2: return
            
        x_step = chart_width / (num_points - 1)
        
        # Calculate how many points to draw based on animation progress
        animated_points = max(1, int(num_points * self._animation_progress))
        
        if animated_points >= 2:
            path = QPainterPath()
            # Get starting point
            _, start_price, _ = self.series_data[0]
            start_y = chart_origin_y + chart_height - ((start_price - min_price_for_scaling) / price_range_for_scaling * chart_height)
            path.moveTo(chart_origin_x, start_y)
            
            # Add subsequent points up to animation progress
            for i in range(1, min(animated_points, num_points)):
                _, y_val_price, _ = self.series_data[i]
                px = chart_origin_x + i * x_step
                py = chart_origin_y + chart_height - ((y_val_price - min_price_for_scaling) / price_range_for_scaling * chart_height)
                path.lineTo(px, py)
            
            # If we're between two points, interpolate the final point for smooth animation
            if animated_points < num_points and self._animation_progress < 1.0:
                current_point_index = int(num_points * self._animation_progress)
                next_point_index = min(current_point_index + 1, num_points - 1)
                
                if current_point_index != next_point_index:
                    # Interpolate between current and next point
                    progress_within_segment = (num_points * self._animation_progress) - current_point_index
                    
                    _, current_price, _ = self.series_data[current_point_index]
                    _, next_price, _ = self.series_data[next_point_index]
                    
                    interpolated_price = current_price + (next_price - current_price) * progress_within_segment
                    interpolated_x = chart_origin_x + (current_point_index + progress_within_segment) * x_step
                    interpolated_y = chart_origin_y + chart_height - ((interpolated_price - min_price_for_scaling) / price_range_for_scaling * chart_height)
                    
                    path.lineTo(interpolated_x, interpolated_y)
            
            painter.setPen(QPen(self.line_color, 2))
            painter.drawPath(path)
        
        # --- Draw Data Points and Hover Effects (Animated) ---
        points_to_draw = min(animated_points, num_points)
        for i in range(points_to_draw):
            _, y_val_price, _ = self.series_data[i]
            px = chart_origin_x + i * x_step
            py = chart_origin_y + chart_height - ((y_val_price - min_price_for_scaling) / price_range_for_scaling * chart_height)
            
            # Calculate opacity for smooth point appearance
            point_opacity = 1.0
            if i == points_to_draw - 1 and self._animation_progress < 1.0:
                # Last point during animation - fade it in
                progress_within_segment = (num_points * self._animation_progress) - i
                point_opacity = min(1.0, progress_within_segment)
            
            if self.hovered_point == i and i < animated_points:
                # Draw hover effects (larger circle, crosshairs)
                hover_color = QColor(self.point_hover_color)
                hover_color.setAlphaF(point_opacity)
                
                painter.setPen(QPen(hover_color, 2))
                painter.setBrush(hover_color)
                painter.drawEllipse(QPointF(px, py), 6, 6)
                
                painter.setPen(QPen(hover_color, 1, Qt.PenStyle.DashLine))
                painter.drawLine(int(px), int(chart_origin_y), int(px), int(chart_origin_y + chart_height)) # Vertical crosshair
                painter.drawLine(int(chart_origin_x), int(py), int(chart_origin_x + chart_width), int(py)) # Horizontal crosshair
                
                if point_opacity > 0.5:  # Only show tooltip if point is mostly visible
                    self._show_point_tooltip(i, px, py, y_val_price)
            else:
                # Draw standard point with opacity
                point_color = QColor(self.point_color)
                point_color.setAlphaF(point_opacity)
                
                painter.setPen(QPen(point_color, 1))
                painter.setBrush(point_color)
                
                # Add pulsing effect to the currently drawing point
                if i == points_to_draw - 1 and self._animation_progress < 1.0 and point_opacity > 0.3:
                    # Draw a larger, semi-transparent circle for pulse effect
                    pulse_color = QColor(self.point_color)
                    pulse_alpha = 0.3 * point_opacity * (1.0 - (self._animation_progress - int(self._animation_progress)))
                    pulse_color.setAlphaF(pulse_alpha)
                    
                    painter.setPen(QPen(pulse_color, 1))
                    painter.setBrush(pulse_color)
                    painter.drawEllipse(QPointF(px, py), 6, 6)
                    
                    # Draw the main point on top
                    painter.setPen(QPen(point_color, 1))
                    painter.setBrush(point_color)
                
                painter.drawEllipse(QPointF(px, py), 3, 3)

    def _draw_x_axis(self, painter, chart_origin_x, chart_origin_y, chart_width, chart_height):
        # Draw X-axis line
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawLine(chart_origin_x, chart_origin_y + chart_height, chart_origin_x + chart_width, chart_origin_y + chart_height)
        
        # Draw X-axis labels
        num_points = len(self.series_data)
        if num_points == 0: return

        num_labels = min(num_points, 8)  # Max 8 labels
        indices = [int(i * (num_points - 1) / (num_labels - 1)) for i in range(num_labels)] if num_labels > 1 else [0]
        
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(self.label_color)
        
        for i in indices:
            x_pos = chart_origin_x + (i / (num_points - 1) if num_points > 1 else 0) * chart_width
            
            # Get timestamp and format the date label
            data_point = self.series_data[i]
            if len(data_point) == 3 and data_point[2] > 0:
                timestamp = data_point[2]
                actual_date = datetime.fromtimestamp(timestamp / 1000)
                
                total_days = (datetime.now() - actual_date).days
                if total_days < 90:
                    date_label = actual_date.strftime("%b %d") # "Jan 30"
                elif total_days < 365 * 2:
                    date_label = actual_date.strftime("%b '%y") # "Jan '25"
                else:
                    date_label = actual_date.strftime("%Y") # "2025"
            else:
                # Fallback for old data format
                date_label = f"{i+1}"
            
            label_width = painter.fontMetrics().horizontalAdvance(date_label)
            painter.drawText(QPointF(x_pos - label_width / 2, chart_origin_y + chart_height + painter.fontMetrics().height() + 5), date_label)

    def _draw_y_axis(self, painter, min_price, max_price, chart_origin_x, chart_origin_y, chart_height):
        """Draw Y-axis with clean, non-repetitive labels"""
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawLine(chart_origin_x, chart_origin_y, chart_origin_x, chart_origin_y + chart_height)

        painter.setFont(QFont("Segoe UI", 8))
        font_metrics = painter.fontMetrics()

        # Generate clean price labels
        num_labels = 5
        if max_price == min_price:
            # Handle case where all prices are the same
            labels = [min_price]
        else:
            # Calculate a "nice" interval between labels
            price_range = max_price - min_price
            raw_interval = price_range / (num_labels - 1)
            
            # Find a nice, round interval (e.g., 100, 500, 1000)
            power = 10**math.floor(math.log10(raw_interval))
            nice_fraction = raw_interval / power
            
            if nice_fraction < 1.5:
                interval = 1 * power
            elif nice_fraction < 3:
                interval = 2 * power
            elif nice_fraction < 7:
                interval = 5 * power
            else:
                interval = 10 * power
                
            start_price = math.floor(min_price / interval) * interval
            end_price = math.ceil(max_price / interval) * interval
            
            labels = []
            current = start_price
            while current <= end_price:
                labels.append(current)
                current += interval
                # Safety break to prevent infinite loops on floating point errors
                if len(labels) > 20: break 
        
        if not labels: labels = [min_price]

        # Update min/max based on nice labels to ensure graph aligns perfectly
        min_price_for_scaling = labels[0]
        max_price_for_scaling = labels[-1]
        price_range_for_scaling = max_price_for_scaling - min_price_for_scaling
        if price_range_for_scaling == 0: price_range_for_scaling = 1

        for price_label in labels:
            y = chart_origin_y + chart_height - ((price_label - min_price_for_scaling) / price_range_for_scaling * chart_height)
            
            # Draw grid line
            painter.setPen(QPen(self.grid_line_color, 1))
            painter.drawLine(chart_origin_x, int(y), chart_origin_x + (self.width() - self.padding_left - self.padding_right), int(y))
            
            # Draw price label on the left side
            painter.setPen(QPen(self.label_color, 1))
            label_text = f"€{price_label:,.0f}"
            label_width = font_metrics.horizontalAdvance(label_text)
            label_height = font_metrics.height()
            
            # Position label to the left of the Y-axis line with some padding
            label_x = chart_origin_x - label_width - 8
            label_y = y + label_height / 4  # Center vertically on the grid line
            
            painter.drawText(QPointF(label_x, label_y), label_text)
            
        # Return the adjusted scale for drawing the main graph line
        return min_price_for_scaling, max_price_for_scaling



    def _draw_empty_state(self):
        """Draw empty state when no data is available"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.background_color)
        painter.setPen(self.label_color)
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.graph_title} - No data available")

    def _show_point_tooltip(self, index, px, py, price):
        """Show tooltip with price and time information"""
        # Get timestamp if available
        data_point = self.series_data[index]
        if len(data_point) == 3:
            # We have timestamp data
            _, _, timestamp = data_point
            if timestamp > 0:
                # Convert from milliseconds to seconds for datetime
                actual_date = datetime.fromtimestamp(timestamp / 1000)
                time_label = actual_date.strftime("%b %d, %Y")  # Format: "Jan 30, 2025"
            else:
                time_label = "Unknown date"
        else:
            # Fallback to relative time calculation
            if len(self.series_data) <= 12:
                mock_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                time_label = mock_months[index % len(mock_months)]
            else:
                weeks_ago = len(self.series_data) - index - 1
                if weeks_ago == 0:
                    time_label = "Current"
                elif weeks_ago < 4:
                    time_label = f"{weeks_ago} weeks ago"
                elif weeks_ago < 52:
                    time_label = f"{weeks_ago//4} months ago"
                else:
                    time_label = f"{weeks_ago//52} years ago"
        
        tooltip_text = f"Price: €{price:,.0f}\nDate: {time_label}\nData point: {index + 1}/{len(self.series_data)}"
        
        # Show tooltip near the cursor
        global_pos = self.mapToGlobal(QPointF(px + 10, py - 10).toPoint())
        QToolTip.showText(global_pos, tooltip_text, self)
    
    def mouseMoveEvent(self, event):
        if not self.series_data:
            return

        # Chart dimensions (same as paintEvent)
        chart_width = self.width() - self.padding_left - self.padding_right
        chart_height = self.height() - self.padding_top - self.padding_bottom
        chart_origin_x = self.padding_left
        chart_origin_y = self.padding_top
        
        if chart_width <= 0 or chart_height <= 0:
            return
        
        # Get data properties and scaling (same as paintEvent)
        prices = [p for _, p, _ in self.series_data]
        min_price, max_price = min(prices), max(prices)
        
        # Calculate the same scaling factors as the Y-axis drawing
        num_labels = 5
        if max_price == min_price:
            min_price_for_scaling = max_price_for_scaling = min_price
        else:
            price_range = max_price - min_price
            raw_interval = price_range / (num_labels - 1)
            
            # Find a nice, round interval (same logic as _draw_y_axis)
            power = 10**math.floor(math.log10(raw_interval))
            nice_fraction = raw_interval / power
            
            if nice_fraction < 1.5:
                interval = 1 * power
            elif nice_fraction < 3:
                interval = 2 * power
            elif nice_fraction < 7:
                interval = 5 * power
            else:
                interval = 10 * power
                
            min_price_for_scaling = math.floor(min_price / interval) * interval
            max_price_for_scaling = math.ceil(max_price / interval) * interval
        
        price_range_for_scaling = max_price_for_scaling - min_price_for_scaling
        if price_range_for_scaling == 0: price_range_for_scaling = 1

        num_points = len(self.series_data)
        x_step = chart_width / (num_points - 1) if num_points > 1 else chart_width

        # Check for hover on data points (only on animated/visible points)
        mouse_x = event.position().x()
        mouse_y = event.position().y()
        
        closest_point = -1
        min_distance = float('inf')
        
        # Only check points that have been animated/drawn
        animated_points = max(1, int(num_points * self._animation_progress))
        points_to_check = min(animated_points, num_points)
        
        for i in range(points_to_check):
            _, y_val_price, _ = self.series_data[i]
            px = chart_origin_x + i * x_step
            py = chart_origin_y + chart_height - ((y_val_price - min_price_for_scaling) / price_range_for_scaling * chart_height)
            
            distance = math.sqrt((mouse_x - px)**2 + (mouse_y - py)**2)
            if distance < 30 and distance < min_distance:  # 30 pixel hover radius
                min_distance = distance
                closest_point = i

        if closest_point != self.hovered_point:
            self.hovered_point = closest_point
            self.update()  # Trigger repaint
    
    def mousePressEvent(self, event):
        """Handle mouse click on data points"""
        super().mousePressEvent(event)
        
        if event.button() == Qt.MouseButton.LeftButton and self.hovered_point is not None:
            # Could add additional click functionality here
            # For now, just maintain the hover state
            pass
    
    def leaveEvent(self, event):
        """Hide tooltip and reset hover state when mouse leaves widget"""
        if self.hovered_point is not None:
            self.hovered_point = None
            self.update()
            QToolTip.hideText()
        super().leaveEvent(event)
    
    def showEvent(self, event):
        """Start animation when widget becomes visible"""
        super().showEvent(event)
        # Don't auto-start animation on show to prevent glitches
        # Animation will be started explicitly by the parent
    
    def startDrawingAnimation(self):
        """Public method to manually start the drawing animation"""
        print(f"[GraphWidget] startDrawingAnimation called for {self.graph_title}")
        if self.series_data:
            # Reset animation state to allow restart
            print(f"[GraphWidget] Resetting animation state for {self.graph_title}")
            self._animation_started = False
            self._start_animation()
        else:
            print(f"[GraphWidget] No data available for animation: {self.graph_title}")
    
    def resetAnimation(self):
        """Reset animation state without starting"""
        self.animation.stop()
        self._animation_started = False
        self._animation_progress = 1.0  # Show full graph
        self.update()