# -*- coding: utf-8 -*-

"""
This file contains a gui to switch a beam block mirror and camera mirror off and on.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import os

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette

class FlipperMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the \*.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_flippermirror_gui.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class FlipperGUI(GuiBase):
    """
    Main flipper mirror gui class.
    """

    #Connector
    flipperlogic = Connector(interface='FlipperMirrorLogic')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """ Definition and initialisation of the GUI.
        """
        self._flipperlogic = self.flipperlogic()

        self._mw = FlipperMainWindow()

        self._mw.onButton_1.clicked.connect(lambda: self.flipOn(1))
        self._mw.onButton_2.clicked.connect(lambda: self.flipOn(2))
        self._mw.offButton_1.clicked.connect(lambda: self.flipOff(1))
        self._mw.offButton_2.clicked.connect(lambda: self.flipOff(2))

        self.show()

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def flipOn(self, num):
        """Flips on one flipper mirror.
        @param (int) num: specifies which flipper mirror to turn on.
        """
        self._flipperlogic.set_mode('on', num)

    def flipOff(self, num):
        """Flips off one flipper mirror.
        @param (int) num: specifies which flipper mirror to turn off.
        """
        self._flipperlogic.set_mode('off', num)

    def show(self):
        """Make main window visible and put it above all other windows. """
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()