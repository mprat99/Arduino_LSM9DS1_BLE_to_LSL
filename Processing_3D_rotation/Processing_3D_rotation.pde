import processing.serial.*;
import java.awt.event.KeyEvent;
import java.io.IOException;

Serial myPort;
boolean portFound = false;
String portName = "COM20"; // Replace with your port name
int baudrate = 9600;
String data="";


void setup() {
  size(600, 600, P3D);
  while (!portFound) {
    try {
      // Try to open the serial port
      myPort = new Serial(this, portName, baudrate);
      portFound = true;
      myPort.bufferUntil('\n');
      println("Serial port opened successfully.");
    } catch (Exception e) {
      // If the port is not available, print a message and wait before retrying
      println("Serial port not available. Waiting...");
      delay(5000); // Wait for 5 seconds before retrying
    }
  }
}

float theta, phi, psi;
float cosTheta;
float sinTheta;
float cosPhi;
float sinPhi;
float cosPsi;
float sinPsi;


void draw() {
  background(33);
  // Draw the static frame
  drawStaticFrame(); 
  
  // Apply transformations only to the rotating frame
  translate(width/2, height/2, 0);
  textSize(22);
  text("Theta: " + int(theta) + "     Phi: " + int(phi) + "     Psi: " + int(psi), -100, 265);
  
  pushMatrix(); // Save the current transformation state
    applyMatrix(
          cosPsi * cosPhi,                         (-sinPhi * cosTheta + cosPhi * sinPsi * sinTheta),          (sinPhi * sinTheta + cosPhi * sinPsi * cosTheta), 0.0,
          cosPsi * sinPhi,                          cosPhi * cosTheta + sinPsi * sinPhi * sinTheta,         (-cosPhi * sinTheta + sinPhi * sinPsi * cosTheta), 0.0,
                     -sinPsi,                                                      cosPsi * sinTheta,                                  cosPsi * cosTheta, 0.0,
        0.0, 0.0, 0.0, 1.0
      );
  drawRotatingFrame();
    // 3D 0bject
  textSize(30);  
  fill(0, 76, 153);
  box (386, 40, 200); // Draw box
  textSize(25);
  fill(255, 255, 255);
  text("MA1 Project", -183, 10, 101);
  
  
  popMatrix(); // Restore the previous transformation state
  
}

void drawRotatingFrame() {
  // Draw X-axis in red
  strokeWeight(2);
  stroke(255, 0, 0);
  line(0, 0, 0, 100, 0, 0);
  
  // Draw Y-axis in green (pointing inward)
  stroke(0, 255, 0);
  line(0, 0, 0, 0, -100, 0);
  
  // Draw Z-axis in blue (pointing upward)
  stroke(0, 0, 255);
  line(0, 0, 0, 0, 0, -100);
}

void drawStaticFrame() {
  // Draw a static frame in the corner
  // Draw X-axis in red
  strokeWeight(2);
  stroke(255, 0, 0);
  line(20, height - 20, 0, 120, height - 20, 0);
  text("x", 130, height - 15);
  
  // Draw Y-axis in green (pointing inward)
  stroke(0, 255, 0);
  line(20, height - 20, 0, 20, height - 120, 0);
  text("y", 100, height-55);
  
  // Draw Z-axis in blue (pointing upward)
  stroke(0, 0, 255);
  line(20, height - 20, 0, 20, height - 20, -100);
  text("z", 30, height-105);
}

// Read data from the Serial Port
void serialEvent (Serial myPort) { 
  // reads the data from the Serial Port up to the character '.' and puts it into the String variable "data".
  data = myPort.readStringUntil('\n');

  // if you got any bytes other than the linefeed:
  if (data != null) {
    data = trim(data);
    // split the string at "/"
    String items[] = split(data, ',');
    if (items.length > 1) {

      //--- Theta,Phi in degrees
      theta = -float(items[0]);
      phi = float(items[1]);
      psi =  -float(items[2]);
      //if (psi<0){
      //  psi+= 360;
      //}
      // Calculate trigonometric values
      cosTheta = cos(radians(theta));
      sinTheta = sin(radians(theta));
      cosPhi = cos(radians(phi));
      sinPhi = sin(radians(phi));
      cosPsi = cos(radians(psi));
      sinPsi = sin(radians(psi));
    }
  }
}
