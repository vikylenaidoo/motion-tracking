/*send pulse train to motor
*period specified in microseconds between 700 and 
*
*
*/


#include <math.h>
#include <TimerOne.h>
unsigned int xcenter;
int dir;
float current_angle;
unsigned long period;
const int STEP_PIN = 10;
const int DIR_PIN = 11;
const int width = 320;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  
  period = 50000;
  dir = 1;
  xcenter = width/2;
  digitalWrite(DIR_PIN, dir);
  
  Timer1.initialize(period);
  Timer1.attachInterrupt(updateCurrentAngle);
  Timer1.pwm(STEP_PIN, 0.5*1023);
  
  Serial.print("Ready");
}

int readIntFromBytes() {
  union u_tag {
    byte b[4];
    int ival;
  } u;

  u.b[0] = Serial.read();
  u.b[1] = Serial.read();
  u.b[2] = Serial.read();
  u.b[3] = Serial.read();
  /*
  Serial.println(u.b[0]);
  Serial.println(u.b[0]);
  Serial.println(u.b[0]);
  Serial.println(u.b[0]);
  Serial.println("end of read");*/
  return u.ival;
}

void updateCurrentAngle(){
    if(dir==1){
      current_angle++;  
    }
    else{
      current_angle--; 
    }
}

void calibrateAngle(){
    
}

void loop() {
  while (1) {
    if(Serial.available() > 4){
      xcenter = readIntFromBytes();
      int deadcenter = width/2;
      if(xcenter>width | xcenter<0){ //out of bounds
        //Serial.print("xcenter out of bounds");
        //Serial.println(xcenter);
        //delay(10000);
       xcenter = deadcenter;  
      }

      //set direction
      if(xcenter>deadcenter){
        dir=0; 
      }
      else{
        dir=1;   
      }

      //set period
      if(xcenter==deadcenter){
        period=100000; 
      }
      else{
        period = 16000/abs(xcenter-deadcenter);  
      }
      if(period<3500){
        period = 3500;
      }
      
      /*Serial.print("xcenter: ");
      Serial.println(xcenter);
      Serial.print("period: ");
      Serial.println(period);
      Serial.println(dir);
      */
      Timer1.setPeriod(period);
      digitalWrite(DIR_PIN, dir);
      
      
    }
    else{
      /*if(period<100000){
        period = period+100;
      }*/
      //period = 64000;
      //Serial.print(xcenter);
      //Serial.println(" no comm");
     
    }
    
    //delay(5)
    Serial.println(current_angle);
    
  }
}
