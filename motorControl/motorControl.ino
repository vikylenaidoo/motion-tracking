/*send pulse train to motor
*period specified in microseconds between 700 and 
*
*
*/
//TODO: fix code for target_angle, find c

#include <math.h>

const int ZERO_PIN = 2;
const int STEP_PIN = 10;
const int DIR_PIN = 11;
const int width = 320;

const float a = 0.03; //0.03
const float b = 0.005;
const float c = 0.2; //0.2

volatile bool isCalibrated;
int state;
unsigned int xcenter;
int dir;
short steps;
float period;
float target_angle;
unsigned long t0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ZERO_PIN, INPUT_PULLUP);
  
  attachInterrupt(digitalPinToInterrupt(2), zeroButton, FALLING); //RISING, FALLING, LOW
  
  isCalibrated = 0;
  calibrateAngle();
  
  period = 500; //fast ~ 2 to 3
  target_angle = 90;
  xcenter = width/2;
  
  digitalWrite(DIR_PIN, dir);

  while(Serial.available()>0){ //to clear the buffer
    Serial.read();
  }

  t0 = millis();
  Serial.print("Ready");
}

int readIntFromBytes() {
  union u_tag {
    byte b[2];
    int ival;
  } u;

  for(int i=0; i<2; i++){
    u.b[i] = Serial.read();
  }

  return u.ival;
}

void updateCurrentAngle(){ //used as a handler on rising edge of timer to update the steps
    if(state){
      if(dir==1){
        steps--;  
      }
      else{
        steps++; 
      }
    }
}

void calibrateAngle(){
  dir = 1;
  digitalWrite(DIR_PIN, dir);
  while(!isCalibrated){
    state = !state;
    digitalWrite(STEP_PIN, state);
    delay(2);
  }
  steps = 0;
}

void zeroButton(){
  if(!isCalibrated){
    //steps = 0;
    isCalibrated = true;  
  }
}

void loop() {
  while (1) {
    float current_angle = 0.15*steps;
    
    if(Serial.available() > 2){ //use recieved xcenter to calculate target angle
      xcenter = readIntFromBytes();
      int deadcenter = width/2;
      int x_error = (xcenter-deadcenter);
      
      //set direction
      if(xcenter>deadcenter){
        dir=0; 
      }
      else{
        dir=1;   
      }

      //set target_angle
      float target = current_angle + c*x_error; //TODO: find value of c
      if(target<180 && target>0){
        target_angle = target;  
      }
      /*Serial.print("serial recieved: \n xcenter = ");
      Serial.println(xcenter);
      Serial.print("target = ");
      Serial.println(target_angle);
      Serial.print("current = ");
      Serial.println(current_angle);
      Serial.print("x error = ");
      Serial.println(x_error);
      */
      
    }
    
    
    
    float error = abs(target_angle-current_angle);
    if(error<0.15){
      period = 50;  
    }
    else{
      if(error>20){
        period = 1;    
      }
      else{
        period = 1.0/(a*error);
      }
    }
    
    if(current_angle>target_angle){
      dir = 1;  
    }
    else{
      dir = 0;  
    }
    
    digitalWrite(STEP_PIN, state);
    digitalWrite(DIR_PIN, dir);
    state = !state;
    updateCurrentAngle();
    delay(period);

    unsigned long now = millis();

    if(Serial.availableForWrite()>2 && (now-t0)>11.1){ //wait until 90Hz (11.1ms) to send
      Serial.write(highByte(steps));
      Serial.write(lowByte(steps));
      t0 = now;
    }

    /*Serial.print("error: ");
    Serial.println(error);
    Serial.print("period: ");
    Serial.println(period);
    */
    
  }
}
