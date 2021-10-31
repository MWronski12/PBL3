#!/usr/bin/env python3

import argparse
import logging

from rpi_rf import RFDevice

logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s',)

parser = argparse.ArgumentParser(
    description='Sends a decimal code via a 433/315MHz GPIO device')
parser.add_argument('msg', metavar='MSG', type=str,
                    help="Binary string to send")
parser.add_argument('-g', dest='gpio', type=int, default=17,
                    help="GPIO pin (Default: 17)")
parser.add_argument('-l', dest='length', type=int, default=8,
                    help="Message length (Default: 8)")
parser.add_argument('-r', dest='repeat', type=int, default=10,
                    help="Repeat cycles (Default: 10)")
args = parser.parse_args()

rfdevice = RFDevice(args.gpio)
rfdevice.enable_tx()
rfdevice.tx_length = args.length
rfdevice.tx_repeat = args.repeat

logging.info("[ message:" + str(args.msg) +
             ", length: " + str(rfdevice.tx_length) +
             ", repeat: " + str(rfdevice.tx_repeat) + "]")

rfdevice.tx_bin(args.code, args.length)
rfdevice.cleanup()
