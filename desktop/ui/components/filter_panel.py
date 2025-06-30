from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from . import BaseComponent
from .filter_panel_components.filter_inputs import FilterInputs
from .filter_panel_components.filter_options import FilterOptions
import os
from PyQt6.QtCore import pyqtSignal, Qt, QObject, QRunnable, QThreadPool
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QApplication)
from PyQt6.QtGui import QCursor
from desktop.services.main_api_service import APIService
from desktop.GLOBAL import GLOBAL

# Worker for fetching the best offer
class BestOfferWorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class BestOfferWorker(QRunnable):
    def __init__(self, api_service, license_key):
        super().__init__()
        self.api_service = api_service
        self.license_key = license_key
        self.signals = BestOfferWorkerSignals()

    def run(self):
        try:
            response = self.api_service.get_best_offer_sync(self.license_key)
            self.signals.finished.emit(response)
        except Exception as e:
            self.signals.error.emit(str(e))

class FilterPanel(BaseComponent):
    # Signal to emit complete filter criteria for tracking
    model_tracking_requested = pyqtSignal(dict)  # Now emits complete filter criteria
    # Signal to emit search request with criteria
    search_requested = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        self.threadpool = QThreadPool()
        super().__init__(*args, **kwargs)
        # Set max threads for this specific threadpool if needed
        # self.threadpool.setMaxThreadCount(2) 

    def _create_ui(self):
        self.is_tracking_mode = False

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        content = QFrame()
        content.setObjectName("filter_content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(15)
        
        filter_frame = QFrame()
        filter_frame.setObjectName("dark_filter_frame")
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(15)
        
        # Create and add filter inputs subcomponent
        self.filter_inputs_widget = FilterInputs()
        filter_layout.addWidget(self.filter_inputs_widget)
        self.filter_inputs_widget.search_button.clicked.connect(self._on_search_button_clicked)

        # Create and add filter options subcomponent
        self.filter_options_widget = FilterOptions()
        filter_layout.addWidget(self.filter_options_widget)
        self.filter_options_widget.tracking_mode_checkbox.stateChanged.connect(self._toggle_tracking_mode)
        self.filter_options_widget.reset_button.clicked.connect(self._reset_filters) # Connect reset
        self.filter_options_widget.analyze_button.clicked.connect(self._analyze_best_offer)
        
        content_layout.addWidget(filter_frame)
        content_layout.addStretch(1)
        main_layout.addWidget(content, 1)

    def _toggle_tracking_mode(self, state):
        if state == Qt.CheckState.Checked.value:
            self.is_tracking_mode = True
            self.filter_inputs_widget.set_search_button_text("Add to Tracked List")
        else:
            self.is_tracking_mode = False
            self.filter_inputs_widget.restore_auto_button_updates()

    def _on_search_button_clicked(self):
        criteria = self.filter_inputs_widget.get_criteria()
        
        if self.is_tracking_mode:
            # Include all available filter criteria for tracking
            if criteria:  # If any criteria is set
                print(f"[FilterPanel] Tracking requested for: {criteria}")
                self.model_tracking_requested.emit(criteria)
            else:
                print("[FilterPanel] Tracking requested, but no criteria set.")
        else:
            print(f"[FilterPanel] Search requested with criteria: {criteria}")
            # Emit search signal with criteria (can be empty for "show all")
            self.search_requested.emit(criteria) 

    def _reset_filters(self):
        self.filter_inputs_widget.reset_inputs()
        self.filter_options_widget.tracking_mode_checkbox.setChecked(False) # Untick tracking mode
        # self.is_tracking_mode will be set to False by _toggle_tracking_mode via checkbox signal
        print("[FilterPanel] Filters reset.")

    def _analyze_best_offer(self):
        """Initiates the best offer analysis."""
        license_key = GLOBAL.LICENSE.get_license_key()
        if not license_key:
            QMessageBox.warning(self, "No License Key", "A valid license key is required to analyze offers.")
            return

        # Show loading indicator
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        
        # Run in background thread
        worker = BestOfferWorker(APIService(), license_key)
        worker.signals.finished.connect(self._on_analysis_finished)
        worker.signals.error.connect(self._on_analysis_error)
        self.threadpool.start(worker)

    def _on_analysis_finished(self, response):
        """Handles the successful completion of the best offer analysis."""
        QApplication.restoreOverrideCursor() # Hide loading indicator
        
        if response and response.get('best_offer'):
            offer = response['best_offer']
            actual_price = offer.get('actual_price', 0)
            predicted_price = offer.get('predicted_price', 0)
            savings = offer.get('saving', 0)
            url = offer.get('url', '')

            if savings > 0:
                title = "🎉 Best Offer Found!"
                message = f"""
                Based on your tracked filters, we found an excellent deal on a 
                <b>{offer.get('brand', '')} {offer.get('model', '')}</b>!
                <br><br>
                Actual Price: <b>€{actual_price:,.2f}</b><br>
                Predicted Market Price: <b>€{predicted_price:,.2f}</b><br>
                <font color='green'>Potential Savings: <b>€{savings:,.2f}</b></font>
                <br><br>
                <a href='{url}'>View Offer</a>
                """
                # Use a QMessageBox instance to enable rich text
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(title)
                msg_box.setTextFormat(Qt.TextFormat.RichText)
                msg_box.setText(message)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
            else:
                QMessageBox.information(self, "Analysis Complete", "No special offers found for your tracked filters at this time. Try tracking more models!")
        else:
            QMessageBox.information(self, "Analysis Complete", "No offers found matching your tracked filters. Try adding more tracked models to improve the analysis.")

    def _on_analysis_error(self, error_message):
        """Handles errors during the best offer analysis."""
        QApplication.restoreOverrideCursor() # Hide loading indicator
        
        # Use a QMessageBox instance to enable rich text for the error message
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Analysis Failed")
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(f"Could not analyze offers. Please check your internet connection and try again.\n\n<small>Error: {error_message}</small>")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    # def _show_additional_filters(self):
    #     print("[FilterPanel] Additional filters button clicked.")
    #     # Implement logic to show more filters, perhaps in a dialog or by expanding the panel
    #     pass 