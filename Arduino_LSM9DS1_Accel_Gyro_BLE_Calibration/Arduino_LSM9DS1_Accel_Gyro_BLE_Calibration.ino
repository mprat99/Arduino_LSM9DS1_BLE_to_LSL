
/*
This script is a modification and fusion of the calibration example scripts for the Accelerometer and Gyroscope of the LSM9DS1.
It usses the V2 Arduino_LSM9DS1 library from https://github.com/FemmeVerbeek/Arduino_LSM9DS1, follow the calibration video tutorial before using this script.
Some functions like changing the FS, ODR or NofCalibrationSamples by command are not available in this script but can be modified before uploading to the board.
This modification allows to calibrate the accelerometer and gyroscope through BLE sending commands using a Python script available at https://github.com/mprat99/Arduino_LSM9DS1_BLE_to_LSL

Written by Marc Prat Plana 20/05/2024
*/

#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h> 

const float accelCriterion = 0.1;
char xyz[3]= {'X','Y','Z'};
float maxAX = 1, maxAY=1, maxAZ=1, minAX=-1, minAY=-1, minAZ=-1; // Accel Slope
float zeroAX1 =0,zeroAX2 =0,zeroAY1 =0,zeroAY2 =0,zeroAZ1 =0,zeroAZ2 =0;  //Accel Offset
boolean accelOK=false;
uint8_t acceMMlOK=0; // bit 0..2 maxXYZ bit 3..5 minXYZ
uint8_t accelODRindex=5; // Sample Rate 0:off, 1:10Hz, 2:50Hz, 3:119Hz, 4:238Hz, 5:476Hz, (6:952Hz=na) 
uint8_t accelFSindex=3;   // Full Scale// 0: ±2g ; 1: ±24g ; 2: ±4g ; 3: ±8g
uint16_t NofCalibrationSamples = 1000;
const float gyroSlopeCriterion = 50;  //Smaller value requires more pureness of the rotation  
boolean gyroOffsetOK=false;
boolean gyroSlopeOK[3]={false,false,false};
float data[6];
uint8_t buffer[sizeof(data)];
boolean validMmt=false;


BLEService customService("19B10000-E8F2-537E-4F6C-D104768A1214"); // Custom BLE service
BLECharacteristic bidirectionalCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite | BLENotify, 24);

void setup() {
  Serial.begin(9600);

  // Start BLE
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

    // Start BLE
  if (!IMU.begin()) {
    Serial.println("Starting IMU failed!");
    while (1);
  }

  // Set advertised local name and service UUID
  BLE.setLocalName("LSM9DS1 Calibration");
  BLE.setAdvertisedService(customService);

  // Add characteristic to the service
  customService.addCharacteristic(bidirectionalCharacteristic);

  // Add the service
  BLE.addService(customService);

  // Start advertising
  BLE.advertise();

  Serial.println("BLE peripheral is now active, waiting for connections...");
}

void loop() {
  // Wait for a BLE central to connect
  BLEDevice central = BLE.central();
  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());
    
    while (central.connected()) {
      // Check for incoming commands
      if (bidirectionalCharacteristic.written()) {
        const uint8_t* command = bidirectionalCharacteristic.value();
        switch (command[0]) {
          case 'A':
            Serial.println("Received A");
            calibrateAccel(NofCalibrationSamples);
            if (!validMmt) {
              for (int i = 0; i < 6; i++) {
                  data[i] = 0.0;
                }
            }
            else {
                data[0] = IMU.accelOffset[0];
                data[1] = IMU.accelOffset[1];
                data[2] = IMU.accelOffset[2];
                data[3] = IMU.accelSlope[0];
                data[4] = IMU.accelSlope[1];
                data[5] = IMU.accelSlope[2];
            }
             // Encode the sampled data into a binary format
            memcpy(buffer, &data, sizeof(data));
            // Send the encoded data as a BLE notification
            bidirectionalCharacteristic.writeValue(buffer, sizeof(buffer));
            break;
          case 'O':
           Serial.println("Received O");
            calibrateGyroOffset(NofCalibrationSamples);
            data[0] = IMU.gyroOffset[0];
            data[1] = IMU.gyroOffset[1];
            data[2] = IMU.gyroOffset[2];
            data[3] = IMU.gyroSlope[0];
            data[4] = IMU.gyroSlope[1];
            data[5] = IMU.gyroSlope[2];
             // Encode the sampled data into a binary format
            memcpy(buffer, &data, sizeof(data));
            // Send the encoded data as a BLE notification
            bidirectionalCharacteristic.writeValue(buffer, sizeof(buffer));
            break;
          case 'S':
           Serial.println("Received S");
            calibrateGyroslope(180);
            if (!validMmt) {
              for (int i = 0; i < 6; i++) {
                  data[i] = 0.0;
                }
            }
            else {
                data[0] = IMU.gyroOffset[0];
                data[1] = IMU.gyroOffset[1];
                data[2] = IMU.gyroOffset[2];
                data[3] = IMU.gyroSlope[0];
                data[4] = IMU.gyroSlope[1];
                data[5] = IMU.gyroSlope[2];
            }
            
             // Encode the sampled data into a binary format
            memcpy(buffer, &data, sizeof(data));
            // Send the encoded data as a BLE notification
            bidirectionalCharacteristic.writeValue(buffer, sizeof(buffer));
            break;
          case 'T':
             Serial.println("Received T");
            float data[6];
            data[0] = IMU.gyroOffset[0];
            data[1] = IMU.gyroOffset[1];
            data[2] = IMU.gyroOffset[2];
            data[3] = IMU.gyroSlope[0];
            data[4] = IMU.gyroSlope[1];
            data[5] = IMU.gyroSlope[2];
             // Encode the sampled data into a binary format
            memcpy(buffer, &data, sizeof(data));
            // Send the encoded data as a BLE notification
            bidirectionalCharacteristic.writeValue(buffer, sizeof(buffer));
            break;
          default:  // 0 or invalid control
            Serial.println("STOP");
            break;
        }

      }

      // You can add more logic here if needed

      delay(10); // Don't hog the CPU
    }

    // Disconnect from the central
    Serial.println("Disconnected from central");
  }
}

void calibrateAccel(uint16_t NofSamples)
{  validMmt=false;
   float x,y,z;
   Serial.println(F("\n\n\n\n\n\n\n\n\n\n\n")); 
   Serial.println(F("measuring \n")); 
//   IMU.setAccelODR(5);  //476 Hz
   raw_N_Accel(NofSamples,x,y,z);
   if (abs(x)>max(abs(y),abs(z)))
   {    Serial.println(F("X detected"));  
       if (sqrt(y*y+z*z)/x<accelCriterion)
       {  validMmt= true;
          if (x>0) {maxAX=x; 
                    acceMMlOK=acceMMlOK | 0b00000001 ;}
          else     {minAX=x; 
                    acceMMlOK=acceMMlOK | 0b00001000 ; }
       }
   }
   if (abs(y)>max(abs(x),abs(z)))
   {  Serial.println(F("Y detected"));  
      if (sqrt(x*x+z*z)/y<accelCriterion)
       {  validMmt= true;
          if (y>0) {maxAY=y; 
                    acceMMlOK=acceMMlOK | 0b00000010 ; }
          else     {minAY=y; 
                    acceMMlOK=acceMMlOK | 0b00010000 ; }
       }  
   }
   if (abs(z)>max(abs(x),abs(y)))
   {  Serial.println(F("Z detected"));  
      if ( sqrt(x*x+y*y)/z<accelCriterion)
       {  validMmt= true;
          if (z>0) {maxAZ=z; 
                    acceMMlOK=acceMMlOK | 0b00000100 ; }
          else     {minAZ=z;
                    acceMMlOK=acceMMlOK | 0b00100000 ; }
       }  
   }
   IMU.setAccelOffset((maxAX+minAX)/2,(maxAY+minAY)/2,(maxAZ+minAZ)/2);
   IMU.setAccelSlope ((maxAX-minAX)/2,(maxAY-minAY)/2,(maxAZ-minAZ)/2);
   if (acceMMlOK==0b00111111) accelOK = true;
   
   if ( !validMmt ) 
    { Serial.print(F("\n\n\nNot a valid measurement!  "));
      Serial.println(" x=");Serial.print(x);Serial.print("  y=");Serial.print(y);Serial.println("  z=");Serial.print(z);
    }
}


void calibrateGyroOffset(uint16_t N)  // don't move the board during calibration
{  float x, y, z;// , addX=0, addY=0, addZ=0  ;
   Serial.println(F("\n\n\n\nMeasuring offset. Just a moment.")); 
   Serial.println(F("\n\nKeep the board still during measurement")); 
   raw_N_Gyro(N,x,y,z);
   IMU.setGyroOffset(x, y,z); // Store the average measurements as offset

   Serial.print("\n\n\n\n\n"); 
   gyroOffsetOK=true;
}   


void calibrateGyroslope(unsigned int turnangle)  // rotate board over known angle
{  validMmt=false;
   float dirX=0, dirY=0, dirZ=0,sigmaX2=0,sigmaY2=0,sigmaZ2=0;
   float x, y, z, maxXYZ;
   unsigned int count=0;
    unsigned long startTime = millis();
    while (millis() - startTime <= 10000) {
      while (!IMU.gyroAvailable());
       IMU.readRawGyro(x, y, z);
       dirX += (x - IMU.gyroOffset[0])/IMU.getGyroODR();    // slope is still raw but offset must already be calibrated 
       dirY += (y - IMU.gyroOffset[1])/IMU.getGyroODR(); 
       dirZ += (z - IMU.gyroOffset[2])/IMU.getGyroODR();
       sigmaX2 +=x*x;  sigmaY2+=y*y;  sigmaZ2+=z*z;
       if (count==0) maxXYZ= abs(x);
       maxXYZ= max(maxXYZ,abs(x)); maxXYZ= max(maxXYZ,abs(y)); maxXYZ= max(maxXYZ,abs(z)); 
       count++;
       if ((count%30)==0)Serial.print('.'); 
       digitalWrite(LED_BUILTIN, (millis()/125)%2);       // blink onboard led every 250ms
   }
   digitalWrite(LED_BUILTIN,0);       // led off
   Serial.readStringUntil(13);        //Empty read buffer
   Serial.print(F("\n\n\nMeasured direction change X ")); 
   Serial.print(dirX,6);Serial.print("°\tY "); Serial.print(dirY,6);Serial.print("°\t Z "); Serial.println(dirZ,6);Serial.print("°");          
   sigmaX2 /= count;    sigmaY2 /= count;    sigmaZ2 /= count;
   Serial.print(F("Std.dev. "));  
   Serial.print(sigmaX2,6);Serial.print('\t'); Serial.print(sigmaY2,6);Serial.print('\t'); Serial.println(sigmaZ2,6);          
   Serial.print(F("percentage of Full Scale ")); Serial.print(100*maxXYZ/IMU.getGyroFS());Serial.println('%');          
   if (maxXYZ/IMU.getGyroFS()>0.95) Serial.print(F("Maximum rotation speed reached. Choose a different FS setting or turn more slowly."));
   else
   { dirX=abs(dirX); dirY=abs(dirY); dirZ=abs(dirZ);
     if (dirX>max(dirY,dirZ))
     { if (sigmaY2<gyroSlopeCriterion && sigmaZ2<gyroSlopeCriterion )
       {  validMmt= true;
          IMU.gyroSlope[0]=turnangle/dirX;
          gyroSlopeOK[0]=true;
          Serial.print ("Valid measurement, X detected, slope ");  Serial.println (IMU.gyroSlope[0]);
       }
     }
     if (dirY>max(dirX,dirZ))
     { if (sigmaX2<gyroSlopeCriterion && sigmaZ2<gyroSlopeCriterion )
       {  validMmt= true;
          IMU.gyroSlope[1]=turnangle/dirY;
          gyroSlopeOK[1]=true;
          Serial.print ("Valid measurement, Y detected, slope ");Serial.println (IMU.gyroSlope[1]);
       }
     }
     if (dirZ>max(dirY,dirX))
     { if (sigmaY2<gyroSlopeCriterion && sigmaX2<gyroSlopeCriterion )
       {  validMmt= true;
          IMU.gyroSlope[2]=turnangle/dirZ;
          gyroSlopeOK[2]=true;
          Serial.print ("Valid measurement, Z detected, slope ");Serial.println (IMU.gyroSlope[2]);
       }
     }
   }  
   if ( !validMmt ) 
   { Serial.println(F("\n\nNot a valid measurement!")); 
     delay(2000);
   }
   else Serial.println("\n\n");
}
 
void raw_N_Accel(uint16_t N, float& averX, float& averY, float& averZ) 
{    float x, y, z;
     averX=0; averY =0;averZ =0;
     for (int i=1;i<=N;i++)
     {  while (!IMU.accelAvailable());
        IMU.readRawAccel(x, y, z);
        averX += x;    averY += y;     averZ += z;
        digitalWrite(LED_BUILTIN, (millis()/125)%2);       // blink onboard led every 250ms
        if ((i%30)==0)Serial.print('.'); 
     } 
     averX /= N;    averY /= N;     averZ /= N;
     digitalWrite(LED_BUILTIN,0);                          // led off
}


void raw_N_Gyro(unsigned int N, float& averX, float& averY, float& averZ) 
{    float x, y, z;
     averX=0; averY =0;averZ =0;
     for (int i=1;i<=N;i++)
     {  while (!IMU.gyroAvailable());
        IMU.readRawGyro(x, y, z);
        averX += x;    averY += y;     averZ += z;
        digitalWrite(LED_BUILTIN, (millis()/125)%2);       // blink onboard led every 250ms
        if ((i%30)==0)Serial.print('.'); 
     } 
     averX /= N;    averY /= N;     averZ /= N;
     digitalWrite(LED_BUILTIN,0);                         // led off
}