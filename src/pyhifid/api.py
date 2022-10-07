#!/usr/bin/env python3

from flask import Flask
from flask_restful import reqparse, Api, Resource
from flask_restful import inputs
from gevent.pywsgi import WSGIServer
import sys

HIFI = None
REMOTE_INFO = None


class Power(Resource):
    def get(self):
        return {"power": HIFI.is_on()}

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("power", type=inputs.boolean)
        args = parser.parse_args()

        if args.power is None:
            return {"error": "invalid param"}, 400

        if args.power:
            HIFI.turn_on()
        else:
            HIFI.turn_off()

        return self.get()


class Mute(Resource):
    def get(self):
        return {"muted": HIFI.muted()}

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("muted", type=inputs.boolean)
        args = parser.parse_args()

        if args.muted is None:
            return {"error": "invalid param"}, 400
        HIFI.mute(args.muted)

        return self.get()


class Volume(Resource):
    def get(self):
        return {"volume": HIFI.get_volume()}

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("volume")
        parser.add_argument("adjust")
        args = parser.parse_args()

        if args.volume is None and args.adjust is None:
            return {"error": "invalid param"}, 400

        if args.volume is not None:
            HIFI.set_volume(float(args.volume))
        else:
            HIFI.adjust_volume(float(args.adjust))

        return self.get()


class Output(Resource):
    def get(self):
        return {
            "outputs": HIFI.get_outputs(),
            "output": HIFI.get_output(),
        }

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("output")
        args = parser.parse_args()

        if args.output is None:
            return {"error": "invalid param"}, 400

        HIFI.set_output(args.output)


class Remotes(Resource):
    def get(self):
        info = REMOTE_INFO.get_info()
        return { "remotes": info }


def serve_api(hifi, remote_info, debug=False):
    global HIFI
    HIFI = hifi

    global REMOTE_INFO
    REMOTE_INFO = remote_info

    app = Flask("pyhifid")
    api = Api(app)

    api.add_resource(Power, "/power")
    api.add_resource(Mute, "/mute")
    api.add_resource(Volume, "/volume")
    api.add_resource(Output, "/output")
    api.add_resource(Remotes, "/remotes")

    server = WSGIServer(("", 4664), app, log=sys.stderr if debug else None)
    server.serve_forever()
