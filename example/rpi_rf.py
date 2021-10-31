# Max cahnges
# send bitstring not int
# receive bitstring not int

import logging
import time
from collections import namedtuple

from RPi import GPIO

MAX_CHANGES = 67

_LOGGER = logging.getLogger(__name__)

Protocol = namedtuple('Protocol',
                      ['pulselength',
                       'sync_high', 'sync_low',
                       'zero_high', 'zero_low',
                       'one_high', 'one_low'])

PROTOCOL = Protocol(350, 1, 31, 1, 3, 3, 1)


class RFDevice:
    """Representation of a GPIO RF device."""

    # pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self, gpio, tx_repeat=10, tx_length=8, rx_tolerance=80):
        """Initialize the RF device."""
        self.gpio = gpio
        self.tx_enabled = False
        self.tx_pulselength = PROTOCOL.pulselength
        self.tx_repeat = tx_repeat
        self.tx_length = tx_length
        self.rx_enabled = False
        self.rx_tolerance = rx_tolerance
        # internal values
        self._rx_timings = [0] * (MAX_CHANGES + 1)
        self._rx_last_timestamp = 0
        self._rx_change_count = 0
        self._rx_repeat_count = 0
        # successful RX values
        self.rx_msg = None
        self.rx_timestamp = None
        self.rx_bitlength = None
        self.rx_pulselength = None

        GPIO.setmode(GPIO.BCM)
        _LOGGER.debug("Using GPIO " + str(gpio))

    def cleanup(self):
        """Disable TX and RX and clean up GPIO."""
        if self.tx_enabled:
            self.disable_tx()
        if self.rx_enabled:
            self.disable_rx()
        _LOGGER.debug("Cleanup")
        GPIO.cleanup()

    def enable_tx(self):
        """Enable TX, set up GPIO."""
        if self.rx_enabled:
            _LOGGER.error("RX is enabled, not enabling TX")
            return False
        if not self.tx_enabled:
            self.tx_enabled = True
            GPIO.setup(self.gpio, GPIO.OUT)
            _LOGGER.debug("TX enabled")
        return True

    def disable_tx(self):
        """Disable TX, reset GPIO."""
        if self.tx_enabled:
            # set up GPIO pin as input for safety
            GPIO.setup(self.gpio, GPIO.IN)
            self.tx_enabled = False
            _LOGGER.debug("TX disabled")
        return True

    def tx_bin(self, rawcode):
        """Send a binary code."""
        _LOGGER.debug("TX bin: " + str(rawcode))
        for _ in range(0, self.tx_repeat):
            for bit in range(0, self.tx_length):
                if rawcode[bit] == '0':
                    if not self.tx_l0():
                        return False
                else:
                    if not self.tx_l1():
                        return False
            if not self.tx_sync():
                return False

        return True

    def tx_l0(self):
        """Send a '0' bit."""
        return self.tx_waveform(PROTOCOL.zero_high,
                                PROTOCOL.zero_low)

    def tx_l1(self):
        """Send a '1' bit."""
        return self.tx_waveform(PROTOCOL.one_high,
                                PROTOCOL.one_low)

    def tx_sync(self):
        """Send a sync."""
        return self.tx_waveform(PROTOCOL.sync_high,
                                PROTOCOL.sync_low)

    def tx_waveform(self, highpulses, lowpulses):
        """Send basic waveform."""
        if not self.tx_enabled:
            _LOGGER.error("TX is not enabled, not sending data")
            return False
        GPIO.output(self.gpio, GPIO.HIGH)
        self._sleep((highpulses * self.tx_pulselength) / 1000000)
        GPIO.output(self.gpio, GPIO.LOW)
        self._sleep((lowpulses * self.tx_pulselength) / 1000000)
        return True

    def enable_rx(self):
        """Enable RX, set up GPIO and add event detection."""
        if self.tx_enabled:
            _LOGGER.error("TX is enabled, not enabling RX")
            return False
        if not self.rx_enabled:
            self.rx_enabled = True
            GPIO.setup(self.gpio, GPIO.IN)
            GPIO.add_event_detect(self.gpio, GPIO.BOTH)
            GPIO.add_event_callback(self.gpio, self.rx_callback)
            _LOGGER.debug("RX enabled")
        return True

    def disable_rx(self):
        """Disable RX, remove GPIO event detection."""
        if self.rx_enabled:
            GPIO.remove_event_detect(self.gpio)
            self.rx_enabled = False
            _LOGGER.debug("RX disabled")
        return True

    def rx_callback(self, gpio):
        """RX callback for GPIO event detection. Handle basic signal detection."""
        timestamp = int(time.perf_counter() * 1000000)
        duration = timestamp - self._rx_last_timestamp

        if duration > 5000:
            if abs(duration - self._rx_timings[0]) < 200:
                self._rx_repeat_count += 1
                self._rx_change_count -= 1
                if self._rx_repeat_count == 2:
                    if self._rx_waveform(self._rx_change_count, timestamp):
                        _LOGGER.debug("RX code " + str(self.rx_msg))
                    self._rx_repeat_count = 0
            self._rx_change_count = 0

        if self._rx_change_count >= MAX_CHANGES:
            self._rx_change_count = 0
            self._rx_repeat_count = 0
        self._rx_timings[self._rx_change_count] = duration
        self._rx_change_count += 1
        self._rx_last_timestamp = timestamp

    def _rx_waveform(self, change_count, timestamp):
        """Detect waveform and format code."""
        bits = ''
        delay = int(self._rx_timings[0] / PROTOCOL.sync_low)
        delay_tolerance = delay * self.rx_tolerance / 100

        for i in range(1, change_count, 2):
            if (abs(self._rx_timings[i] - delay * PROTOCOL.zero_high) < delay_tolerance and
                    abs(self._rx_timings[i+1] - delay * PROTOCOL.zero_low) < delay_tolerance):
                bits += '0'
            elif (abs(self._rx_timings[i] - delay * PROTOCOL.one_high) < delay_tolerance and
                  abs(self._rx_timings[i+1] - delay * PROTOCOL.one_low) < delay_tolerance):
                bits += '1'
            else:
                return False

        if self._rx_change_count > 6:
            self.rx_msg = bits
            self.rx_timestamp = timestamp
            self.rx_bitlength = int(change_count / 2)
            self.rx_pulselength = delay
            return True

        return False

    def _sleep(self, delay):
        _delay = delay / 100
        end = time.time() + delay - _delay
        while time.time() < end:
            time.sleep(_delay)