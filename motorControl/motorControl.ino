/*send pulse train to motor
*period specified in microseconds between 700 and 
*
*
*/


#include <math.h>
#include <TimerOne.h>
unsigned int xcenter;
int dir;
short steps;
unsigned long period;
const int STEP_PIN = 10;
const int DIR_PIN = 11;
const int width = 320;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  
  period = 500000; //500000;
  dir = 1;
  xcenter = width/2;
  digitalWrite(DIR_PIN, dir);
  
  Timer1.initialize(period);
  //Timer1.attachInterrupt(updateCurrentAngle);
  Timer1.pwm(STEP_PIN, 0.5*1023);

  while(Serial.available()>0){ //to clear the buffer
    Serial.read();
  }
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
    if(dir==1){
      steps++;  
    }
    else{
      steps--; 
    }
}

void calibrateAngle(){
    
}

void loop() {
  while (1) {
    if(Serial.available() > 2){
      xcenter = readIntFromBytes();
      int deadcenter = width/2;

      //set direction
      if(xcenter>deadcenter){
        dir=0; 
      }
      else{
        dir=1;   
      }

      //set period
      if(xcenter==deadcenter){
        period=100000; //100000; 
      }
      else{
        period = 160000/abs(xcenter-deadcenter);  
      }
      if(period<20000){
        period = 20000;
      }
      
      Serial.print("xcenter: ");
      Serial.println(xcenter);
      Serial.print("period: ");
      Serial.println(period);
      Serial.println(dir);
      
      Timer1.setPeriod(period);
      digitalWrite(DIR_PIN, dir);
      //delay(100);
      
    }
    else{
      
      
      
    }
    /*Serial.write(highByte(steps));
    Serial.write(lowByte(steps));
    //delay(200);
    Serial.print("steps: ");
    Serial.println(steps);
    */
  }
}
