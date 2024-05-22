import asyncio
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal
from bleak import BleakScanner


class BLEScannerSignals(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    services = pyqtSignal(list)
    running = pyqtSignal(bool)

class BLEScanner(QRunnable):
    def __init__(self, device=None):
        super().__init__()
        self.signals = BLEScannerSignals()
        self.device = device
        self.running = False

    def run(self):
        self.running=True
        self.signals.running.emit(self.running)
        try:
            asyncio.run(self.scan_and_emit_devices())
        except Exception as e:
            print("Error:", e)
            self.signals.error.emit(str(e))
        finally:
            self.running=False
            self.signals.running.emit(self.running)


    async def scan_and_emit_devices(self):
        self.running = True
        self.signals.running.emit(self.running)
        try:
            devices = await self.scan_for_devices()
            self.running=False
            self.signals.running.emit(self.running)
            self.signals.finished.emit(devices)
        except Exception as e:
            print("Error:", e)
            self.signals.error.emit(str(e))
        finally:
            self.running = False
            self.signals.running.emit(self.running)
            
    async def scan_for_devices(self):
        try:
            scanner = BleakScanner()
            devices = await scanner.discover(timeout=2)
            return [d for d in devices if d.name is not None]
        except Exception as e:
            print("Error:", e)
        finally:
            self.running=False
