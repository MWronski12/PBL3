import RPi.GPIO as GPIO
import time
import logging

# Logging config
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(name)s %(asctime)s: \n%(message)s\n")

file_handler = logging.FileHandler("sample.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# States of transmission
IDLE = 0
SYNC = 1
TRANSMISSION = 2

# Global vars
timeout = 0
timestamp = 0
state = IDLE

rx_tick = 350 / 1000000
tx_tick = 350 / 1000000

msg_len = 8
bits_left = 8
buff = ""

tol = rx_tick * 0.8
tx_pin = 17
rx_pin = 27


def rx_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(rx_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(rx_pin, GPIO.RISING)
    GPIO.add_event_callback(rx_pin, rx_interrupt_handler)
    logger.debug("Listening to messages\nrx_pin set to: {}".format(rx_pin))


def rx_got_msg_callback():
    global buff
    logger.debug("Message received: %s", buff)
    buff = ""


def rx_interrupt_handler(gpio):
    global state, timeout, timestamp, rx_tick, buff, bits_left
    if state == IDLE:
        timestamp = time.time()
        timeout = timestamp + 32 * rx_tick
        state = SYNC
#        logger.debug("Interrupt detected during idle phase\nSync phase initialized\ntimeout set to: {}".format(timeout))

    elif state == SYNC:
        if time.time() < timeout - tol:
#            logger.debug("Next interrupt detected too early, probably noise")
            return
        if time.time() > timeout + tol:
            state = IDLE
#            logger.debug("Sync phase timeout; returning to idle...")
            return
        rx_tick = (time.time() - timestamp) / 32
        timeout = time.time() + 4 * rx_tick
        state = TRANSMISSION
        rx_receive()
#        logger.debug("Interrupt detected during Sync phase\nrx_tick set to: {}\ntimeout set to: {}\nTransmission phase initialized".format(rx_tick, timeout))

    elif state == TRANSMISSION:
        if time.time() < timeout - tol:
#            logger.debug("Interrupt detected too early, probably noise")
            return
        if time.time() > timeout + tol:
            buff = ""
            bits_left = 8
            state = IDLE
#            logger.debug("Timeout during Transmission phase\nReturning to idle")
            return
        timeout = time.time() + 4 * rx_tick
        rx_receive()
#        logger.debug("Interrupt detected during transmission phase\ntimeout set to: {}".format(timeout))


def rx_receive():
    global state, bits_left, buff
    if bits_left == 0:
        rx_got_msg_callback()
        bits_left = 8
        state = IDLE
        return
    time.sleep(2 * rx_tick)
    buff += str(GPIO.input(rx_pin))
    bits_left -= 1

def tx_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(tx_pin, GPIO.OUT)
    logger.debug("tx_pin set to: {}".format(tx_pin))


def tx_0():
    GPIO.output(tx_pin, GPIO.HIGH)
    time.sleep(tx_tick)
    GPIO.output(tx_pin, GPIO.LOW)
    time.sleep(3 * tx_tick)


def tx_1():
    GPIO.output(tx_pin, GPIO.HIGH)
    time.sleep(3 * tx_tick)
    GPIO.output(tx_pin, GPIO.LOW)
    time.sleep(tx_tick)


def tx_sync():
    GPIO.output(tx_pin, GPIO.HIGH)
    time.sleep(tx_tick)
    GPIO.output(tx_pin, GPIO.LOW)
    time.sleep(31 * tx_tick)


def tx_send_msg(msg):
    # msg is a string of bits
    if len(msg) != msg_len:
        logger.debug("Incorrect message format; transmission failed")
        return
    tx_sync()
    for i in range(len(msg)):
        if msg[i] == "0":
            tx_0()
        elif msg[i] == "1":
            tx_1
        else:
            logger.debug("Incorrect message format; transmission failed")
            return
