#!/usr/bin/env python3

import datetime
import logging
import time
from threading import Lock, Thread
from powermate import Powermate, PowermateDelegate


class PowermatePreamp(PowermateDelegate):
    def __init__(self, hifi):
        self.hifi = hifi
        self.logger = logging.getLogger(__name__)
        self.lock = Lock()
        self.last = datetime.datetime.now()
        self.adjust = 0

        def adjust_thread():
            while True:
                with self.lock:
                    if self.adjust != 0:
                        self.hifi.adjust_volume(self.adjust)
                        self.adjust = 0
                time.sleep(0.05)

        self.thread = Thread(target=adjust_thread)
        self.thread.start()

    def on_connect(self):
        self.logger.debug("powermate connected")

    def on_disconnect(self):
        self.logger.debug("powermate disconnnected")

    def on_battery_report(self, val):
        self.logger.debug(f"powermate battery: {val}%")

    def on_press(self):
        self.logger.debug("powermate button pressed")
        self.hifi.toggle_mute()

    def on_long_press(self, t):
        self.logger.debug(f"powermate button long pressed for {t} seconds")
        with self.lock:
            if self.hifi.is_on():
                self.hifi.turn_off()
            else:
                self.hifi.turn_on()

    def on_clockwise(self):
        self.logger.debug("powermate clockwise")
        with self.lock:
            self.adjust += 1

    def on_counterclockwise(self):
        self.logger.debug("powermate counterclockwise")
        with self.lock:
            self.adjust += -1

    def _adjust_output(self, direction):
        with self.lock:
            outputs = self.hifi.get_outputs()
            output = self.hifi.get_output()
            if output not in outputs:
                self.logger.error(f"{output} not in {outputs}")
                return
            idx = (outputs.index(output) + direction) % len(outputs)
            self.hifi.set_output(outputs[idx])

    def on_press_clockwise(self):
        self.logger.debug("powermate press clockwise")
        self._adjust_output(1)

    def on_press_counterclockwise(self):
        self.logger.debug("powermate press counterclockwise")
        self._adjust_output(-1)


def create_powermate(addr, hifi):
    return Powermate(addr, PowermatePreamp(hifi))
