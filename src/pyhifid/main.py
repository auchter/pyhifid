#!/usr/bin/env python3

import argparse
import logging
import sys

import pyhifid.backends
from pyhifid.powermate import create_powermate, RemoteInfo
from pyhifid.api import serve_api


def main():
    parser = argparse.ArgumentParser(description="pyhifid")
    parser.add_argument(
        "--backend", action="store", default="?", help="Backend to use; ? for list"
    )
    parser.add_argument(
        "--powermate_addr",
        action="append",
        default=[],
        metavar="ADDR",
        help="BT address of Griffin Powermate",
    )
    parser.add_argument(
        "--log", default="warning", action="store", help="change log level"
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper())

    if args.backend == "?":
        print("Valid backends:")
        for k, v in pyhifid.backends.BACKENDS.items():
            print("\t", k)
        return 1

    if args.backend not in pyhifid.backends.BACKENDS:
        raise RuntimeError("Unknown backend")

    # Almost certainly not the most pythonic way to do this,
    # but it's what  I came up with:
    name = pyhifid.backends.BACKENDS[args.backend]
    target = __import__(".".join(name.split(".")[:-1]))
    for component in name.split(".")[1:]:
        target = getattr(target, component)

    hifi = target()

    remote_info = RemoteInfo()
    powermates = []
    for addr in args.powermate_addr:
        powermates.append(create_powermate(addr, hifi, remote_info))

    serve_api(hifi, remote_info)


if __name__ == "__main__":
    sys.exit(main())
