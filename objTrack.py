import cv2
import numpy as np
import serial
import time

# get arduino
arduino = serial.Serial('COM5', 9600)
time.sleep(2)

# get camera
cap = cv2.VideoCapture(1)

# initialize window
cv2.namedWindow("Object Tracking", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Object Tracking", 1000, 1000)

last_quadrant = None  

quadrant_notes = {
    1: "C4", 2: "G4", 3: "D4", 4: "A4",  # Quadrants 1-4
    5: "E4", 6: "B4", 7: "F#4", 8: "C#4",  # Quadrants 5-8
    9: "G#4", 10: "D#4", 11: "A#4", 12: "F4"  # Quadrants 9-12
}

def get_quadrant(center_x, center_y, width, height):
    """determine which of the 12 boxes object is currently in"""
    
    box_width = width // 4
    box_height = height // 4

    box_positions = {
        1:  (3 * box_width, 0, width, box_height),      
        2:  (width - int(0.75 * (width - 3 * box_width)), box_height, width, 2 * box_height),
        3:  (width - int(0.75 * (width - 3 * box_width)), 2 * box_height, width, 3 * box_height),
        4:  (3 * box_width, 3 * box_height, width, height),  
        5:  (2 * box_width, height - int(0.75 * (height - 3 * box_height)), 3 * box_width, height),
        6:  (box_width, height - int(0.75 * (height - 3 * box_height)), 2 * box_width, height),
        7:  (0, 3 * box_height, box_width, height),        
        8:  (0, 2 * box_height, int(0.75 * box_width), 3 * box_height),
        9:  (0, box_height, int(0.75 * box_width), 2 * box_height),
        10: (0, 0, box_width, box_height),                
        11: (box_width, 0, 2 * box_width, int(0.75 * box_height)),
        12: (2 * box_width, 0, 3 * box_width, int(0.75 * box_height))
    }

    for quadrant, (x1, y1, x2, y2) in box_positions.items():
        if x1 <= center_x < x2 and y1 <= center_y < y2:
            return quadrant

    return -1  # middle quadrant


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape
    box_width = width // 4
    box_height = height // 4

    # draw boxes around edge
    box_positions = {
        1: (3 * box_width, 0, width, box_height),
        2: (width - int(0.75 * (width - 3 * box_width)), box_height, width, 2 * box_height),
        3: (width - int(0.75 * (width - 3 * box_width)), 2 * box_height, width, 3 * box_height),
        4: (3 * box_width, 3 * box_height, width, height),
        5: (2 * box_width, height - int(0.75 * (height - 3 * box_height)), 3 * box_width, height),
        6: (box_width, height - int(0.75 * (height - 3 * box_height)), 2 * box_width, height),
        7: (0, 3 * box_height, box_width, height),
        8: (0, 2 * box_height, int(0.75 * box_width), 3 * box_height),
        9: (0, box_height, int(0.75 * box_width), 2 * box_height),
        10: (0, 0, box_width, box_height),
        11: (box_width, 0, 2 * box_width, int(0.75 * box_height)),
        12: (2 * box_width, 0, 3 * box_width, int(0.75 * box_height))
    }

    for quadrant, (x1, y1, x2, y2) in box_positions.items():
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"Q{quadrant} - {quadrant_notes[quadrant]}", (x1 + 10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # pink color range
    lower_pink = np.array([168, 100, 110])
    upper_pink = np.array([174, 255, 220])
    
    mask = cv2.inRange(hsv, lower_pink, upper_pink)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest_contour = None
    max_area = 175  # minimium detection size

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            largest_contour = contour

    if largest_contour is not None:
        x, y, w, h = cv2.boundingRect(largest_contour)
        object_center_x, object_center_y = x + w // 2, y + h // 2
        quadrant = get_quadrant(object_center_x, object_center_y, width, height)

        # print quad when object enters new quad
        if quadrant != last_quadrant:
            print(f"Object entered quadrant {quadrant}")
            # send data to arduino
            arduino.write(f"{quadrant}\n".encode())
            last_quadrant = quadrant

        # draw one rectangle
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.circle(frame, (object_center_x, object_center_y), 5, (0, 0, 255), -1)
        text = f"({object_center_x}, {object_center_y}) - Q{quadrant}"
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Object Tracking", frame)

    # close frame when q is hit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()