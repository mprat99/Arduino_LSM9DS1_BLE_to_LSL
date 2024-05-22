import csv
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable

class CSVWriterSignals(QObject):
    error = pyqtSignal(str)
    services = pyqtSignal(list)
    running = pyqtSignal(bool)
    
class CSVWriter(QRunnable):
    def __init__(self, filename, data):
        super().__init__()
        self.data = data
        self.filename = filename
        self.signals = CSVWriterSignals()

    def run(self):
        with open(self.filename, 'a', newline='', encoding="utf-8") as csvfile:
            # writer = csv.writer(csvfile, delimiter=";") #change depending on your region settings
            writer = csv.writer(csvfile)
            for row in self.data:
                formatted_row = [f'{value:.4f}' if isinstance(value, float) else value for value in row]
                writer.writerow(formatted_row)
