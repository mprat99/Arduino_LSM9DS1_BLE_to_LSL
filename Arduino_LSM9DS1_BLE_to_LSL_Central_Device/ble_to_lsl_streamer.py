import time
import asyncio
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from bleak import BleakClient
from bleak.exc import BleakError
from datetime import datetime
from pylsl import StreamInfo, StreamOutlet
import struct
import serial
from imu_processor import IMUProcessor
from csv_writer import CSVWriter

class BLEtoLSLStreamerSignals(QObject):
    running = pyqtSignal(bool)
    waiting = pyqtSignal(bool)
    started = pyqtSignal(bool)
    services = pyqtSignal(list)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    received = pyqtSignal(str)
    

class LSLProperties():
    def __init__(self):
        self.checked: bool = False
        self.name: str = ""
        self.type: str = ""
        self.srate: int = 0
        self.n_channels: int = 0
        self.id = ""
        self.data_to_stream = [('AccX', True), ('AccY', True), ('AccZ', True), 
                               ('GyroX', True), ('GyroY', True), ('GyroZ', True),
                               ('MagX', True), ('MagY', True), ('MagZ', True), 
                               ('Acc θ', True), ('Acc φ', True), ('Gyro θ', True), 
                               ('Gyro φ', True), ('Gyro ψ', True), ('Mag ψ', True), 
                               ('Complementary θ', True), ('Complementary φ', True), ('Complementary ψ', True), 
                               ('Kalman θ', True), ('Kalman φ', True), ('Kalman ψ', True), ('Kalman ω_θ', True), ('Kalman ω_φ', True), ('Kalman ω_ψ', True)]
 
class ConfigProperties():
    def __init__(self):
        self.lsl_properties: LSLProperties
        self.filename = ""
        self.characteristic_uuid = ""
        self.csv_checked = ""
        self.serial = False  
        self.serial_port = ""   
        self.baudrate = 9600
        self.kalman = True  
        self.alpha = 0.05
    

class BLEtoLSLStreamer(QRunnable):
    def __init__(self, device):
        super().__init__()
        self.signals = BLEtoLSLStreamerSignals()
        self.device = device
        self.client: BleakClient = None
        self.config = ConfigProperties()
        self.device_waiting = False
        self.running = False
        self.started = False
        self.outlet = None
        self.millis = 0
        self.first_millis = 0
        self.first_data_index = 0
        self.samples_received = 0
        self.data_to_write = [["accX", "accY", "accZ", "gyrX", "gyrY", "gyrZ", "magX", "magY" , "magZ", "theta_acc", "phi_acc", "theta_gyro", "phi_gyro", "psi_gyro", "psi_mag" , 
                               "theta_comp", "phi_comp", "psi_comp", "theta_k", "phi_k", "psi_k", "w_theta_k", "w_phi_k", "w_psi_k", "Ts", "Freq."]]
        self.threadpool = QThreadPool()
        self.theta_gyro = 0.0
        self.phi_gyro = 0.0
        self.psi_gyro = 0.0
        self.theta_complementary = 0.0
        self.phi_complementary = 0.0
        self.psi_complementary = 0.0
        self.heading0 = None
        self.imu_processor = IMUProcessor()
        


    def run(self):
        try:
            asyncio.run(self.subscribe_to_notifications(), debug=True)
        except Exception as e:
            print("Error:", e)
            return
        finally:
            self.running = False
            self.device_waiting = False
            self.started = False
            self.signals.running.emit(self.running)
            self.signals.waiting.emit(self.device_waiting)
            self.signals.started.emit(self.started)
            return


        
    async def subscribe_to_notifications(self):
        try:
            async with BleakClient(self.device) as client:
                self.started = True
                self.signals.started.emit(self.started)
                if not client.is_connected:
                    print("Failed to connect to the Arduino Nano 33 BLE.")
                    return
                self.client = client
                self.services = self.client.services
                self.signals.services.emit(self.services)
                while self.device_waiting:
                    await asyncio.sleep(0)
                if self.running:
                    self.config.lsl_properties.id = client.address
                    if self.config.lsl_properties.checked:
                        await self.init_lsl(self.config.lsl_properties)
                    start_time = time.time()
                    self.previous_time = start_time
                    self.previous_ts = 0
                    await client.start_notify(self.config.characteristic_uuid, self.handle_data)
                    while self.running and client.is_connected:
                        await asyncio.sleep(0)
                    if self.config.csv_checked:
                        if self.data_to_write:
                            self.write_csv()
                        await asyncio.sleep(2)
                if client.is_connected:
                    if self.running:
                        await client.stop_notify(self.config.characteristic_uuid)
                    await client.disconnect()
                print("disconnected")

        except BleakError as e:
            print("Error:", e)
            self.signals.error.emit(str(e))
            return
        finally:
            self.running = False
        
        
        
    async def get_services(self, device):
        try:
            async with BleakClient(device) as client:
                self.client = client
                if not client.is_connected:
                    print("Failed to connect to the Arduino Nano 33 BLE.")
                    return
                self.services = self.client.services
                self.signals.finished.emit(self.services)
        except BleakError as e:
            print("Error: get_Services()", e)
            self.signals.error.emit(str(e))
            return
        finally:
            await self.client.disconnect()
            self.running=False
    
            
    def change_complementary_kalman(self, filter):
        self.config.kalman = filter      
        
        
    def change_alpha(self, alpha):
        self.imu_processor.alpha = alpha  
    
                
    # Function to handle data received from Arduino Nano 33 BLE
    def handle_data(self, sender, data):
        result = struct.unpack("<ffffffffff", data)
        sample = list(result)
        sample_length = len(sample)
        # calculate Ts based on the millis() data from the Arduino
        if self.previous_ts != 0:
            Ts = sample[sample_length - 1] - self.previous_ts
        else:
            Ts = 0
        self.previous_ts = sample.pop(sample_length - 1)
        sample = self.imu_processor.get_angular_position_and_speed(sample=sample, delta_t=Ts/1000.0)
        
        if self.config.serial:
            try:
                ser = serial.Serial(self.config.serial_port, self.config.baudrate, timeout=1)
                if self.config.kalman:
                    theta = sample[18]
                    phi = sample[19]
                    psi = sample[20]
                else:
                    theta = sample[15]
                    phi = sample[16]
                    psi = sample[17]

                ser.write(f"{theta},{phi},{psi}\n".encode())
            except Exception as e:
                pass
        
        message = f"{datetime.now()} Received: {result}"
        self.samples_received += 1
        self.signals.received.emit(message)
        if self.config.csv_checked:
            data_to_write = list(sample)
            data_to_write.append(Ts)
            if Ts != 0:
                data_to_write.append(1/Ts)
            else:
                data_to_write.append(0)
                    
            self.data_to_write.append(data_to_write)
            if len(self.data_to_write) == 500:
                self.write_csv()
        if self.config.lsl_properties.checked:
            sample_to_send = []
            for i, d in enumerate(self.config.lsl_properties.data_to_stream):
                if d[1]:
                    sample_to_send.append(sample[i])
            self.send_Data_LSL(sample_to_send)

     
    
    def write_csv(self):
        csv_writer_task = CSVWriter(self.config.filename, self.data_to_write)
        self.threadpool.start(csv_writer_task)
        self.data_to_write = []    
        
        
      
    async def init_lsl(self, lsl_properties: LSLProperties):
        srate = int(lsl_properties.srate)
        name = lsl_properties.name
        type = lsl_properties.type
        n_channels = int(lsl_properties.n_channels)
        id = lsl_properties.id
        info = StreamInfo(name, type, n_channels, srate, 'float32', id)
        self.outlet = StreamOutlet(info)
        print("Ready to stream data to LSL...")
      
      
      
    def send_Data_LSL(self, sample):
        self.outlet.push_sample(sample)
        
        
        
    def start(self):
        self.running = True
        self.device_waiting = False
        self.signals.waiting.emit(self.device_waiting)
        self.signals.running.emit(self.running)
        
        
        
    def stop_and_disconnect(self):
        self.imu_processor = IMUProcessor()
        self.device_waiting = False
        self.running = False
        
        
        
    def update_device_status(self):
        self.device_waiting = not self.device_waiting
        self.signals.waiting.emit(self.device_waiting)
        
        
        
    def set_config(self, config: ConfigProperties):
        self.config = config
        
        