#include <AccelStepper.h>
#include <GFButton.h>
#include <LinkedList.h>
#include <Servo.h>

AccelStepper motorX(1, 2, 5);   // entrada X do shield
AccelStepper motorY1(1, 3, 6);  // entrada Y do shield
AccelStepper motorY2(1, 4, 7);  // entrada Z do shield

GFButton botaoX(22);
GFButton botaoY(24);

Servo servoGirador;
Servo servoGarfador;
Servo servoSubidor;

typedef struct {
    int x;
    int y;
    int angulo;
    String pincel; // OFF, SINGLE or THREE
} Punto;

LinkedList<Punto> positions; 

bool goingToPositions = false;
int posCurr = 0;

int xAntes = 0;
int yAntes = 0;
int posServo = 90;

void botaoXStop() {
  //Serial.print("Beleza X\n");
  motorX.stop();
  motorX.runToPosition();
  motorX.setCurrentPosition(0);
}

void botaoYStop() {
  //Serial.print("Beleza Y\n");
  motorY1.stop();
  motorY2.stop();
  motorY1.runToPosition();
  motorY2.runToPosition();
  motorY1.setCurrentPosition(0);
  motorY2.setCurrentPosition(0);
}

void movePincel(String pincel) {
  if (pincel == "OFF") {
    servoSubidor.write(105);
    //motorZ.setCurrentPosition(...);
    //motorZ.runToPosition();
  }
  else if (pincel == "SINGLE") {
    servoSubidor.write(60);
    servoGarfador.write(10); //confirmar angulo 
    //motorZ.setCurrentPosition(...);
    //motorZ.runToPosition();
  }
  else if (pincel == "THREE") {
    servoSubidor.write(60);
    servoGarfador.write(75);
    //motorZ.setCurrentPosition(...);
    //motorZ.runToPosition();
  }
  else {
    Serial.print("Pincel not valid!!!");
  }
}

void goToStartPosition() {
  motorX.moveTo(5000);
  motorY1.moveTo(-5000);
  motorY2.moveTo(-5000);
}

int calcAngle(int y, int x){
  int dy = y - yAntes;
  int dx = x - xAntes;
  int angulo = atan2(dy,dx) * 57.296; //angulo entre um ponto e outro, em coordenada polar
  yAntes = y;
  xAntes = x;

  if (angulo > 180){ // revisar
    angulo = 180;
  } else if (angulo < 0){
    angulo = 0;
  }

  return angulo;
}

//positionsStr format: 100,50,OFF 200,0,SINGLE 10,20,THREE ...
void savePositions(String positionsStr) {
  String coordCurr;
  int indSpace, x, y, indVirgola, indVirgola2;
  Punto coordCurrStruct;
  //Serial.print(String(test.indexOf(' ')) + '\n');
  while ((indSpace = positionsStr.indexOf(' ')) != -1) {
    coordCurr = positionsStr.substring(0, indSpace);
    //Serial.print(coordCurr + '\n');

    indVirgola = coordCurr.indexOf(',');
    indVirgola2 = coordCurr.lastIndexOf(',');
    coordCurrStruct.x = coordCurr.substring(0, indVirgola).toInt();
    coordCurrStruct.y = coordCurr.substring(indVirgola+1, indVirgola2).toInt();
    coordCurrStruct.pincel = coordCurr.substring(indVirgola2+1);
    //Serial.print(String(coordCurrStruct.x) + "  -  " + String(coordCurrStruct.y) + " " + coordCurrStruct.pincel +'\n');
    
    coordCurrStruct.angulo = calcAngle(coordCurrStruct.y, coordCurrStruct.x);

    positions.add(coordCurrStruct);

    positionsStr = positionsStr.substring(indSpace+1);
    //Serial.print(test + '\n');
  }

  indVirgola = positionsStr.indexOf(',');
  coordCurrStruct.x = positionsStr.substring(0, indVirgola).toInt();
  coordCurrStruct.y = positionsStr.substring(indVirgola+1).toInt();
  coordCurrStruct.pincel = positionsStr.substring(indVirgola2+1);
  coordCurrStruct.angulo = calcAngle(coordCurrStruct.y, coordCurrStruct.x);

  //Serial.print(String(x) + "  -  " + String(y) + '\n');
  positions.add(coordCurrStruct);

  /*for (int i=0; i<positions.size(); i++) {
    Punto coord = positions.get(i);
    Serial.print(String(coord.x) + ", " + String(coord.y) + '\n');
  }*/
}

void checkCurrentPosition() {
  Punto puntoCurr = positions.get(posCurr);

  if (posCurr == 0) {
    motorX.moveTo(puntoCurr.x);
    motorY1.moveTo(puntoCurr.y);
    motorY2.moveTo(puntoCurr.y);
    movePincel(puntoCurr.pincel);
    servoGirador.write(puntoCurr.angulo);
  }

  // current position reached, set next position
  if (motorX.distanceToGo() == 0 || motorY1.distanceToGo() == 0 || motorY2.distanceToGo() == 0) {
    Serial.print("Position " + String(posCurr) + " (" + String(positions.get(posCurr).x) + ", " + String(positions.get(posCurr).y) + ") reached\n");
    posCurr++;

    // last position reached, stop
    if (posCurr == positions.size()) {
      posCurr = 0;
      goingToPositions = false;
      servoSubidor.write(120); // confirmar angulo (sobe pá)
    } else {
      motorX.moveTo(puntoCurr.x);
      motorY1.moveTo(puntoCurr.y);
      motorY2.moveTo(puntoCurr.y);
      movePincel(puntoCurr.pincel);
      servoGirador.write(puntoCurr.angulo);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10); // espera máxima de 10ms na leitura

  motorX.setMaxSpeed(100);
  motorX.setAcceleration(1000);
  motorY1.setMaxSpeed(100);
  motorY1.setAcceleration(1000);
  motorY2.setMaxSpeed(100);
  motorY2.setAcceleration(1000);

  botaoX.setPressHandler(botaoXStop);
  botaoY.setPressHandler(botaoYStop);
  servoGirador.attach(30);
  servoGarfador.attach(28);
  servoSubidor.attach(26);

  movePincel("OFF");
}

void loop() {
  botaoX.process();
  botaoY.process();

  if (Serial.available() > 0) {
    String textInput = Serial.readStringUntil('\n');
    textInput.trim(); // remove quebra de linha
    Serial.print(textInput + '\n');

    String axis = textInput.substring(0,1);
    int position = textInput.substring(2).toInt();

    //Serial.print("Axis: " + axis + ", position: " + String(position) + '\n' );

    if (axis == "X") {
      movePincel("OFF");
      motorX.moveTo(position);
    }
    else if (axis == "Y") {
      movePincel("OFF");
      motorY1.moveTo(position);
      motorY2.moveTo(position);
    }
    else if (textInput == "home") {
      movePincel("OFF");
      goToStartPosition();
    }
    else if (textInput == "positions") {
      if (positions.size() > 0) {
        goingToPositions = true;
      }
    }
    else if (textInput == "clear") {
      positions.clear();
      Serial.print("Positions cleared");
    }
    else if (textInput == "OFF" || textInput == "SINGLE" || textInput == "THREE") {
      movePincel(textInput);
    }
    else {
      savePositions(textInput);
      Serial.print("Positions saved");
    }
  }

  if (goingToPositions) {
    checkCurrentPosition();
  }
  motorX.run();
  motorY1.run();
  motorY2.run();
}