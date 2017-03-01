from awidom import utils
from awidom.utils import CONFIG
import os
import sys
import yaml
import watchdog


class AWIClient(object):
    def __init__(self, configfile):
        self.loadConfig(configfile)

    def loadConfig(self, configfile):
        config = utils.loadYAML(configfile)
        self.BROADCAST_IP = config['broadcast_ip']
        self.NETWORK_DRIVE = config['root_path']
        self.OTREE_EXEC = config['otree_command']

    def reload(self):
        pass
