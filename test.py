import RPi.GPIO as GPIO
import time

def test(pin):
    for i in range(100):
        print(GPIO.input(pin), end=" ")
        time.sleep(0.01)
    print("")

pin = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.IN)
test(pin)
