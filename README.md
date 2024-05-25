# Arduino_LSM9DS1_BLE_to_LSL

This repository is part of the course Project in Electromechanical Engineering from my Master in Electromechanical Engineering at Bruface (ULB-VUB). In addition to the code, STL files for 3D printing the box and clamp to attach to a welding gun are included.

Arduino_LSM9DS1_BLE_to_LSL provides code for sending IMU data from the Arduino Nano 33 BLE (also Sense) to a central device running Python through BLE notify. The program implements a Complementary Filter to estimate the angular position and a Kalman Filter to estimate the angular position and velocity. Data can be saved to a CSV file, selected for sending to an LSL network, and sent via serial communication to visualize the angular position in 3D using Processing 4.3.

The scripts have been developed for Python 3.12.2.

## Installation
1. Download or clone this repository.
2. Download the V2 version of the [Arduino_LSM9DS1 library](https://github.com/FemmeVerbeek/Arduino_LSM9DS1).
3. Navigate to `Arduino_LSM9DS1_BLE_to_LSL_Central_Device` and use the package manager [pip](https://pip.pypa.io/en/stable/) to install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. To visualize the rotation of the device in 3D, download the software from [Processing](https://processing.org/download). The script for Processing 4.3 is available in this repository.

## Calibration of Accelerometer and Gyroscope
1. Watch the tutorial video from the developer of the V2 [Arduino_LSM9DS1 library](https://github.com/FemmeVerbeek/Arduino_LSM9DS1).
   - If you don't need to calibrate through Bluetooth, follow his instructions and skip the next steps.
2. Open the `Arduino_LSM9DS1_Accel_Gyro_BLE_Calibration.ino` file and upload it to your Arduino board.
3. Run the Python script `lsm9ds1_accel_gyro_ble_calibration.py`:
    ```bash
    python lsm9ds1_accel_gyro_ble_calibration.py
    ```
    Follow the calibration steps displayed in the terminal.
4. Open the `Arduino_LSM9DS1_to_BLE.ino` file and paste the Offset and Slope values provided by the calibration script into the `setup()` function.
5. Upload the code to the Arduino board.

## Usage
1. Turn on your Arduino board and calibrate the magnetometer by spinning it in all directions until the LED turns green. You can recalibrate it by pressing the push button or resetting the board.
2. Open the folder `Arduino_LSM9DS1_BLE_to_LSL_Central_Device` in your IDE and run:
    ```bash
    python main.py
    ```
    - If debugging is needed, manually insert `breakpoint()` before the desired line, as `asyncio` is used.
    - Once the program starts, refresh if your BLE device does not appear on the list, select the device, service, and characteristic. Set the desired outputs and click start.
    - The whole repository is designed to work with an Arduino Nano 33 BLE (Sense) and the LSM9DS1 IMU. The Python program expects a byte-array containing 10 floats (9-DOF IMU + millis()). To send data in a different format, modify both the Arduino firmware and the Python code.
3. To send data via serial communication from your central device to another software, create a virtual serial port using [ETERLOGIC VIRTUAL SERIAL PORTS EMULATOR](https://eterlogic.com/Products.VSPE.html). Then, specify the port and baud rate in the central device's GUI.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss the proposed changes.
