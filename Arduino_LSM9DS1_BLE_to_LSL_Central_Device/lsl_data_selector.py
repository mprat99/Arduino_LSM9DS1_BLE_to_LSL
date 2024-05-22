from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QDialog, QPushButton
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class LSLDataSignals(QObject):
    change = pyqtSignal(list)
    
class DataSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select LSL Data to Stream")
        self.setGeometry(200, 200, 400, 300)
        
        self.signals = LSLDataSignals()
        
        # Layout
        layout = QVBoxLayout()

        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemChanged.connect(self.handleItemChanged)
        layout.addWidget(self.tree_widget)
        

        # Add button
        self.button = QPushButton("Accept")
        self.button.clicked.connect(self.accept)
        layout.addWidget(self.button)

        self.populateTree()

        self.setLayout(layout)
    
    def accept(self):
        self.signals.change.emit(self.getSelectedChildStates())
        self.close()

    def populateTree(self):
        # Add root items
        parents = ["Raw data", "Single Sensor angle estimation", "Complementary Filter", "Kalman Filter"]
        accelerometer = ["AccX", "AccY", "AccZ"]
        gyroscope = ["GyroX", "GyroY", "GyroZ"]
        magnet = ["MagX", "MagY", "MagZ"]
        accelerometer_angles = ["Acc \u03B8", "Acc \u03C6"]
        gyroscope_angles = ["Gyro \u03B8", "Gyro \u03C6", "Gyro \u03C8"]
        magnetometer_angle = ["Mag \u03C8"]
        complementary = ["Complementary \u03B8", "Complementary \u03C6", "Complementary \u03C8"]
        kalman = ["Kalman \u03B8", "Kalman \u03C6", "Kalman \u03C8", "Kalman \u03C9_\u03B8", "Kalman \u03C9_\u03C6", "Kalman \u03C9_\u03C8"]
        parent_items = ["", "", "", ""]
        
        for i in range(4):
            parent_items[i] = QTreeWidgetItem(self.tree_widget, [parents[i]])
            parent_items[i].setCheckState(0, Qt.CheckState.Checked)

        accelerometer_item = QTreeWidgetItem(parent_items[0], ["Accelerometer"])
        accelerometer_item.setCheckState(0, Qt.CheckState.Checked)  
        for j in range(3):
            child_item = QTreeWidgetItem(accelerometer_item, [accelerometer[j]])
            child_item.setCheckState(0, Qt.CheckState.Checked) 
            
        gyroscope_item = QTreeWidgetItem(parent_items[0], ["Gyroscope"])
        gyroscope_item.setCheckState(0, Qt.CheckState.Checked)  
        for j in range(3):
            child_item = QTreeWidgetItem(gyroscope_item, [gyroscope[j]])
            child_item.setCheckState(0, Qt.CheckState.Checked) 
            
        magnet_item = QTreeWidgetItem(parent_items[0], ["Magnetometer"])
        magnet_item.setCheckState(0, Qt.CheckState.Checked)  
        for j in range(3):
            child_item = QTreeWidgetItem(magnet_item, [magnet[j]])
            child_item.setCheckState(0, Qt.CheckState.Checked) 
            
        accelerometer_angles_item = QTreeWidgetItem(parent_items[1], ["Accelerometer angles"])
        accelerometer_angles_item.setCheckState(0, Qt.CheckState.Checked)
        for j in range(2):
            child_item = QTreeWidgetItem(accelerometer_angles_item, [accelerometer_angles[j]])
            child_item.setCheckState(0, Qt.CheckState.Checked)
            
        gyroscope_angles_item = QTreeWidgetItem(parent_items[1], ["Gyroscope angles"])
        gyroscope_angles_item.setCheckState(0, Qt.CheckState.Checked)
        for j in range(3):
            child_item = QTreeWidgetItem(gyroscope_angles_item, [gyroscope_angles[j]])
            child_item.setCheckState(0, Qt.CheckState.Checked)
        
        magnetometer_angle_item = QTreeWidgetItem(parent_items[1], ["Magnetometer angles"])
        magnetometer_angle_item.setCheckState(0, Qt.CheckState.Checked)
        child_item = QTreeWidgetItem(magnetometer_angle_item, [magnetometer_angle[0]])
        child_item.setCheckState(0, Qt.CheckState.Checked)  
        
        for j in range(3):
            child_item = QTreeWidgetItem(parent_items[2], [complementary[j]])
            child_item.setCheckState(0, Qt.CheckState.Checked) 
            
        for j in range(6):
            child_item = QTreeWidgetItem(parent_items[3], [kalman[j]])
            child_item.setCheckState(0, Qt.CheckState.Checked) 
        

    def handleItemChanged(self, item, column):
        state = item.checkState(column)
        for i in range(item.childCount()):
            item.child(i).setCheckState(column, state)

    def getSelectedChildStates(self):
        def collect_leaf_states(item):
            if item.childCount() == 0:  # It's a leaf node
                child_text = item.text(0)
                child_state = item.checkState(0)
                child_state_bool = child_state == Qt.CheckState.Checked
                child_states.append((child_text, child_state_bool))
            else:
                for j in range(item.childCount()):
                    collect_leaf_states(item.child(j))

        child_states = []
        for i in range(self.tree_widget.topLevelItemCount()):
            root_item = self.tree_widget.topLevelItem(i)
            collect_leaf_states(root_item)

        return child_states