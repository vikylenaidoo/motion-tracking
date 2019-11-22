/*send pulse train to motor
*period specified in microseconds between 700 and 
*
*
*/


#include <math.h>
#include <TimerOne.h>
unsigned int xcenter;
int dir;
unsigned int period;
//int state;
const int STEP_PIN = 10;
const int DIR_PIN = 11;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  period = 500000;
  //state = 1;
  dir = 0;
  xcenter = 640;
  digitalWrite(DIR_PIN, dir);
  Timer1.initialize(period);
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
 
  return u.ival;
}

void loop() {
  while (1) {
    if(Serial.available() > 1){
      xcenter = readIntFromBytes();
      if(xcenter>1280 | xcenter<0){
        //Serial.print("xcenter out of bounds");
        //Serial.println(xcenter);
        //delay(10000);
       xcenter = 200;  
      }
      else{
        if(xcenter>640){
          dir=0; 
        }
        else{
          dir=1;   
        }
        if(xcenter==640){
          period=10000; 
        }
        else{
          period = 640000/abs(xcenter-640);  
        }
      }
    }
    else{
      period = period;  
    }

    if(period<3800){
      period = 3800;
    }
    delay(100);
    Timer1.setPeriod(period);
    digitalWrite(DIR_PIN, dir); 
    Serial.print("xcenter: ");
    Serial.println(xcenter);
    Serial.print("period: ");
    Serial.println(period);
    Serial.println(dir);
    
  }
}
