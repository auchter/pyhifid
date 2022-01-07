#!/usr/bin/env python3

from pyhifid.hifi import HiFi
import requests
import sys


class Client(HiFi):
    def __init__(self, url):
        super().__init__()
        self.url = url + "/"

    def _get(self, endpoint):
        resp = requests.get(self.url + endpoint)
        resp.raise_for_status()
        return resp.json()

    def _put(self, endpoint, data):
        resp = requests.put(self.url + endpoint, data=data)
        resp.raise_for_status()
        return resp.json()

    def get_outputs(self):
        return self._get("output")["outputs"]

    def set_output(self, output):
        self._put("output", data={"output": output})

    def get_output(self):
        return self._get("output")["output"]

    def set_volume(self, level):
        self._put("volume", data={"volume": level})

    def adjust_volume(self, adjustment):
        self._put("volume", data={"adjust": adjustment})

    def get_volume(self):
        return self._get("volume")["volume"]

    def mute(self, muted):
        if muted:
            muted = True
        else:
            muted = False

        self._put("mute", data={"muted": muted})

    def muted(self):
        return self._get("mute")["muted"]

    def turn_on(self):
        self._put("power", data={"power": True})

    def turn_off(self):
        self._put("power", data={"power": False})

    def is_on(self):
        return self._get("power")["power"]

    def remote_info(self):
        return self._get("remotes")["remotes"]


def cli(hifi):
    def do_volume(args):
        if len(args) >= 2:
            hifi.set_volume(int(args[1]))
        elif len(args) == 1:
            print("volume: %f" % hifi.get_volume())
        else:
            print("usage: volume [vol]")

    def do_output(args):
        if len(args) >= 2:
            outputs = hifi.get_outputs()
            hifi.set_output(outputs[int(args[1])])
        elif len(args) == 1:
            print("outputs: %s" % str(hifi.get_outputs()))
            print("output: %s" % str(hifi.get_output()))
        else:
            print("usage: output [output]")

    def do_mute(args):
        if len(args) >= 2:
            if args[1] == "on":
                hifi.mute(True)
            elif args[1] == "off":
                hifi.mute(False)
            else:
                print("usage: mute [on/off]")
        elif len(args) == 1:
            print("mute: %s" % str(hifi.muted()))

    def do_power(args):
        if len(args) >= 2:
            if args[1] == "on":
                hifi.turn_on()
            elif args[1] == "off":
                hifi.turn_off()
            else:
                print("usage: power [on/off]")
        elif len(args) == 1:
            print("power: %s" % str(hifi.is_on()))
        else:
            print("usage: power [on/off]")

    def do_quit(args):
        sys.exit(0)

    def do_remotes(args):
        print(hifi.remote_info())

    cmds = {
        "vol": do_volume,
        "volume": do_volume,
        "mute": do_mute,
        "out": do_output,
        "output": do_output,
        "outputs": do_output,
        "power": do_power,
        "remotes": do_remotes,
        "quit": do_quit,
        "q": do_quit,
    }

    while True:
        val = input("> ")
        args = val.strip(" ").split(" ")
        if args[0] in cmds:
            try:
                cmds[args[0]](args)
            except Exception as e:
                print(e)
        else:
            print("Unknown command")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="pyhifid")
    parser.add_argument("url", help="pyhifid instance url")
    args = parser.parse_args()

    hifi = Client(args.url)
    cli(hifi)
