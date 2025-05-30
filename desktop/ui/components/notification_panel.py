from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QFrame, QWidget, QGridLayout, QScrollArea, QDialog, QSizePolicy)
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QTimer
from PyQt6.QtGui import QIcon, QCursor, QFont
from . import BaseComponent
from .notification_components.notification_card import NotificationCard

class NotificationPanel(BaseComponent):
    def _create_ui(self):
        self.all_sample_notifications_data = [] # Store all notification data
        main_layout = QVBoxLayout(self)
        self.setObjectName("notification_panel")

        self.grid_row = 0
        self.grid_col = 0
        self.num_columns = 2  # Display 2 notifications per row
        
        # Header with title, clear all, and settings
        header_layout = QHBoxLayout()
        title = QLabel("Recent Matches")
        title.setObjectName("section_title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch(1) # Add stretch before buttons

        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.setObjectName("small_button") # Re-use existing style or create new
        self.clear_all_button.clicked.connect(self._clear_all_notifications_action)
        header_layout.addWidget(self.clear_all_button)
        
        settings_button = QPushButton("Settings")
        settings_button.setObjectName("small_button")
        header_layout.addWidget(settings_button) # Removed alignment, will use stretch before
        
        main_layout.addLayout(header_layout)
        
        # Notification container setup with QGridLayout
        self.notification_container = QWidget() # This widget will hold the grid
        self.grid_layout = QGridLayout(self.notification_container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setSpacing(10)
        for i in range(self.num_columns):
            self.grid_layout.setColumnStretch(i, 1)

        # Add the notification container (which contains the grid) directly to the main layout
        main_layout.addWidget(self.notification_container)

        # "View All Notifications" button
        self.view_all_button = QPushButton("View All Notifications")
        self.view_all_button.setObjectName("view_all_button") # For potential styling
        self.view_all_button.clicked.connect(self._show_all_notifications_dialog)
        main_layout.addWidget(self.view_all_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Load and display initial notifications
        self._load_sample_notifications_data()
        self._display_initial_notifications()

    def _load_sample_notifications_data(self):
        sample_matches = [
            {
                "title": "Mercedes-Benz CLA 200 d",
                "subtitle": "Shooting Brake • AMG • CAMERA",
                "price": "35.980 €",
                "time": "2 hours ago",
                "type": "match",
                "margin_rating": 5,
                "margin_text": "Very good price",
                "margin_percentage_text": "Profit est: 18%"
            },
            {
                "title": "BMW 3 Series 320d",
                "subtitle": "M Sport • Panorama • LED",
                "price": "42.500 €",
                "time": "3 hours ago",
                "type": "price_drop",
                "margin_rating": 3,
                "margin_text": "Fair price",
                "margin_percentage_text": "Profit est: 8%"
            },
            {
                "title": "Audi A4 Avant 2.0 TDI",
                "subtitle": "S line • quattro • Matrix",
                "price": "38.900 €",
                "time": "5 hours ago",
                "type": "new_arrival",
                "margin_rating": 4,
                "margin_text": "Good price",
                "margin_percentage_text": "Profit est: 12%"
            },
            {
                "title": "Volkswagen Golf VIII",
                "subtitle": "1.5 eTSI • R-Line • HUD",
                "price": "28.750 €",
                "time": "1 day ago",
                "type": "match",
                "margin_rating": 5,
                "margin_text": "Excellent deal",
                "margin_percentage_text": "Profit est: 20%"
            },
            # Adding a fifth notification to test the "View All" functionality
            {
                "title": "Tesla Model 3",
                "subtitle": "Long Range • Autopilot",
                "price": "55.000 €",
                "time": "2 days ago",
                "type": "match",
                "margin_rating": 4,
                "margin_text": "Good price",
                "margin_percentage_text": "Profit est: 15%"
            }
        ]
        self.all_sample_notifications_data = sample_matches

    def _clear_grid_layout(self):
        # Clears all widgets from self.grid_layout
        # Also remove the "no matches" label if it exists
        existing_no_matches_label = self.notification_container.findChild(QLabel, "no_matches_label_style")
        if existing_no_matches_label:
            self.grid_layout.removeWidget(existing_no_matches_label)
            existing_no_matches_label.deleteLater()
            
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                # child.widget().setParent(None) # Not strictly necessary before deleteLater if taken from layout
                child.widget().deleteLater()
        self.grid_row = 0
        self.grid_col = 0

    def _display_initial_notifications(self):
        self._clear_grid_layout()
        
        if not self.all_sample_notifications_data:
            # Display "No new matches" message
            no_matches_label = QLabel("No new matches so far.")
            no_matches_label.setObjectName("no_matches_label_style") # For styling
            no_matches_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_matches_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Normal)) # Example font
            # Add to grid, spanning all columns
            self.grid_layout.addWidget(no_matches_label, 0, 0, 1, self.num_columns)
            self.grid_row = 1 # Next item would be on next row
            self.grid_col = 0
            
            self.view_all_button.hide()
            self.clear_all_button.hide()
            # change the size of the scroll area
        else:
            # Display up to the last 3 notifications.
            notifications_to_show = self.all_sample_notifications_data[-2:]
            for match_data in notifications_to_show:
                self._add_match_notification_to_grid(match_data)
            
            # Show/Hide "View All" button
            if len(self.all_sample_notifications_data) <= 2:
                self.view_all_button.hide()
            else:
                self.view_all_button.show()
            
            # Show/Hide Clear All button
            self.clear_all_button.show()

    def _show_all_notifications_dialog(self):
        if not self.all_sample_notifications_data:
            return # No data to show

        dialog = QDialog(self)
        dialog.setWindowTitle("All Notifications")
        dialog.setMinimumSize(700, 500) # Set a decent minimum size

        dialog_layout = QVBoxLayout(dialog)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Usually off for vertical lists
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        notification_container_dialog = QWidget()
        grid_layout_dialog = QGridLayout(notification_container_dialog)
        grid_layout_dialog.setAlignment(Qt.AlignmentFlag.AlignTop)
        grid_layout_dialog.setSpacing(10)
        
        # Determine number of columns (can be same as main panel or different)
        num_dialog_columns = self.num_columns 
        for i in range(num_dialog_columns):
            grid_layout_dialog.setColumnStretch(i, 1)

        dialog_grid_row = 0
        dialog_grid_col = 0

        for match_data in self.all_sample_notifications_data:
            notification_widget = NotificationCard(match_data, self._handle_dismiss_notification_from_dialog)
            grid_layout_dialog.addWidget(notification_widget, dialog_grid_row, dialog_grid_col)
            dialog_grid_col += 1
            if dialog_grid_col >= num_dialog_columns:
                dialog_grid_col = 0
                dialog_grid_row += 1
        
        scroll_area.setWidget(notification_container_dialog)
        dialog_layout.addWidget(scroll_area)

        # Optional: Add a close button to the dialog
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept) # Or dialog.close
        dialog_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.exec()

    def _add_match_notification_to_grid(self, match_data, target_layout=None, dismiss_callback=None):
        # Default to self.grid_layout and self._handle_dismiss_notification if not provided
        layout_to_use = target_layout if target_layout else self.grid_layout
        callback_to_use = dismiss_callback if dismiss_callback else self._handle_dismiss_notification

        notification_widget = NotificationCard(match_data, callback_to_use)
        
        # Determine where to add the widget based on which layout is being used
        if layout_to_use == self.grid_layout:
            layout_to_use.addWidget(notification_widget, self.grid_row, self.grid_col)
            self.grid_col += 1
            if self.grid_col >= self.num_columns:
                self.grid_col = 0
                self.grid_row += 1
        else: # Assuming it's a dialog grid or similar, needs row/col management if not self.grid_layout
            # For simplicity, this example assumes dialogs manage their own row/col or add sequentially
            # For a more robust solution for dialogs, pass row/col indices or manage them in the dialog method
            current_row = target_layout.rowCount()
            current_col = 0
            # Find the next available cell or start a new row
            # This is a simplified logic; a more robust one would track col/row for the dialog grid
            if target_layout.itemAtPosition(current_row -1, self.num_columns -1) is not None : # if last cell of current row is filled
                 current_row +=1
            else: # find first empty cell in current_row (or last row)
                for c in range(self.num_columns):
                    if target_layout.itemAtPosition(current_row -1, c) is None:
                        current_col = c
                        current_row -=1 # use current row
                        break
            layout_to_use.addWidget(notification_widget, current_row, current_col)

    def _handle_dismiss_notification(self, match_data_to_remove, notification_widget_to_remove):
        if match_data_to_remove in self.all_sample_notifications_data:
            self.all_sample_notifications_data.remove(match_data_to_remove)

        if notification_widget_to_remove:
            notification_widget_to_remove.setParent(None) 
            notification_widget_to_remove.deleteLater()
        
        # Refresh the main notification panel display
        self._display_initial_notifications()

    def _handle_dismiss_notification_from_dialog(self, match_data_to_remove, notification_widget_to_remove):
        # This method is called when a notification is dismissed from the "All Notifications" dialog.
        # It ensures the main panel is also updated.
        if match_data_to_remove in self.all_sample_notifications_data:
            self.all_sample_notifications_data.remove(match_data_to_remove)
        
        # The widget itself is part of the dialog, so it will be cleaned up when the dialog closes
        # or if we manually remove it from the dialog's layout.
        # For simplicity, we'll let the card handle its own deletion via its dismiss_callback.
        # The key is to update the underlying data and refresh the main panel.
        if notification_widget_to_remove: # Widget is passed to be removed from dialog's layout
             notification_widget_to_remove.setParent(None)
             notification_widget_to_remove.deleteLater()

        # Refresh the main notification panel display after dialog interaction
        self._display_initial_notifications()
        
        # Additionally, we might need to refresh the dialog if it's still open,
        # or simply close it. For now, let's assume the user will close the dialog.
        # If the dialog needs to be refreshed live, its parent (dialog) would need a method to rebuild its content.

    def _clear_all_notifications_action(self):
        self.all_sample_notifications_data.clear()
        # _display_initial_notifications will call _clear_grid_layout and update buttons
        self._display_initial_notifications() 