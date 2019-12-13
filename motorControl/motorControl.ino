/*send pulse train to motor
*period specified in microseconds between 700 and 
*
*
*/
//TODO: find c

#include <math.h>
//#include "TimerOne.h"

/*--------------------------------------- global variables --------------------------------*/
const int ZERO_PIN = 2;
const int STEP_PIN = 10;
const int DIR_PIN = 11;
const int TIMING_PIN = 9;
const int CALIBRATED_PIN = 3;


const int width = 320;

const float a = 0.26; //0.3
const float b = 0.005;
const float c = 0.1; //error gain
const float d = 0.05;

/*target = current_angle + c*x_error + d*(target_angle-prev_target_angle)/period
*/

volatile bool isCalibrated;
volatile bool isCalibrated_Jetson;
int state;
unsigned int xcenter;
int dir;
unsigned short steps;
float period;

float prev_x_error;
float prev_target_angle;
float target_angle;
unsigned long prev_target_time;

unsigned long t0;
volatile bool pinState;
volatile bool sendState;


// properties
//unsigned int pwmPeriod;
//unsigned char clockSelectBits;

/*--------------------------------------- setup -----------------------------------------*/
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ZERO_PIN, INPUT_PULLUP);
  pinMode(TIMING_PIN, OUTPUT);
  pinMode(CALIBRATED_PIN, OUTPUT);
  digitalWrite(CALIBRATED_PIN, 1);
  digitalWrite(STEP_PIN, 0);
  
  attachInterrupt(digitalPinToInterrupt(2), zeroButton, FALLING); //RISING, FALLING, LOW

  isCalibrated_Jetson = 0;
  isCalibrated = 0;
  digitalWrite(CALIBRATED_PIN, 0);
  calibrateAngle();
  
  period = 500; 
  target_angle = 45;
  xcenter = width/2;
  
  digitalWrite(DIR_PIN, dir);

  while(Serial.available()>0){ //to clear the input buffer
    Serial.read();
  }
  //Serial.flush();

  t0 = 0;
  Serial.print("Ready");
  /*
  Timer1.initialize(1000);//11111
  Timer1.attachInterrupt(sendSerial);
  //Timer1.start();
  */  
  
}


/*--------------------------- function definitions ---------------------------*/




/*----------------------AUX FNS ----------------------------*/
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
  isCalibrated = 0;
  digitalWrite(DIR_PIN, dir);
  while(!isCalibrated){
    state = !state;
    digitalWrite(STEP_PIN, state);
    delay(2);
  }
  steps = 0;
  delay(3000);
}

void zeroButton(){
  if(!isCalibrated){
    //steps = 0;
    isCalibrated = true;  
  }
  // digitalWrite(CALIBRATED_PIN, 0);
  //Timer1.start();
}

/*
void sendSerial(){
  now +=1; 
  //digitalWrite(3, pinState);
  //pinState = !pinState; 
  
}*/

/*-----------------------------------main loop ------------------------------------*/
void loop() {
  while (1) {
    float current_angle = 0.15*steps;
    
    if(Serial.available() > 2){ //use recieved xcenter to calculate target angle
      xcenter = readIntFromBytes();
      while(xcenter>width){
        Serial.read();
        xcenter = readIntFromBytes();
      }
      
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
      unsigned long now = millis();
      float target;
      if(x_error<25){
        target = current_angle + d*x_error;
      }
      else{
        target = current_angle + c*x_error;// - d*(x_error - prev_x_error)/(now - prev_target_time); //TODO: find value of c
        //target = target + 0.01*(target-prev_target_angle)/(now-prev_target_time);
      }
      if(target<180 && target>0){
        prev_x_error = x_error;
        prev_target_time = now;
        
        target_angle = target; 
        prev_target_angle = target_angle; 
        
      }
      Serial.print("serial recieved: \n xcenter = ");
      Serial.println(xcenter);
      //Serial.print("target = ");
      //Serial.println(target_angle);
      //Serial.print("current = ");
      //Serial.println(current_angle);
      //Serial.print("x error = ");
      //Serial.println(x_error);
      
      
    }
    
    
    //set period
    float error = abs(target_angle-current_angle);
    if(error<0.15){
      period = 50000; 
      if(target_angle==45 && isCalibrated_Jetson==0){
          isCalibrated_Jetson==1;
          digitalWrite(CALIBRATED_PIN, 0);
      } 
    }
    else{
      if(error>25){
        period = 20*error;//error*20-250;
      }
      else{
        if(error>15){
          period = 500;//250;    
        }
        else{
          period = 1000.0/(0.1333*error);//1000.0/(a*error);
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
   
    updateCurrentAngle();
    
    //unsigned long now = millis();
    
    //digitalWrite(TIMING_PIN, state);
    state = !state;
    }
    
    if(period<1000){
      delayMicroseconds(period);
    }
    else{
      delay(period/1000) ;
    }
  }
}
