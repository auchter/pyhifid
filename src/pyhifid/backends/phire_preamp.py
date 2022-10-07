#!/usr/bin/env python3

import time

from pyhifid.hifi import HiFi
from pyhifid.backends.utils.gpio import Gpio
from brutefir import BruteFIR
from threading import Lock, Timer
import logging
import gpiod

_LOGGER = logging.getLogger(__name__)

class Relay:
    def __init__(self, set_gpio, rst_gpio):
        self.set_gpio = set_gpio
        self.rst_gpio = rst_gpio
        self.reset()

    def control(self, val):
        if val != 0:
            self.rst_gpio.set(False)
            self.set_gpio.set(True)
        else:
            self.set_gpio.set(False)
            self.rst_gpio.set(True)

    def reset(self):
        self.set_gpio.set(False)
        self.rst_gpio.set(False)


def get_linebulk(lines):
    for chip in gpiod.ChipIter():
        try:
            bulk = chip.find_lines(lines)
            _LOGGER.debug("found chip! " + str(bulk))
            return bulk
        except Exception as e:
            _LOGGER.debug(str(e))

    raise RuntimeError("couldn't find gpio chip for lines: " + str(lines))


def to_bitarray(x):
    return [1 if (x & (1 << i)) > 0 else 0 for i in range(8)]


class AmbDelta1:
    def __init__(self, pwr_gpio_name, prefix, relays=8):
        self.lock = Lock()
        self.pwr_gpio = Gpio(pwr_gpio_name, direction=Gpio.OUTPUT)

        self._volume = 0
        self._mute_volume = 0
        self._muted = False

        set_line_names = [f"{prefix}SET_{i}" for i in range(relays)]
        rst_line_names = [f"{prefix}RST_{i}" for i in range(relays)]

        self.set_lines = get_linebulk(set_line_names)
        self.rst_lines = get_linebulk(rst_line_names)

        self.set_lines.request(consumer="pyhifid", type=gpiod.LINE_REQ_DIR_OUT)
        self.rst_lines.request(consumer="pyhifid", type=gpiod.LINE_REQ_DIR_OUT) 

        self.set(0, force=True)

    def get(self):
        with self.lock:
            return self._volume

    def set(self, volume, force=False):
        _LOGGER.debug(f"{volume}, force: {force}")

        if volume > 255:
            raise RuntimeError("invalid volume level")

        with self.lock:
            mask = volume ^ self._volume

            if force:
                mask = 0xFF
                self._volume = 0xFF

            self.pwr_gpio.set(True)
            time.sleep(0.015)

            self.rst_lines.set_values(to_bitarray(self._volume & mask))
            time.sleep(0.003)
            self.set_lines.set_values(to_bitarray(volume & mask))
            time.sleep(0.015)

            self.rst_lines.set_values(to_bitarray(0))
            self.set_lines.set_values(to_bitarray(0))

            time.sleep(0.015)

            self.pwr_gpio.set(False)
            self._volume = volume


class AmbDelta2:
    def __init__(self, pwr_gpio_name, prefix, inputs=[], outputs=[]):
        self.lock = Lock()

        overlap = set(inputs) & set(outputs)
        if len(overlap) > 0:
            raise RuntimeError("inputs and outputs must be mutually exclusive")

        self.pwr_gpio = Gpio(pwr_gpio_name, direction=Gpio.OUTPUT)

        self.input = -1
        self.input_relays = []
        for i in inputs:
            set_gpio = Gpio(f"{prefix}SET_{i}", direction=Gpio.OUTPUT)
            rst_gpio = Gpio(f"{prefix}RST_{i}", direction=Gpio.OUTPUT)
            self.input_relays.append(Relay(set_gpio, rst_gpio))

        self.outputs = []
        self.output_relays = []
        for i in outputs:
            set_gpio = Gpio(f"{prefix}SET_{i}", direction=Gpio.OUTPUT)
            rst_gpio = Gpio(f"{prefix}RST_{i}", direction=Gpio.OUTPUT)
            self.output_relays.append(Relay(set_gpio, rst_gpio))

        self.select_outputs([])

    def select_input(self, index):
        if index < 0 or index > len(self.input_relays):
            raise RuntimeError("invalid input!")

        with self.lock:
            if index == self.input:
                return

            self.pwr_gpio.set(True)

            for relay in self.input_relays:
                relay.control(False)

            time.sleep(0.015)

            self.input_relays[index].control(True)

            time.sleep(0.015)

            for relay in self.input_relays:
                relay.reset()

            self.input = index

            self.pwr_gpio.set(False)

    def select_outputs(self, indices):
        if type(indices) is not list:
            indices = [indices]
        indices = sorted(indices)

        for index in indices:
            if index > len(self.output_relays):
                raise RuntimeError("invalid output!")

        with self.lock:
            if indices == self.outputs:
                return

            self.pwr_gpio.set(True)

            for relay in self.output_relays:
                relay.control(False)

            time.sleep(0.015)

            for index in indices:
                self.output_relays[index].control(True)

            time.sleep(0.015)

            self.outputs = indices

            self.pwr_gpio.set(False)

    def get_outputs(self):
        return self.outputs

    def get_input(self):
        return self.input


class LazyPower:
    """
    Class to provide lazy power control. turn_on will return
    the amount of time before the device is "on", and turn_off will
    power off the device after the grace period expires.
    """
    def __init__(self, gpio, turn_on_delay, turn_off_grace):
        self.gpio_name = gpio
        self.gpio = Gpio(gpio, direction=Gpio.OUTPUT)
        self.on_delay = turn_on_delay
        self.off_grace = turn_off_grace
        self.timer = None

        self.gpio.set(False)

    def turn_on(self):
        if self.timer is not None:
            _LOGGING.debug(f"LazyPower: {self.gpio} cancelling timer")
            self.timer.cancel()

        if not self.gpio.get():
            _LOGGING.info(f"LazyPower: {self.gpio} turning on")
            self.gpio.set(True)
            return self.on_delay

        return 0

    def turn_off(self):
        def deferred_off():
            _LOGGING.info(f"LazyPower: {self.gpio} turning off")
            self.gpio.set(False)
            self.timer = None

        if self.timer is None and self.gpio.get():
            _LOGGING.debug(f"LazyPower: {self.gpio} scheduling deferred off")
            self.timer = Timer(self.off_grace, deferred_off)
            self.timer.start()


class PhirePreamp(HiFi):
    # Delta2 outputs: 5 = headphones, 6 = stereo amp, 7 = subwoofer
    def __init__(self):
        super().__init__()
        self.delta1 = AmbDelta1("RELAY_PWR", "DELTA1_")
        self.delta2 = AmbDelta2(
            "RELAY_PWR", "DELTA2_", inputs=[0, 1, 2, 3, 4], outputs=[5, 6, 7]
        )
        self.brutefir = BruteFIR(host="127.0.0.1", port=6556)
        self.amp_power = LazyPower("TRIG_OUT_0", turn_on_delay=4.0, turn_off_grace=120.0)

        self._is_on = False
        self._output = None

        self._muted = False
        self._d2_outputs = []

        self.delta2_outputs = {
            "headphones": [2],
            "speakers": [0, 1],
            "no_sub": [0],
            "none": [],
        }

        self.output_coeffs = {
            "headphones": [
                "hd650",
                "dt770",
                "dirac",
            ],
            "speakers": [
                "speakers"
            ],
            "no_sub": [
                "no_sub",
                "dirac",
            ],
            "none": [
                "dirac",
            ]
        }

    def turn_on(self):
        with self.lock:
            self.set_output("none:dirac")
            self.set_volume(170)
            self._is_on = True

    def turn_off(self):
        with self.lock:
            self.set_output("none:dirac")
            self.set_volume(0)
            self._is_on = False

    def is_on(self):
        return self._is_on

    def get_outputs(self):
        ret = []
        for output, coeffs in self.output_coeffs.items():
            for coeff in coeffs:
                ret.append(f"{output}:{coeff}")
        return ret

    def set_output(self, output_coeffs):
        output, coeffs = output_coeffs.split(":")

        with self.lock:
            self.brutefir.change_filter_coeffs(coeffs)
            if output in ['speakers', 'no_sub']:
                self.amp_power.turn_on()
            else:
                self.amp_power.turn_off()
            self._set_outputs(output)

        self._output = output_coeffs

    def _set_outputs(self, outputs):
        with self.lock:
            outputs = self.delta2_outputs[outputs]
            if not self._muted:
                self.delta2.select_outputs(outputs)
            self._d2_outputs = outputs

    def get_output(self):
        return self._output

    def get_volume(self):
        return self.delta1.get()

    def set_volume(self, level):
        self.delta1.set(int(level))

    def adjust_volume(self, adjustment):
        with self.lock:
            cur = self.get_volume()
            cur += adjustment
            if cur > 255:
                cur = 255
            if cur < 0:
                cur = 0
            print(f"cur: {cur} adj: {adjustment}")
            self.set_volume(cur)

    def mute(self, muted):
        with self.lock:
            if muted:
                self._muted = True
                self.delta2.select_outputs([])
            else:
                self.delta2.select_outputs(self._d2_outputs)
                self._muted = False

    def muted(self):
        return self._muted
