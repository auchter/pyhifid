import logging
from pyhifid.hifi import HiFi

class MockHiFi(HiFi):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Created a MockHiFi instance")

        self._output = None
        self._volume = 0
        self._muted = False
        self._power = False

    def get_outputs(self):
        return ["speakers", "headphones"]

    def set_output(self, output):
        assert output in self.get_outputs()
        self.logger.info(f"Set output to {output}")
        self._output = output

    def get_output(self):
        return self._output

    def set_volume(self, level):
        assert level <= 255.0
        assert level >= 0.0
        self.logger.info(f"Set volume to {level}")
        self._volume = level

    def get_volume(self):
        return self._volume

    def adjust_volume(self, adjustment):
        new_level = self._volume + adjustment
        if new_level > 255:
            new_level = 255
        if new_level < 0:
            new_level = 0

        self.set_volume(new_level)

    def mute(self, muted):
        self.logger.info(f"Set mute to {muted}")
        self._muted = muted

    def muted(self):
        return self._muted

    def turn_on(self):
        self.logger.info(f"Turn power on")
        self._power = True

    def turn_off(self):
        self.logger.info(f"Turn power off")
        self._power = False

    def is_on(self):
        return self._power

    def brutefir_graph(self):
        return ""
