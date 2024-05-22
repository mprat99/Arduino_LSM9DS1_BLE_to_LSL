# Arduino_LSM9DS1_BLE_to_LSL

Arduino_LSM9DS1_BLE_to_LSL is a repository where you will find the code for sending IMU data from the Arduino Nano 33 BLE (also Sense) to a central device running Python through BLE notify. The program implements a Complementary Filter to estimate the angular position of the device and a Kalman Filter to estimate the angular position and velocity of the device. You can save the data to a csv file,  select which data to send to a LSL network and send the data via serial communication, to a Processing 4.3 script for example, to visualize the angular position in 3D.

The scripts have been developed on Python 3.12.2

## Installation
1. Dowload or clone this repository
2. Go to [Arduino_LSM9DS1](https://github.com/FemmeVerbeek/Arduino_LSM9DS1) to download the V2 version of the Arduino_LSM9DS1 library.

3. Go to Arduino_LSM9DS1_BLE_to_LSL_Central_Device and use the package manager [pip](https://pip.pypa.io/en/stable/) to install the required dependencies.

```bash
pip install -r requirements.txt
```
4. If you want to visualize the rotation of the device in 3D, go to the website of [Processing](https://processing.org/download) to download their software. My script for Processing 4.3 is available in this repository.
## Calibration of Accelerometer and Gyroscope
1. Watch the tutorial video from the developer of the V2 [Arduino_LSM9DS1](https://github.com/FemmeVerbeek/Arduino_LSM9DS1) library.
If you don't need to calibrate through Bluetooth, you can follow his instructions and skip the next steps.

2. Open the Arduino_LSM9DS1_Accel_Gyro_BLE_Calibration.ino file and upload it to your Arduino board.

3. Run the Python script lsm9ds1_accel_gyro_ble_calibration.py
```bash
python lsm9ds1_accel_gyro_ble_calibration.py
```
You should see something like this, follow the calibration steps.
```bash
"""
Step 1       Calibrate Accelerometer Offset and Slope
 Place the board on a horizontal surface with one of its axes vertical and hit enter to start a calibration
 measurement. Each of the axes must be measured pointing up and pointing down, so a total of 6 measurements.
 The program recognises which axis is vertical and shows which were measured successfully. If the angle is too
 far oblique the measurement is not valid.\n  

 ...
```
4. Open the Arduino_LSM9DS1_to_BLE.ino file and paste in the setup() function the Offset and Slope values provided on the calibration script.

5. Upload the code to the Arduino board.

## Usage
1. Turn on your Arduino Board and calibrate the magnetometer by spinning it in all directions, similarly as what you would do to calibrate the compass of your phone, until the LED turns Green. You can recalibrate it by pressing the push button or simply resetting the board.

2. Open the folder Arduino_LSM9DS1_BLE_to_LSL_Central_Device on your IDE and run it with:
```bash
python main.py
```
You can also debug it but if you need breakpoints, as asyncio is used, you will need to manually write breakpoint() before the desired line and re-debug the code.

Once the program has started, refresh if your BLE device does not appear on the list, select the device, service and characteristic. Set the desired outputs and click start.

The whole repository is meant to work with an Arduino Nano 33 BLE (sense) and the LSM9DS1 IMU. The Python program expects to receive through BLE a byte-array containing 10 floats (9-DOF IMU + millis()). If you want to send data in a different format, you will need to modify both the Arduino firmware and the python code.

3. If you want to send data via serial communication from your central device to another software, you can create a virtual serial port. I used [ETERLOGIC VIRTUAL SERIAL PORTS EMULATOR](https://eterlogic.com/Products.VSPE.html). Then you will need to specify the port and baudrate in the GUI of the central device.

## Contributing
Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
