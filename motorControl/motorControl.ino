// Send PWM mirco-seconds out of pinD9
#include <math.h>
int xcenter;
int dir;
float period;
int state;
int STEP_PIN;
int DIR_PIN;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  period = 10;
  state = 1;
  dir = 0;
  Serial.print("Ready");
}

int readIntFromBytes() {
  union u_tag {
    byte b[2];
    int ival;
  } u;

  u.b[0] = Serial.read();
  u.b[1] = Serial.read();
  return u.ival;
}

void loop() {
  while (1) {
    if(Serial.available() > 2){
      xcenter = readIntFromBytes();

      if(xcenter>640){
        dir=0;  
      }
      else{
        dir=1;  
      }
      if(xcenter==640){
        period=1; 
      }
      else{
        period = 10/fabs(xcenter-640);  
      }
      
    }

    digitalWrite(DIR_PIN, dir);
    digitalWrite(STEP_PIN, state);
    delay(period);
    Serial.write((int)round(period));
  }
}
