import os
import sys
import platform

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QScrollArea, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, QLayoutItem, QPlainTextEdit, QPushButton, QComboBox, QLineEdit, QWidget, QLabel, QMessageBox, QCheckBox
from PyQt6.QtCore import QTimer, QThreadPool, QSignalBlocker, Qt
from PyQt6.QtGui import QIcon, QIntValidator
from PyQt6.QtGui import QPixmap
from ble_scanner import BLEScanner
from ble_to_lsl_streamer import BLEtoLSLStreamer, ConfigProperties, LSLProperties
from lsl_data_selector import DataSelector
from animated_toggle import AnimatedToggle
import time

class BLEToLSLGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.devices = []
        self.services = []
        self.service_selected = None
        self.characteristics = None
        self.scanner_running: bool = False
        self.ble_to_lsl_running: bool = False
        self.device_waiting: bool = False
        self.started: bool = False
        self.lsl_properties = LSLProperties()
        self.config = ConfigProperties()
        
        
        self.setWindowTitle("Arduino LSM9DS1 BLE to LSL")
        self.setGeometry(100, 30, 450, 795)
        
        self.central_widget = QWidget()
        
        # self.move(100, 10) 
        # Create a scroll area and set its widget to the scroll content widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the scroll area to resize its content
        scroll_area.setWidget(self.central_widget)
        
        self.setCentralWidget(scroll_area)
        self.layout = QVBoxLayout()
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(script_dir, 'images')
        top_image_path = os.path.join(images_dir, 'logo.png')
        icon_image_path = os.path.join(images_dir, 'icon.png')
        
        self.setWindowIcon(QIcon(icon_image_path))
        
        logo_image = QLabel()
        pixmap = QPixmap(top_image_path).scaled(*(400, 400), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio, transformMode=Qt.TransformationMode.SmoothTransformation)
        logo_image.setPixmap(pixmap)
        self.layout.addWidget(logo_image)

        
        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)
        
        self.devices_layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.devices_dropdown = QComboBox()
        self.devices_layout.addWidget(self.devices_dropdown)
        self.devices_dropdown.currentIndexChanged.connect(self.get_services)

        self.refresh_button = QPushButton()
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_BrowserReload)
        self.refresh_button.setIcon(icon)
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.refresh_button.setFixedSize(30, 25)  # Set fixed size for the button
        self.devices_layout.addWidget(self.refresh_button)
        self.layout.addLayout(self.devices_layout)
        
        self.services_label = QLabel("Services and characteristics")
        self.layout.addWidget(self.services_label)
        self.services_dropdown = QComboBox()
        self.layout.addWidget(self.services_dropdown)
        self.services_dropdown.setEnabled(False)
        self.services_dropdown.currentIndexChanged.connect(self.update_characteristics)

        self.characteristics_dropdown = QComboBox()
        self.layout.addWidget(self.characteristics_dropdown)
        self.characteristics_dropdown.setEnabled(False)  
        
        separator_frame2 = QFrame()
        separator_frame2.setFrameShape(QFrame.Shape.HLine)
        separator_frame2.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(separator_frame2)
        
        self.lsl_checkbox = QCheckBox("LSL")
        self.lsl_checkbox.setChecked(True)
        self.lsl_checkbox.clicked.connect(self.enable_lsl)
        self.layout.addWidget(self.lsl_checkbox)
        
        self.lsl_layout = QGridLayout()
        
        self.data_selector = DataSelector()
        self.lsl_data_button = QPushButton("Select data to stream", self)
        self.lsl_data_button.clicked.connect(self.open_data_selector)
        self.data_selector.signals.change.connect(self.retrieve_lsl_data_to_stream)
        self.lsl_layout.addWidget(self.lsl_data_button)
        self.lsl_name_label = QLabel("Name")
        self.lsl_name = QLineEdit()
        self.lsl_name.setPlaceholderText("Name")
        self.lsl_name.setText("Test")
        self.lsl_layout.addWidget(self.lsl_name_label,1, 0)
        self.lsl_layout.addWidget(self.lsl_name, 2, 0)
        
        self.lsl_type_label = QLabel("Type")
        self.lsl_type = QLineEdit()
        self.lsl_type.setPlaceholderText("Type")
        self.lsl_type.setText("IMU")
        self.lsl_layout.addWidget(self.lsl_type_label,1, 1)
        self.lsl_layout.addWidget(self.lsl_type, 2, 1)
        
        int_validator = QIntValidator()
        int_validator.setBottom(1)
        
        self.lsl_srate_label = QLabel("Sampling Rate [Hz]")
        self.lsl_srate = QLineEdit()
        self.lsl_srate.setPlaceholderText("Sampling Rate [Hz]")
        self.lsl_srate.setText("90")
        self.lsl_layout.addWidget(self.lsl_srate_label, 3, 0)
        self.lsl_layout.addWidget(self.lsl_srate, 4, 0)
        self.lsl_srate.setValidator(int_validator)
        self.lsl_n_channels_label = QLabel("Number of channels")
        self.lsl_n_channels = QLineEdit()
        self.lsl_n_channels.setPlaceholderText("Number of channels")
        self.lsl_n_channels.setText(str(sum(1 for _, state in self.lsl_properties.data_to_stream if state)))
        self.lsl_n_channels.setToolTip("Select data to stream to change the number of channels")
        self.lsl_n_channels.setReadOnly(True)
        self.lsl_layout.addWidget(self.lsl_n_channels_label, 3, 1)
        self.lsl_layout.addWidget(self.lsl_n_channels, 4, 1)
        self.lsl_n_channels.setValidator(int_validator)
        self.layout.addLayout(self.lsl_layout)
        
        separator_frame3 = QFrame()
        separator_frame3.setFrameShape(QFrame.Shape.HLine)
        separator_frame3.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(separator_frame3)
        
        self.csv_layout = QGridLayout()
        self.csv_checkbox = QCheckBox("CSV File")
        self.csv_checkbox.setChecked(True)
        self.layout.addWidget(self.csv_checkbox)
        self.csv_directory = QLineEdit()
        current_directory = os.getcwd()
        csv_directory = os.path.join(current_directory, 'output')
        self.csv_directory.setText(csv_directory)
        self.csv_directory.setReadOnly(True)
        self.csv_layout.addWidget(self.csv_directory, 0, 0)
        self.browse_button = QPushButton()
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirOpenIcon)
        self.browse_button.setIcon(icon)
        self.csv_filename = QLineEdit()
        self.csv_filename.setPlaceholderText("CSV filename")
        self.csv_layout.addWidget(self.csv_filename, 1, 0)
        self.browse_button.clicked.connect(self.browse_folder)
        self.csv_checkbox.clicked.connect(lambda: (self.csv_filename.setEnabled(not self.csv_filename.isEnabled()),
                                                    self.browse_button.setEnabled(not self.browse_button.isEnabled())))
        self.csv_layout.addWidget(self.browse_button, 0, 1)
        self.layout.addLayout(self.csv_layout)
        
        separator_frame4 = QFrame()
        separator_frame4.setFrameShape(QFrame.Shape.HLine)
        separator_frame4.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(separator_frame4)
        
        # Create and add the checkbox
        self.serial_checkbox = QCheckBox("Send data through Serial")
        self.serial_checkbox.setChecked(True)
        self.serial_checkbox.clicked.connect(lambda: {
            self.toogle.setEnabled(self.serial_checkbox.isChecked()),
            self.serial_combobox.setEnabled(self.serial_checkbox.isChecked()),
            self.baudrate_combobox.setEnabled(self.serial_checkbox.isChecked())
        })
        self.layout.addWidget(self.serial_checkbox)
        
        # Create and add the label above the combo boxes
        self.label = QLabel("Select Serial Port and Baud Rate:")
        self.layout.addWidget(self.label)

        # Create and add the dropdown (combobox) for selecting serial COM port
        self.serial_combobox = QComboBox()
        for i in range(1, 21):
            self.serial_combobox.addItem("COM" + str(i))
        self.serial_combobox.setFixedWidth(75)

        # Create and add the dropdown (combobox) for selecting baud rates
        self.baudrate_combobox = QComboBox()
        baud_rates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
        self.baudrate_combobox.addItems(baud_rates)
        self.baudrate_combobox.setFixedWidth(80)
        
        comp_label = QLabel()
        comp_label.setText("Complementary Filter")
        comp_label.setFixedWidth(118)
        comp_label.setMargin(2)
        self.toogle = AnimatedToggle()
        self.toogle.setFixedSize(self.toogle.sizeHint())
        self.toogle.setChecked(True)
        kalman_label = QLabel()
        kalman_label.setText("Kalman Filter")
        self.toogle.stateChanged.connect(self.change_complementary_kalman)
        # Create a horizontal layout for the combo boxes
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.serial_combobox)
        hbox_layout.addWidget(self.baudrate_combobox)
        hbox_layout.addWidget(comp_label)
        hbox_layout.addWidget(self.toogle)
        hbox_layout.addWidget(kalman_label)
        hbox_layout.addStretch()  # Add a stretch to align combo boxes to the left

        # Add the horizontal layout to the main layout
        self.layout.addLayout(hbox_layout)
        
        separator_frame5 = QFrame()
        separator_frame5.setFrameShape(QFrame.Shape.HLine)
        separator_frame5.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(separator_frame5)
        
        # Add the grid layout to the main layout
        self.start_button = QPushButton()
        self.start_button.setText("Start")
        self.start_button.clicked.connect(self.start_BLE)
        self.start_button.setEnabled(False)
        self.layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton()
        self.stop_button.setText("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_all)
        self.layout.addWidget(self.stop_button)
        
        self.clear_terminal_button = QPushButton()
        self.clear_terminal_button.setText("Clear Terminal")
        self.clear_terminal_button.setFixedSize(100, 25)
        self.clear_terminal_button.clicked.connect(lambda: self.terminal.clear())
        self.layout.addWidget(self.clear_terminal_button)
        
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.layout.addWidget(self.terminal)
                       
        self.threadpool = QThreadPool()    
    
        self.refresh_devices()
    
    def open_data_selector(self):
        if not self.data_selector:
            self.data_selector = DataSelector(self)
        self.data_selector.show()

    def retrieve_lsl_data_to_stream(self, data):
        self.lsl_properties.data_to_stream = data
        self.lsl_n_channels.setText(str(sum(1 for _, state in data if state)))
        
    
    def change_complementary_kalman(self):
        self.config.kalman = self.toogle.isChecked()
        if hasattr(self, 'ble_lsl_streamer_task'):
            self.ble_lsl_streamer_task.change_complementary_kalman(self.config.kalman)
        

          
    def refresh_devices(self):
        if self.ble_to_lsl_running or self.device_waiting:
            self.ble_lsl_streamer_task.stop_and_disconnect()
        self.scanner_task = BLEScanner()
        self.refresh_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.scanner_task.signals.finished.connect(self.update_devices)
        self.scanner_task.signals.error.connect(self.show_error)
        self.scanner_task.signals.running.connect(lambda new_value: setattr(self, 'scanner_running', new_value))
        self.threadpool.start(self.scanner_task)
        self.info_label.setText("Scanning for devices...")
        
    def update_devices(self, devices):
        if devices:
            self.devices = devices
            blocker = QSignalBlocker(self.devices_dropdown)
            self.devices_dropdown.clear()
            self.devices_dropdown.addItems([device.name for device in devices])
            self.devices_dropdown.setCurrentIndex(-1)
            self.devices_dropdown.showPopup() 
            del blocker
            #If devices are added to the list or the user selects a device, it triggers get_services()
        self.refresh_button.setEnabled(True)
        self.info_label.setText("Select your BLE device")
        
    def get_current_device(self):
        index = self.devices_dropdown.currentIndex()
        if index != -1:
            return self.devices[index]
        else:
            return None
    
    def get_services(self):
        self.terminal.appendPlainText("Waiting for the device to become ready...")
        device = self.get_current_device()
        if self.device_waiting:
            self.ble_lsl_streamer_task.update_device_status()
        self.ble_lsl_streamer_task = BLEtoLSLStreamer(device)
        self.ble_lsl_streamer_task.signals.services.connect(self.update_services)
        self.ble_lsl_streamer_task.signals.waiting.connect(lambda new_state: self.update_state_variables('device_waiting', new_state))
        self.ble_lsl_streamer_task.signals.started.connect(lambda new_state: self.update_state_variables('started', new_state))
        self.ble_lsl_streamer_task.signals.running.connect(lambda new_state: self.update_state_variables('ble_to_lsl_running', new_state))
        self.ble_lsl_streamer_task.signals.error.connect(self.show_error)
        self.ble_lsl_streamer_task.update_device_status()
        self.services_dropdown.setEnabled(False)
        self.characteristics_dropdown.setEnabled(False)
        self.services_dropdown.clear()
        
        self.threadpool.start(self.ble_lsl_streamer_task)

    def update_state_variables(self, variable, new_state):
        if variable == "device_waiting":
            self.device_waiting = new_state
        elif variable == "started":
            self.started = new_state
        elif variable == "ble_to_lsl_running":
            self.ble_to_lsl_running = new_state
        if not self.ble_to_lsl_running and not self.device_waiting:
            self.start_button.setEnabled(True)
            
    def update_services(self, services):
        self.services = services[::-1]
        services_list = []
        for service in self.services:
            service_string = f"{service.uuid} ({service.description})"
            services_list.append(service_string)
        self.services_dropdown.clear()
        self.services_dropdown.addItems(services_list)
        index = self.services_dropdown.currentIndex()
        self.service_selected = self.services[index]
        self.services_dropdown.setEnabled(True)
        #If services are added to the list or the user selects a service, it triggers update_characteristics()
        
    def update_characteristics(self):
        index = self.services_dropdown.currentIndex()
        service = self.services[index]
        if service is not None:
            self.characteristics = service.characteristics
            characteristics_list = []
            for characteristic in self.characteristics:
                characteristics_list.append(characteristic.description)
            self.characteristics_dropdown.clear()
            self.characteristics_dropdown.addItems(characteristics_list)
            self.characteristics_dropdown.setEnabled(True)
            if characteristics_list and not self.start_button.isEnabled():
                QTimer.singleShot(1000, lambda: (self.start_button.setEnabled(True),
                                                 self.stop_button.setEnabled(True), 
                                                 self.terminal.appendPlainText("READY!")))
                
    def get_current_characteristic(self):
        index = self.characteristics_dropdown.currentIndex()
        if index != -1:
            return self.characteristics[index]
        else:
            return None
    
    def validate_inputs(self):
        invalid = False
        if self.lsl_properties.checked:
            invalid = self.lsl_properties.name == "" or self.lsl_properties.type == "" or self.lsl_properties.srate == 0 or self.lsl_properties.n_channels == 0
            if invalid:
                message = "Invalid or missing LSL Properties"
                self.show_error(message)
        return invalid
    
    def validate_filename(self):
        invalid = False
        if self.csv_checkbox.isChecked():
            invalid = self.csv_filename.text() == ""
            if invalid:
                message = "CSV filename can't be blank"
                self.show_error(message)
        return invalid
    
    def start_BLE(self):
        self.lsl_properties.checked = self.lsl_checkbox.isChecked()
        self.lsl_properties.name = self.lsl_name.text()
        self.lsl_properties.type = self.lsl_type.text()
        self.lsl_properties.srate = self.lsl_srate.text()
        self.lsl_properties.n_channels = self.lsl_n_channels.text()
        inputErrors = self.validate_inputs() or self.validate_filename()
        filename = self.csv_directory.text() + "/" + self.csv_filename.text()
        filename = filename.replace(".csv", "") + ".csv"
        if platform.system() == 'Windows':
            filename = filename.replace('/', '\\')
        if not inputErrors:
            device = self.get_current_device()
            characteristic = self.get_current_characteristic()
            characteristic_uuid = characteristic.uuid
            self.config.characteristic_uuid = characteristic_uuid
            self.config.csv_checked = self.csv_checkbox.isChecked()
            self.config.filename = filename
            self.config.lsl_properties = self.lsl_properties
            self.config.serial = self.serial_checkbox.isChecked()
            self.config.serial_port = self.serial_combobox.currentText()
            self.config.baudrate = int(self.baudrate_combobox.currentText())
            self.ble_lsl_streamer_task.set_config(self.config)
            self.ble_lsl_streamer_task.start()
            if not self.started:
                self.ble_lsl_streamer_task = BLEtoLSLStreamer(device)
                self.ble_lsl_streamer_task.set_config(self.config)
                self.ble_lsl_streamer_task.start()
                self.threadpool.start(self.ble_lsl_streamer_task)
            
            
            self.ble_lsl_streamer_task.signals.received.connect(self.terminal.appendPlainText)
            self.start_button.setEnabled(False)
            self.devices_dropdown.setEnabled(False)
            self.services_dropdown.setEnabled(False)
            self.characteristics_dropdown.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.lsl_checkbox.setEnabled(False)
            self.stop_button.setEnabled(True)
        
    def stop_all(self):
        if self.ble_to_lsl_running or self.device_waiting:
            self.ble_lsl_streamer_task.stop_and_disconnect()
        self.stop_button.setEnabled(False)
        self.info_label.setText("Disconnecting device...")
        QTimer.singleShot(3000, lambda: (self.start_button.setEnabled(True),
                                        self.devices_dropdown.setEnabled(True),
                                        self.services_dropdown.setEnabled(True),
                                        self.characteristics_dropdown.setEnabled(True),
                                        self.refresh_button.setEnabled(True),
                                        self.lsl_checkbox.setEnabled(True),
                                        self.info_label.setText("Select your Bluetooth BLE device")))

    def show_error(self, message):
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Error")
        error_box.setText(message)
        error_box.exec()
        QTimer.singleShot(1000, lambda: (self.stop_all()))

        
    def enable_lsl(self):
        self.lsl_properties.checked = not self.lsl_properties.checked 
        for i in range(self.lsl_layout.count()):
            item = self.lsl_layout.itemAt(i)
            if isinstance(item, QLayoutItem):
                if item.widget():
                    item.widget().setEnabled(not item.widget().isEnabled())  
                    
                    
    def browse_folder(self):
        directory = QFileDialog.getExistingDirectory(self, 'Hey! Select a Folder')
        if directory:
            self.csv_directory.setText(directory)  # Set the selected folder as the filename

    def closeEvent(self, event):
        if hasattr(self, 'ble_lsl_streamer_task'):
            self.ble_lsl_streamer_task.stop_and_disconnect()
            while self.ble_lsl_streamer_task.running:
                time.sleep(1)
        event.accept()

def create_output_directory(folder_name):
    current_directory = os.getcwd()
    directory_path = os.path.join(current_directory, folder_name)

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
        
def main():
    create_output_directory("output")
    app = QApplication(sys.argv)
    gui = BLEToLSLGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
