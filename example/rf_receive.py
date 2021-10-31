#!/usr/bin/env python3

import argparse
import signal
import sys
import time
import logging

from rpi_rf import RFDevice


def exithandler(signal, frame):
    rfdevice.cleanup()
    sys.exit(0)


logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s', )

parser = argparse.ArgumentParser(
    description='Receives a decimal code via a 433/315MHz GPIO device')
parser.add_argument('-g', dest='gpio', type=int, default=27,
                    help="GPIO pin (Default: 27)")
parser.add_argument('-l', dest='length', type=int, default=27,
                    help="length of msg (Default: 8)")
args = parser.parse_args()

signal.signal(signal.SIGINT, exithandler)

rfdevice = RFDevice(args.gpio, tx_length=args.length)
rfdevice.enable_rx()
timestamp = None
logging.info("Listening for messagess on GPIO " + str(args.gpio))

while True:
    if rfdevice.rx_msg_timestamp != timestamp:
        timestamp = rfdevice.rx_msg_timestamp
        logging.info("Message received: " + str(rfdevice.rx_code))
    time.sleep(0.01)
