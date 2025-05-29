from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from . import BaseComponent
from .filter_panel_components.filter_inputs import FilterInputs
from .filter_panel_components.filter_options import FilterOptions

class FilterPanel(BaseComponent):
    model_tracking_requested = pyqtSignal(dict)

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
        # self.filter_options_widget.additional_filters_button.clicked.connect(self._show_additional_filters) # Placeholder
        
        content_layout.addWidget(filter_frame)
        content_layout.addStretch(1)
        main_layout.addWidget(content, 1)

    def _toggle_tracking_mode(self, state):
        if state == Qt.CheckState.Checked.value:
            self.is_tracking_mode = True
            self.filter_inputs_widget.set_search_button_text("Add to Tracked List")
        else:
            self.is_tracking_mode = False
            self.filter_inputs_widget.set_search_button_text(self.filter_inputs_widget.original_search_button_text)

    def _on_search_button_clicked(self):
        if self.is_tracking_mode:
            criteria = self.filter_inputs_widget.get_criteria()
            # For tracking, we might only care about brand, model, year
            model_criteria = {
                "brand": criteria.get("brand"),
                "model": criteria.get("model"),
                "year": criteria.get("year"),
            }
            if any(model_criteria.values()): 
                print(f"[FilterPanel] Tracking requested for: {model_criteria}")
                self.model_tracking_requested.emit(model_criteria)
            else:
                print("[FilterPanel] Tracking requested, but no specific criteria set.")
        else:
            print("[FilterPanel] Normal search button clicked.")
            # Implement actual search logic here based on self.filter_inputs_widget.get_criteria()
            all_criteria = self.filter_inputs_widget.get_criteria()
            print(f"[FilterPanel] Search with criteria: {all_criteria}")
            pass 

    def _reset_filters(self):
        self.filter_inputs_widget.reset_inputs()
        self.filter_options_widget.tracking_mode_checkbox.setChecked(False) # Untick tracking mode
        # self.is_tracking_mode will be set to False by _toggle_tracking_mode via checkbox signal
        print("[FilterPanel] Filters reset.")

    # def _show_additional_filters(self):
    #     print("[FilterPanel] Additional filters button clicked.")
    #     # Implement logic to show more filters, perhaps in a dialog or by expanding the panel
    #     pass 