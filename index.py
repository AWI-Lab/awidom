import argparse
import awidom


CONFIGFILE = 'config.yaml'


def startClient():
    sub = awidom.client.AWIClient(CONFIGFILE)
    sub.run()


def startServer():
    dom = awidom.server.AWIDom(CONFIGFILE)
    dom.run()
    sys.exit(dom.exec_())


if __name__ == "__main__":
    startServer()
