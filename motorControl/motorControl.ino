// Send PWM mirco-seconds out of pinD9
#include <math.h>
int xcenter;
int dir;
float period;
int state;
const int STEP_PIN = 12;
const int DIR_PIN = 11;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  period = 1;
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
        period = 500.0/fabs(xcenter-640);  
      }
      
    }

    digitalWrite(DIR_PIN, dir);
    digitalWrite(STEP_PIN, state);
    delay(period);
    state = !state;
    Serial.print(xcenter+" ");
    Serial.println((state));
  }
}
