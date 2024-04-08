from sense_hat import SenseHat
import time

sense = SenseHat()

y = (255, 255, 0) # Yellow
b = (0, 0, 0) # Black
o = (0, 0, 0) # Off/black

# Define the image as an 8x8 grid (smiley face)
smiley_image = [
o, o, y, y, y, y, o, o,
o, y, y, y, y, y, y, o,
y, y, b, y, y, b, y, y,
y, y, y, y, y, y, y, y,
y, y, b, b, b, b, y, y,
y, y, y, b, b, y, y, y,
o, y, y, y, y, y, y, o,
o, o, y, y, y, y, o, o
]

black = [
    
]

try:
    while True:
        for event in sense.stick.get_events():
            # Check if the joystick was pressed
            if event.action == "pressed":
                # Print the direction of the press
                print("Joystick was {} {}".format(event.direction, event.action))
            if event.direction == "up":
                sense.set_pixels(smiley_image)
            
        # Wait a short time
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Program exited cleanly")
