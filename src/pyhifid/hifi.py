#!/usr/bin/env python3

from threading import RLock


class HiFi:
    """
    Base class for HiFi units
    """

    def __init__(self):
        self.lock = RLock()

    def get_outputs(self):
        """
        Returns the supported outputs for this device
        """
        return []

    def set_output(self, output):
        """
        Switch to the specified output
        """
        pass

    def get_output(self):
        """
        Return the currently selected output
        """
        return None

    def set_volume(self, level):
        """
        Set the volume to the specified level
        level should be between 0 and 255
        """
        pass

    def get_volume(self):
        """
        Return the current volume level
        """
        return 0.0

    def adjust_volume(self, adjustment):
        """
        Adjust the volume level by adjustment
        """
        return 0.0

    def mute(self, muted):
        """
        Mute outputs
        """

    def muted(self):
        """
        Return whether muted or not
        """
        return False

    def toggle_mute(self):
        """
        Toggle mute
        """
        with self.lock:
            muted = self.muted()
            self.mute(not muted)

    def turn_on(self):
        """
        Turn on the device
        """

    def turn_off(self):
        """
        Turn off the device
        """

    def is_on(self):
        """
        Returns whether this is powered on or not
        """
        return False
