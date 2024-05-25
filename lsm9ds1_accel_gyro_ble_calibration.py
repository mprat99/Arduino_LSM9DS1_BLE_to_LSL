import asyncio
from bleak import BleakClient, BleakScanner
import struct
import functools
import time

CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"

DEVICE_NAME = "LSM9DS1 Calibration"  # Replace with your Arduino BLE device name

command_sent = ""
acc_axis = 0
gyr_axis = 0
accelOffset = ""
accelSlope = ""
gyroOffset = ""
gyroSlope = ""

async def write_command(client):
    global command_sent
    # while True:
    command = input("Enter command (A: Calibrate Accelerometer, O: Calibrate Gyroscope Offset, S: Calibrate Gyroscope Slope,P: Print Summary, T: Test, Q: Quit): ").strip().upper()
    if command == "Q":
        exit()
    elif command == "P":
        print("\n")
        print(accelOffset)
        print(accelSlope)
        print(gyroOffset)
        print(gyroSlope)
        print("\n")
    else:
        await client.write_gatt_char(CHARACTERISTIC_UUID, command.encode())
        command_sent = command
        print("Command sent:", command)
    
        print("\n")
        if command == "S":
            print("Rotate the device 180º very slowly before 10s")
            for i in range(10, 0, -1):
                print(f"\r{' ' * 10}", end='', flush=True)
                print(f"\r{i}", end='', flush=True)
                time.sleep(0.9)
            print("\n")
        else:
            print("Measuring ", end='', flush=True)
            for i in range(15):
                print(".", end='', flush=True)
                time.sleep(0.3)
            print("\n")
            

async def read_messages(sender, client, data):
    global command_sent, acc_axis, gyr_axis, accelOffset, accelSlope, gyroOffset, gyroSlope
    if len(data) >1:
        try:
            # breakpoint()
            result = struct.unpack("<ffffff", data)
            sample = list(result)
            if all(isinstance(elem, float) and elem == 0.0 for elem in sample):
                    print("Invalid Measurement: Try again")
            else:
                if command_sent == "A":
                    acc_axis += 1
                    print("Positions measured: " + str(acc_axis) + "    Positions missing: " + str(6-acc_axis))
                    accelOffset = "IMU.accelOffset[0] = " + "{:.6f}".format(sample[0]) + ";   ""IMU.accelOffset[1] = " + "{:.6f}".format(sample[1]) + ";   ""IMU.accelOffset[2] = " + "{:.6f}".format(sample[2]) + ";   "
                    accelSlope = "IMU.accelSlope[0] = " + "{:.6f}".format(sample[3]) + ";   ""IMU.accelSlope[1] = " + "{:.6f}".format(sample[4]) + ";   ""IMU.accelSlope[2] = " + "{:.6f}".format(sample[5]) + ";   "
                    print(accelOffset)
                    print(accelSlope)
                elif command_sent == "O":
                    gyroOffset = "IMU.gyroOffset[0] = " + "{:.6f}".format(sample[0]) + ";   ""IMU.gyroOffset[1] = " + "{:.6f}".format(sample[1]) + ";   ""IMU.gyroOffset[2] = " + "{:.6f}".format(sample[2]) + ";   "
                    print(gyroOffset)
                elif command_sent == "S":
                    gyr_axis += 1
                    print("Rotations measured: " + str(gyr_axis) + "    Rotations missing: " + str(3-gyr_axis))
                    gyroSlope = "IMU.gyroSlope[0] = " + "{:.6f}".format(sample[3]) + ";   ""IMU.gyroSlope[1] = " + "{:.6f}".format(sample[4]) + ";   ""IMU.gyroSlope[2] = " + "{:.6f}".format(sample[5]) + ";   "
                    print(gyroSlope)
                if command_sent == "T":
                    print(sample)
            await write_command(client)
        except Exception as e:
            print("Error:", str(e))

async def read_messages_wrapper(sender, data, client):
    await read_messages(sender, client, data)

async def connect_and_write():
    global DEVICE_NAME
    global instructions
    print(instructions)
    print("Connecting to device...")
    scanner = BleakScanner()
    devices = await scanner.discover(timeout=2)
    devices = [d for d in devices if d.name is not None]
    for device in devices:
        if DEVICE_NAME in device.name:
            async with BleakClient(device) as client:
                callback = functools.partial(read_messages_wrapper, client=client)
                await client.start_notify(CHARACTERISTIC_UUID, callback)
                await write_command(client)
                while client.is_connected:
                    await asyncio.sleep(0)
                break
    else:
        print(f"Device with name {DEVICE_NAME} not found.")

instructions = """
Step 1       Calibrate Accelerometer Offset and Slope
 Place the board on a horizontal surface with one of its axes vertical and hit enter to start a calibration
 measurement. Each of the axes must be measured pointing up and pointing down, so a total of 6 measurements.
 The program recognises which axis is vertical and shows which were measured successfully. If the angle is too
 far oblique the measurement is not valid.\n  

Step 2       CALIBRATE GYROSCOPE OFFSET
First choose the sample frequency (ODR) and the Full Scale value. The accelerometer and the gyroscope
share their ODR, so the setting here must be the same as in the DIY_Calibration_Gyroscope sketch.
This is far more important for the Gyroscope than for the accelerometer.
Next enter "O" to start the gyroscope offset measurement. 
During this offset measurement the sensor must be kept still.

Step 3       CALIBRATE GYROSCOPE SLOPE
During a slope calibration the sensor must be rotated calmly about one axis over a known angle.
Change the angle to your convenience. A larger angle is more accurate, but more difficult to do.
The rotation must be pure, without much rotation about the other two axes. It can be done by hand.
Keeping the board on a flat surface with the rotation axis vertical while turning is good enough.
For an accurate result you can start and end with its side pushed against a non moving object.
When you're done turning the sensor, press (Enter) to stop measuring. Each of the axes X,Y and Z
must be measured. The program automatically detects which.
"""


asyncio.run(connect_and_write())