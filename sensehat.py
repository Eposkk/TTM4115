from sense_hat import SenseHat
import time

sense = SenseHat()

# Define the colors
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


# Display the image
sense.set_pixels(smiley_image)

# Keep the image displayed for a certain time, then clear it.
# For example, 5 seconds
time.sleep(5)
sense.clear()
