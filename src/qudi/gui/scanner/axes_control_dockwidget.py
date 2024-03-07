# -*- coding: utf-8 -*-

"""
This file contains a custom QWidget class to provide controls for each scanner axis.

Copyright (c) 2021, the qudi developers. See the AUTHORS.md file at the top-level directory of this
distribution and on <https://github.com/Ulm-IQO/qudi-iqo-modules/>

This file is part of qudi.

Qudi is free software: you can redistribute it and/or modify it under the terms of
the GNU Lesser General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.

Qudi is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with qudi.
If not, see <https://www.gnu.org/licenses/>.
"""

__all__ = ('AxesControlDockWidget', 'AxesControlWidget')

from PySide2 import QtCore, QtGui, QtWidgets
from qudi.util.widgets.scientific_spinbox import ScienDSpinBox
from qudi.util.widgets.slider import DoubleSlider


class AxesControlDockWidget(QtWidgets.QDockWidget):
    """ Scanner control QDockWidget based on the corresponding QWidget subclass
    """
    __wrapped_attributes = frozenset({'sigResolutionChanged', 'sigRangeChanged', 'sigStepSizeChanged',
                                      'sigTargetChanged', 'sigSliderMoved', 'sigCenterSizeChanged', 'axes', 
                                      'resolution', 'scan_size', 'range', 'target', 'get_resolution', 
                                      'set_resolution', 'get_step_size', 'set_step_size', 'get_scan_size', 
                                      'set_scan_size', 'get_range', 'set_range', 'get_target', 'set_target', 
                                      'set_assumed_unit_prefix', 'get_galvo_pos', 'set_galvo_pos'})

    def __init__(self, scanner_axes, stepsize_resolution_mode, default_option_1, default_option_2, default_option_3):
        super().__init__('Axes Control')
        self.setObjectName('axes_control_dockWidget')
        widget = AxesControlWidget(scanner_axes=scanner_axes, stepsize_resolution_mode=stepsize_resolution_mode,
                                   default_option_1=default_option_1, default_option_2=default_option_2, default_option_3=default_option_3)
        widget.setObjectName('axes_control_widget')
        self.setWidget(widget)
        return

    def __getattr__(self, item):
        if item in self.__wrapped_attributes:
            return getattr(self.widget(), item)
        raise AttributeError(f'AxesControlDockWidget has not attribute "{item}"')


class AxesControlWidget(QtWidgets.QWidget):
    """ Widget to control scan parameters and target position of scanner axes.
    """

    sigResolutionChanged = QtCore.Signal(str, int)
    sigStepSizeChanged = QtCore.Signal(str, float)
    sigCenterSizeChanged = QtCore.Signal(str, float)
    sigRangeChanged = QtCore.Signal(str, tuple)
    sigTargetChanged = QtCore.Signal(str, float)
    sigSliderMoved = QtCore.Signal(str, float)

    def __init__(self, *args, scanner_axes, stepsize_resolution_mode, default_option_1, default_option_2, default_option_3, **kwargs):
        super().__init__(*args, **kwargs)

        self.axes_widgets = dict()

        font = QtGui.QFont()
        font.setBold(True)
        layout = QtWidgets.QGridLayout()

        self.stepsize_resolution_mode=stepsize_resolution_mode
        self.default_option_1 = default_option_1
        self.default_option_2 = default_option_2
        self.default_option_3 = default_option_3
        self.scanner_axes = scanner_axes
        

        label = QtWidgets.QLabel('Defaults')
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        # label.setContentsMargins(7, 11, 7, 11)
        layout.addWidget(label, 0, 0)
        
        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        vline.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(vline, 0, 1, len(scanner_axes) + 1, 1)

        if (stepsize_resolution_mode == 'nm'): 
            label = QtWidgets.QLabel('Step Size')
        else:
            label = QtWidgets.QLabel('Resolution')
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label, 0, 3)

        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        vline.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(vline, 0, 4, len(scanner_axes) + 1, 1)

        label = QtWidgets.QLabel('Scan Center')
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label, 0, 5)

        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        vline.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(vline, 0, 6, len(scanner_axes) + 1, 1)

        label = QtWidgets.QLabel('Scan Size')
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label, 0, 7, 1, 2)

        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        vline.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(vline, 0, 8, len(scanner_axes) + 1, 1)

        label = QtWidgets.QLabel('Galvo Position')
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label, 0, 9)

        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        vline.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(vline, 0, 10, len(scanner_axes) + 1, 1)

        label = QtWidgets.QLabel('Current Target')
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label, 0, 11)
        
        set_scan_center_button = QtWidgets.QPushButton("Set Scan Center")
        set_scan_center_button.clicked.connect(
            self.__set_scan_center_button_callback()
        )

        for index, axis in enumerate(scanner_axes, 1):
            defaults_option_buttons = QtWidgets.QPushButton(f"Option {index}")

            # Axis name
            ax_name = axis.name
            label = QtWidgets.QLabel('{0}-Axis:'.format(ax_name.title()))
            label.setObjectName('{0}_axis_label'.format(ax_name))
            label.setFont(font)
            label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            # TODO: Fix range for step size mode
            res_step_size_spinbox = QtWidgets.QSpinBox()
            res_step_size_spinbox.setObjectName('{0}_stepsize_resolution_spinBox'.format(ax_name))
            res_step_size_spinbox.setRange(axis.min_resolution, min(2 ** 31 - 1, axis.max_resolution))
            res_step_size_spinbox.setValue(axis.min_resolution)
            res_step_size_spinbox.setSuffix(f' {stepsize_resolution_mode}')
            res_step_size_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            res_step_size_spinbox.setMinimumSize(50, 0)
            res_step_size_spinbox.setMaximumWidth(75)
            res_step_size_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Preferred)

            scan_center_spinbox = ScienDSpinBox()
            scan_center_spinbox.setObjectName('{0}_scan_center_spinBox'.format(ax_name))
            scan_center_spinbox.setRange(*axis.value_range)
            scan_center_spinbox.setValue(axis.min_value)
            scan_center_spinbox.setSuffix(axis.unit)
            scan_center_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            scan_center_spinbox.setMinimumSize(75, 0)
            scan_center_spinbox.setMaximumWidth(100)
            scan_center_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Preferred)

            scan_size_spinbox = ScienDSpinBox()
            scan_size_spinbox.setObjectName('{0}_scan_size_spinBox'.format(ax_name))
            scan_size_spinbox.setRange(*axis.value_range)
            scan_size_spinbox.setValue(axis.min_value)
            scan_size_spinbox.setSuffix(axis.unit)
            scan_size_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            scan_size_spinbox.setMinimumSize(75, 0)
            scan_size_spinbox.setMaximumWidth(100)
            scan_size_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Preferred)

            # min_spinbox = ScienDSpinBox()
            # min_spinbox.setObjectName('{0}_min_range_scienDSpinBox'.format(ax_name))
            # min_spinbox.setRange(*axis.value_range)
            # min_spinbox.setValue(axis.min_value)
            # min_spinbox.setSuffix(axis.unit)
            # min_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            # min_spinbox.setMinimumSize(75, 0)
            # min_spinbox.setMaximumWidth(120)
            # min_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
            #                           QtWidgets.QSizePolicy.Preferred)

            # max_spinbox = ScienDSpinBox()
            # max_spinbox.setObjectName('{0}_max_range_scienDSpinBox'.format(ax_name))
            # max_spinbox.setRange(*axis.value_range)
            # max_spinbox.setValue(axis.max_value)
            # max_spinbox.setSuffix(axis.unit)
            # max_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            # max_spinbox.setMinimumSize(75, 0)
            # min_spinbox.setMaximumWidth(120)
            # max_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
            #                           QtWidgets.QSizePolicy.Preferred)
            
            galvo_pos_spinbox = ScienDSpinBox()
            galvo_pos_spinbox.setObjectName(f'{ax_name}_galvo_pos_spinBox')
            galvo_pos_spinbox.setRange(*axis.value_range)
            galvo_pos_spinbox.setValue(axis.min_value)
            galvo_pos_spinbox.setSuffix(axis.unit)
            galvo_pos_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            galvo_pos_spinbox.setMinimumSize(75, 0)
            galvo_pos_spinbox.setMaximumWidth(100)
            galvo_pos_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                    QtWidgets.QSizePolicy.Preferred)


            init_pos = (axis.max_value - axis.min_value) / 2 + axis.min_value

            slider = DoubleSlider(QtCore.Qt.Horizontal)
            slider.setObjectName('{0}_position_doubleSlider'.format(ax_name))
            slider.setRange(*axis.value_range)
            granularity = 2 ** 31 - 1
            if axis.min_step > 0:
                granularity = min(granularity,
                                  round((axis.max_value - axis.min_value) / axis.min_step) + 1)
            slider.set_granularity(granularity)
            slider.setValue(init_pos)
            slider.setMinimumSize(150, 0)
            slider.setMaximumWidth(400)
            slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

            pos_spinbox = ScienDSpinBox()
            pos_spinbox.setObjectName('{0}_position_scienDSpinBox'.format(ax_name))
            pos_spinbox.setRange(*axis.value_range)
            pos_spinbox.setValue(init_pos)
            pos_spinbox.setSuffix(axis.unit)
            pos_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            pos_spinbox.setMinimumSize(75, 0)
            pos_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Preferred)
            pos_spinbox.dynamic_precision = False

            # Add to layout
            layout.addWidget(defaults_option_buttons, index, 0)
            layout.addWidget(label, index, 2)
            layout.addWidget(res_step_size_spinbox, index, 3)
            layout.addWidget(scan_center_spinbox, index, 5)
            layout.addWidget(scan_size_spinbox, index, 7)
            
            if (index in (1,2)):
                layout.addWidget(galvo_pos_spinbox, index, 9)
            else:
                layout.addWidget(set_scan_center_button, index, 9)
            
            # layout.addWidget(max_spinbox, index, 8)
            layout.addWidget(slider, index, 11)
            layout.addWidget(pos_spinbox, index, 12)

            # Connect signals
            # TODO "editingFinished" also emits when window gets focus again, so also after alt+tab.
            #  "valueChanged" was considered as a replacement but is emitted when scrolled or while typing numbers.

            if (stepsize_resolution_mode == 'px'):
                res_step_size_spinbox.editingFinished.connect(
                    self.__get_axis_resolution_callback(ax_name, res_step_size_spinbox)
                )
            else:
                res_step_size_spinbox.editingFinished.connect(
                    self.__get_step_size_callback(ax_name, res_step_size_spinbox)
                )

            defaults_option_buttons.clicked.connect(
                self.__set_default_options(index)
            )


            # scan_size_spinbox.editingFinished.connect(
            #     self.__get_scan_size_callback(ax_name, scan_size_spinbox)
            # )
            
            # min_spinbox.editingFinished.connect(
            #     self.__get_axis_min_range_callback(ax_name, min_spinbox)
            # )
            # max_spinbox.editingFinished.connect(
            #     self.__get_axis_max_range_callback(ax_name, max_spinbox)
            # )
            slider.doubleSliderMoved.connect(self.__get_axis_slider_moved_callback(ax_name))
            slider.sliderReleased.connect(self.__get_axis_slider_released_callback(ax_name, slider))
            pos_spinbox.editingFinished.connect(
                self.__get_axis_target_callback(ax_name, pos_spinbox)
            )

            # Remember widgets references for later access
            self.axes_widgets[ax_name] = dict()
            self.axes_widgets[ax_name]['label'] = label
            self.axes_widgets[ax_name]['res_step_size_spinbox'] = res_step_size_spinbox
            self.axes_widgets[ax_name]['scan_size_spinbox'] = scan_size_spinbox
            self.axes_widgets[ax_name]['scan_center_spinbox'] = scan_center_spinbox
            if (index in (1,2)):
                self.axes_widgets[ax_name]['galvo_pos_spinbox'] = galvo_pos_spinbox
            # self.axes_widgets[ax_name]['min_spinbox'] = min_spinbox
            # self.axes_widgets[ax_name]['max_spinbox'] = max_spinbox
            self.axes_widgets[ax_name]['slider'] = slider
            self.axes_widgets[ax_name]['pos_spinbox'] = pos_spinbox

        layout.setColumnStretch(5, 1)
        self.setLayout(layout)
        self.setMaximumHeight(self.sizeHint().height())

        # set tab order of Widgets
        res_widgets = [self.axes_widgets[ax]['res_step_size_spinbox'] for ax in self.axes]
        # min_spinboxes = [self.axes_widgets[ax]['min_spinbox'] for ax in self.axes]
        # max_spinboxes = [self.axes_widgets[ax]['max_spinbox'] for ax in self.axes]
        pos_spinboxes = [self.axes_widgets[ax]['pos_spinbox'] for ax in self.axes]

        for idx in range(len(self.axes) - 1):
            self.setTabOrder(res_widgets[idx], res_widgets[idx + 1])

        # self.setTabOrder(res_widgets[-1], min_spinboxes[0])

        # for idx in range(len(self.axes) - 1):
        #     self.setTabOrder(min_spinboxes[idx], max_spinboxes[idx])
        #     self.setTabOrder(max_spinboxes[idx], min_spinboxes[idx + 1])

        # self.setTabOrder(min_spinboxes[-1], max_spinboxes[-1])

        # self.setTabOrder(max_spinboxes[-1], pos_spinboxes[0])

        for idx in range(len(self.axes) - 1):
            self.setTabOrder(pos_spinboxes[idx], pos_spinboxes[idx + 1])
                
    @property
    def axes(self):
        return tuple(self.axes_widgets)

    @property
    def resolution(self):
        return {ax: widgets['res_step_size_spinbox'].value() for ax, widgets in self.axes_widgets.items()}

    @property
    def scan_size(self):
        return {ax: widgets['scan_size_spinbox'].value() for ax, widgets in self.axes_widgets.items()}

    @property
    def range(self):
        return {ax: (widgets['min_spinbox'].value(), widgets['max_spinbox'].value()) for ax, widgets
                in self.axes_widgets.items()}

    @property
    def target(self):
        return {ax: widgets['pos_spinbox'].value() for ax, widgets in self.axes_widgets.items()}

    def get_resolution(self, axis):
        return self.axes_widgets[axis]['res_step_size_spinbox'].value()

    @QtCore.Slot(dict)
    def set_resolution(self, value, axis=None):
        if axis is None or isinstance(value, dict):
            for ax, val in value.items():
                resolution = self.axes_widgets[ax]['res_step_size_spinbox']
                resolution.blockSignals(True)
                resolution.setValue(val)
                resolution.blockSignals(False)
        else:
            resolution = self.axes_widgets[axis]['res_step_size_spinbox']
            resolution.blockSignals(True)
            resolution.setValue(value)
            resolution.blockSignals(False)


    def get_step_size(self, axis):
        return self.axes_widgets[axis]['res_step_size_spinbox'].value()

    @QtCore.Slot(dict)
    def set_step_size(self, value, axis=None):
        if axis is None or isinstance(value, dict):
            for ax, val in value.items():
                step_size = self.axes_widgets[ax]['res_step_size_spinbox']
                step_size.blockSignals(True)
                step_size.setValue(val)
                step_size.blockSignals(False)
        else:
            step_size = self.axes_widgets[axis]['res_step_size_spinbox']
            step_size.blockSignals(True)
            step_size.setValue(value)
            step_size.blockSignals(False)

    def get_scan_size(self, axis):
        return self.axes_widgets[axis]['scan_size_spinbox'].value()

    @QtCore.Slot(dict)
    def set_scan_size(self, value, axis=None):
        if axis is None or isinstance(value, dict):
            for ax, val in value.items():
                scan_size = self.axes_widgets[ax]['scan_size_spinbox']
                scan_size.blockSignals(True)
                scan_size.setValue(val)
                scan_size.blockSignals(False)
        else:
            scan_size = self.axes_widgets[axis]['scan_size_spinbox']
            scan_size.blockSignals(True)
            scan_size.setValue(value)
            scan_size.blockSignals(False)

    def get_range(self, axis):
        widget_dict = self.axes_widgets[axis]
        return widget_dict['min_spinbox'].value(), widget_dict['max_spinbox'].value()

    @QtCore.Slot(dict)
    def set_range(self, value, axis=None):
        if axis is None or isinstance(value, dict):
            for ax, val in value.items():
                # min_spinbox = self.axes_widgets[ax]['min_spinbox']
                # max_spinbox = self.axes_widgets[ax]['max_spinbox']
                scan_size_spinbox = self.axes_widgets[ax]['scan_size_spinbox']
                min_val, max_val = val
                scan_size = (max_val - min_val)
                # min_spinbox.blockSignals(True)
                # min_spinbox.setValue(min_val)
                # min_spinbox.blockSignals(False)
                # max_spinbox.blockSignals(True)
                # max_spinbox.setValue(max_val)
                # max_spinbox.blockSignals(False)
                scan_size_spinbox.blockSignals(True)
                scan_size_spinbox.setValue(scan_size)
                scan_size_spinbox.blockSignals(False)
        else:
            # min_spinbox = self.axes_widgets[axis]['min_spinbox']
            # max_spinbox = self.axes_widgets[axis]['max_spinbox']
            scan_size_spinbox = self.axes_widgets[axis]['scan_size_spinbox']
            min_val, max_val = val
            scan_size = (max_val - min_val) / 2
            # min_spinbox.blockSignals(True)
            # min_spinbox.setValue(min_val)
            # min_spinbox.blockSignals(False)
            # max_spinbox.blockSignals(True)
            # max_spinbox.setValue(max_val)
            # max_spinbox.blockSignals(False)
            scan_size_spinbox.blockSignals(True)
            scan_size_spinbox.setValue(scan_size)
            scan_size_spinbox.blockSignals(False)

    def get_target(self, axis):
        return self.axes_widgets[axis]['pos_spinbox'].value()

    @QtCore.Slot(dict)
    def set_target(self, value, axis=None):
        if axis is None or isinstance(value, dict):
            for ax, val in value.items():
                spinbox = self.axes_widgets[ax]['pos_spinbox']
                slider = self.axes_widgets[ax]['slider']
                slider.blockSignals(True)
                slider.setValue(val)
                slider.blockSignals(False)
                spinbox.blockSignals(True)
                spinbox.setValue(val)
                spinbox.blockSignals(False)
        else:
            spinbox = self.axes_widgets[axis]['pos_spinbox']
            slider = self.axes_widgets[axis]['slider']
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)
            spinbox.blockSignals(True)
            spinbox.setValue(value)
            spinbox.blockSignals(False)

    def get_galvo_pos(self, axis):
        return self.axes_widgets[axis]['pos_spinbox'].value()

    @QtCore.Slot(dict)
    def set_galvo_pos(self, value, axis=None):
        if axis is None or isinstance(value, dict):
            for ax, val in value.items():
                spinbox = self.axes_widgets[ax]['pos_spinbox']
        else:
            spinbox = self.axes_widgets[axis]['pos_spinbox']


    def set_assumed_unit_prefix(self, prefix):
        for widgets in self.axes_widgets.values():
            widgets['pos_spinbox'].assumed_unit_prefix = prefix
            widgets['scan_size_spinbox'].assumed_unit_prefix = prefix
            # widgets['min_spinbox'].assumed_unit_prefix = prefix
            # widgets['max_spinbox'].assumed_unit_prefix = prefix

    def __set_default_options(self, index):
        def callback():
            default_scan_size_x = 0
            default_scan_size_y = 0
            default_step_size = 0
            
            if (index == 1):
                default_scan_size_x = self.default_option_1[0]
                default_scan_size_y = self.default_option_1[1]
                default_step_size = self.default_option_1[2]
            elif (index == 2):
                default_scan_size_x = self.default_option_2[0]
                default_scan_size_y = self.default_option_2[1]
                default_step_size = self.default_option_2[2]
            elif (index == 3):
                default_scan_size_x = self.default_option_3[0]
                default_scan_size_y = self.default_option_3[1]
                default_step_size = self.default_option_3[2]
                
            # self.sigRangeChanged.emit("x", (max(min_value, floor), min(max_value, ceiling)))
            self.set_scan_size(default_scan_size_x, "x")
            self.set_scan_size(default_scan_size_y, "y")
            self.set_step_size(default_step_size, "x")
            self.set_step_size(default_step_size, "y")
            self.set_step_size(default_step_size, "z")
        return callback


    def __set_scan_center_button_callback(self):
        def callback():

            for idx, ax in enumerate(self.scanner_axes):
                axis = ax.name
                curr_pos_spinbox = self.axes_widgets[axis]['pos_spinbox']
                curr_scan_size_spinbox = self.axes_widgets[axis]['scan_size_spinbox']
                scan_center_spinbox = self.axes_widgets[axis]['scan_center_spinbox']
                
                curr_pos = curr_pos_spinbox.value()
                curr_scan_size = curr_scan_size_spinbox.value()
                
                min_value = curr_pos - curr_scan_size / 2
                max_value = curr_pos + curr_scan_size / 2

                ceiling = ax.max_value 
                floor   = ax.min_value
                
                scan_center_spinbox.blockSignals(True)
                scan_center_spinbox.setValue(curr_pos)
                scan_center_spinbox.blockSignals(False)


                self.sigRangeChanged.emit(axis, (max(min_value, floor), min(max_value, ceiling)))
                print(f"__set_scan_center_button_callback (axis, (max(min_value, floor), min(max_value, ceiling))): {(axis, (max(min_value, floor), min(max_value, ceiling)))}")

        return callback

    def __get_axis_resolution_callback(self, axis, spinbox):
        def callback():
            self.sigResolutionChanged.emit(axis, spinbox.value())
        return callback

    def __get_step_size_callback(self, axis, spinbox):
        def callback():
            min_range, max_range = self.get_range(axis=axis)
            # self.sigStepSizeChanged.emit(axis, (max_range - min_range) / (spinbox.value() / (10 ** 9)))
            self.sigStepSizeChanged.emit(axis, spinbox.value())
        return callback

    def __get_scan_size_callback(self, axis, spinbox):
        def callback():
            curr_pos_spinbox = self.axes_widgets[axis]['pos_spinbox']
            min_value = curr_pos_spinbox.value() - spinbox.value() / 2
            max_value = curr_pos_spinbox.value() + spinbox.value() / 2
            ceiling = 10000000
            floor = 0
            for idx, ax in enumerate(self.scanner_axes):
                if axis == ax.name:
                    ceiling = ax.max_value
                    floor = ax.min_value

            print(f"__get_scan_size_callback (axis, (max(min_value, floor), min(max_value, ceiling))): {(axis, (max(min_value, floor), min(max_value, ceiling)))}")
            self.sigRangeChanged.emit(axis, (max(min_value, floor), min(max_value, ceiling)))
        return callback

    def __get_axis_min_range_callback(self, axis, spinbox):
        def callback():
            max_spinbox = self.axes_widgets[axis]['max_spinbox']
            min_value = spinbox.value()
            max_value = max_spinbox.value()
            if min_value > max_value:
                max_spinbox.blockSignals(True)
                max_spinbox.setValue(min_value)
                max_spinbox.blockSignals(False)
                max_value = min_value
            print(f"__get_axis_min_range_callback (axis, (min_value, max_value)): {(axis, (min_value, max_value))}")
            self.sigRangeChanged.emit(axis, (min_value, max_value))
        return callback

    def __get_axis_max_range_callback(self, axis, spinbox):
        def callback():
            min_spinbox = self.axes_widgets[axis]['min_spinbox']
            min_value = min_spinbox.value()
            max_value = spinbox.value()
            if max_value < min_value:
                min_spinbox.blockSignals(True)
                min_spinbox.setValue(max_value)
                min_spinbox.blockSignals(False)
                min_value = max_value
            print(f"__get_axis_max_range_callback (axis, (min_value, max_value)): {(axis, (min_value, max_value))}")
            self.sigRangeChanged.emit(axis, (min_value, max_value))
        return callback

    def __get_axis_slider_moved_callback(self, axis):
        def callback(value):
            spinbox = self.axes_widgets[axis]['pos_spinbox']
            spinbox.blockSignals(True)
            spinbox.setValue(value)
            spinbox.blockSignals(False)
            self.sigSliderMoved.emit(axis, value)
        return callback

    def __get_axis_slider_released_callback(self, axis, slider):
        def callback():
            value = slider.value()
            spinbox = self.axes_widgets[axis]['pos_spinbox']
            spinbox.blockSignals(True)
            spinbox.setValue(value)
            spinbox.blockSignals(False)
            self.sigTargetChanged.emit(axis, value)
        return callback

    def __get_axis_target_callback(self, axis, spinbox):
        def callback():
            value = spinbox.value()
            slider = self.axes_widgets[axis]['slider']
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)
            self.sigTargetChanged.emit(axis, value)
        return callback
