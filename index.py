import argparse
import awidom.server
import sys


CONFIGFILE = 'config.yaml'


def startServer():
    dom = awidom.server.AWIDom(CONFIGFILE)
    dom.run()
    sys.exit(dom.exec_())


if __name__ == "__main__":
    startServer()
