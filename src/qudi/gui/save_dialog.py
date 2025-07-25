import os
import numpy as np
import time
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette

class SaveDialog(QtWidgets.QDialog):
    """ Dialog to provide feedback and block GUI while saving """
    def __init__(self, parent, default_filename="", default_notes=""):
        super().__init__(parent)
        
        self.setWindowTitle("Saving...")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        
        # text box for experiment name
        self.name_label = QtWidgets.QLabel("Experiment/Sample Name:")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("e.g. test_run_01")

        # text box for notes
        self.notes_label = QtWidgets.QLabel("Notes (optional):")
        self.notes_edit = QtWidgets.QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Add notes or observations...")
        
        # persistennce
        self.name_edit.setText(default_filename)
        self.notes_edit.setPlainText(default_notes)

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.setEnabled(False)  # disabled until name is entered

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)
        layout.addWidget(self.notes_label)
        layout.addWidget(self.notes_edit)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        # --- Connections
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.save_button.clicked.connect(self.accept)

    def _on_name_changed(self, text):
        self.save_button.setEnabled(bool(text.strip()))

    def get_data(self):
        return self.name_edit.text().strip(), self.notes_edit.toPlainText().strip()

    # just for QOL because it closes out normally if you x out
    # i think reject (for pyside5) is a protected function so should be ok to call???
    def reject(self):
        if not self.name_edit.text().strip():
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Quit without saving?")
            msg.setText("You haven't entered a file name for this experiment.\nDo you want to go back and enter one?")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
            response = msg.exec_()

            if response == QtWidgets.QMessageBox.Yes:
                return  # don't close the dialog
        super().reject()  # proceed with closing