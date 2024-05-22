#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>

// Custom UUIDs for IMU Service and Characteristics
BLEService IMUService("19B10000-E8F2-537E-4F6C-D104768A1214");  // Custom UUID for IMU Service
BLECharacteristic IMUCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 40, false);  // Custom UUID for Accelerometer Data Characteristic

int Ts = 8;
float accX, accY, accZ ,gyroX, gyroY, gyroZ, mX, mY, mZ;
float m_offset_x, m_offset_y, m_offset_z;
float m_scale_x = 1.0; 
float m_scale_y = 1.0;
float m_scale_z = 1.0;
uint8_t elapsedTime;
unsigned long before;
unsigned long after;

#define POWER_LED 3
#define RED_LED 6
#define GREEN_LED 8
#define BLUE_LED 10
#define PUSH_BUTTON 2


void setup() {
  Serial.begin(9600); 
  
  pinMode(POWER_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);  
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);
  pinMode(PUSH_BUTTON, INPUT_PULLUP);

  digitalWrite(POWER_LED, HIGH);
  
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  //Perform the calibration of the Accelerometer and Gyroscope and paste the offsets and slopes here

  IMU.accelOffset[0] = -0.020826;   IMU.accelOffset[1] = -0.021961;   IMU.accelOffset[2] = -0.003005;
  IMU.accelSlope[0] = 0.996597;     IMU.accelSlope[1] = 0.993784;     IMU.accelSlope[2] = 0.997720;
  IMU.gyroOffset[0] = 2.633362;     IMU.gyroOffset[1] = 1.267822;     IMU.gyroOffset[2] = 1.955811;
  IMU.gyroSlope[0] = 1.151848;      IMU.gyroSlope[1] = 1.149317;      IMU.gyroSlope[2] = 1.132921;

  IMU.setMagnetODR(8);  //Set magnetometer Sampling Freq. to 400Hz

  magnetCalibration();

  BLE.setLocalName("IMUSensor");
  BLE.setAdvertisedService(IMUService);
  IMUService.addCharacteristic(IMUCharacteristic);
  BLEDescriptor imuDescriptor("2901", "IMU: Accelerometer, Gyroscope and Magnetometer");
  IMUCharacteristic.addDescriptor(imuDescriptor);
  BLE.addService(IMUService);  // Add the battery service


  BLE.setConnectionInterval(0x0006, 0x0006);  // 7.5 ms minimum, 4 s maximum. Here is set at 7.5 ms min and max
  BLE.advertise();

  Serial.println("Bluetooth® device active, waiting for connections...");
}

void loop() {
  // wait for a Bluetooth® Low Energy central
  BLEDevice central = BLE.central();

  digitalWrite(BLUE_LED, (millis()/2000)%2);

  if(!digitalRead(PUSH_BUTTON)) {   //trigger magnetometer calibration
    magnetCalibration();
  }

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    while (central.connected()) {
      digitalWrite(BLUE_LED, (millis()/500)%2);
      if (IMUCharacteristic.subscribed()) {
        digitalWrite(BLUE_LED, HIGH);
          while (IMUCharacteristic.subscribed()) {
          before = millis();
          readIMU();
          sendDataBLE();
          after = millis();
          elapsedTime = after - before;
          if (elapsedTime <= Ts + 4) {
            delay(4 + Ts - elapsedTime);
          }
        }   
      }
    }

    if (BLE.connected()) {
      BLE.disconnect();
    }
    // when the central disconnects, turn off the LED:
    digitalWrite(BLUE_LED, LOW);
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
    delay(3000);
  }
}

void readIMU() {
  IMU.readGyroscope(gyroX, gyroY, gyroZ);
  gyroY = -gyroY;

  IMU.readAcceleration(accX, accY, accZ);
  accY = - accY;

  IMU.readMagnet(mX, mY, mZ);
  mX = (mX - m_offset_x) * m_scale_x;
  mY = (mY - m_offset_y) * m_scale_y;
  mZ = (mZ - m_offset_z) * m_scale_z;
}

void sendDataBLE() {

  float imuData[10]; //Data from the 9-DOF IMU + millis()
  imuData[0] = accX;
  imuData[1] = accY;
  imuData[2] = accZ;
  imuData[3] = gyroX;
  imuData[4] = gyroY;
  imuData[5] = gyroZ;
  imuData[6] = mX;
  imuData[7] = mY;
  imuData[8] = mZ;
  imuData[9] = (float) before;

  // Encode the sampled data into a binary format
  uint8_t buffer[sizeof(imuData)];
  memcpy(buffer, &imuData, sizeof(imuData));

  // Send the encoded data as a BLE notification
  IMUCharacteristic.writeValue(buffer, sizeof(buffer));
}

void magnetCalibration() {
  float  mX, mY, mZ, min_x, min_y, min_z, max_x, max_y, max_z;
  digitalWrite(BLUE_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);
  delay(3000);
  for (int i=0; i<1000; i++) {
  digitalWrite(RED_LED, (millis()/250)%2);
  if (IMU.magnetAvailable()) {
    IMU.readMagnet(mX, mY, mZ);
  }
  Serial.print("Mag: (");
  Serial.print(mX); Serial.print(", ");
  Serial.print(mY); Serial.print(", ");
  Serial.print(mZ); Serial.print(")");

  min_x = min(min_x, mX);
  min_y = min(min_y, mY);
  min_z = min(min_z, mZ);

  max_x = max(max_x, mX);
  max_y = max(max_y, mY);
  max_z = max(max_z, mZ);

  // Calculate hard iron offset
  m_offset_x = (max_x + min_x) / 2;
  m_offset_y = (max_y + min_y) / 2;
  m_offset_z = (max_z + min_z) / 2;

  // Calculate soft iron scale factors
  m_scale_x = 2 / (max_x - min_x);
  m_scale_y = 2 / (max_y - min_y);
  m_scale_z = 2 / (max_z - min_z);
  
  Serial.print(" Hard offset: (");
  Serial.print(m_offset_x); Serial.print(", ");
  Serial.print(m_offset_y); Serial.print(", ");
  Serial.print(m_offset_z); Serial.print(")");  

  Serial.print(" Field: (");
  Serial.print((max_x - min_x)/2); Serial.print(", ");
  Serial.print((max_y - min_y)/2); Serial.print(", ");
  Serial.print((max_z - min_z)/2); Serial.println(")");    
  delay(10); 
  }
  digitalWrite(RED_LED, LOW);
  delay(500);
  for (int i=0 ; i<3; i++) {
    digitalWrite(GREEN_LED, HIGH);
    delay(100);
    digitalWrite(GREEN_LED, LOW);
    delay(500);
  }
  digitalWrite(GREEN_LED, HIGH);
  delay(2000);
  digitalWrite(GREEN_LED, LOW);
  delay(1000);
}