#include "pitches.h"

int buzzerPin = 3;

// define notes
int quadrantNotes[] = {
  NOTE_C4, NOTE_G4, NOTE_D4, NOTE_A4,  // quadrants 1-4
  NOTE_E4, NOTE_B4, NOTE_FS4, NOTE_CS4,  // quadrants 5-8
  NOTE_GS4, NOTE_DS4, NOTE_AS4, NOTE_F4   // quadrants 9-12
};

bool played[12] = {false, false, false, false,  // which quads have played their notes
                   false, false, false, false, 
                   false, false, false, false};

int lastQuadrant = -1;  // To store the last quadrant that played a note

unsigned long previousMillis = 0;  // last time a quad was triggered
const long resetInterval = 2000;   // time before allowing note to be played again

void setup() {
  Serial.begin(9600);  // start serial communication
  pinMode(buzzerPin, OUTPUT);  // set output pin
}

void playNote(int noteIndex) {
  // Play the note
  tone(buzzerPin, quadrantNotes[noteIndex]);
}

void stopNote() {
  noTone(buzzerPin);  
}

void loop() {
  if (Serial.available() > 0) {
    int quadrant = Serial.parseInt();  // read data

    // If quadrant is -1, stop all notes
    if (quadrant == -1) {
      stopNote();
      for (int i = 0; i < 12; i++) {
        played[i] = false;  // reset all played flags
      }
      lastQuadrant = -1;  // Reset last quadrant
    }
    // Ensure quad isn't out of range and play the note
    else if (quadrant >= 1 && quadrant <= 12) {
      unsigned long currentMillis = millis();

      // If we're leaving the previous quadrant and entering a new one
      if (quadrant != lastQuadrant) {
        // Stop current note if new note is received - override
        if (lastQuadrant != -1 && played[lastQuadrant - 1]) {
          stopNote();  // stop the previous note
          played[lastQuadrant - 1] = false;  // reset played flag for the previous quadrant
        }

        // Play the new note for the new quadrant
        playNote(quadrant - 1);
        played[quadrant - 1] = true;  // mark the new quadrant as played
        lastQuadrant = quadrant;  // update the last quadrant to the current one
      }
    }
    else {
      Serial.flush();  // clear serial buffer
    }
  }

  // If no quadrant is active, stop the note 
  bool anyNotePlaying = false;
  for (int i = 0; i < 12; i++) {
    if (played[i]) {
      anyNotePlaying = true;
      break;
    }
  }

  if (!anyNotePlaying) {
    stopNote();  // stop any note if no quadrant is active
  }
}
