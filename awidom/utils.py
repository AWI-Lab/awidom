from enum import Enum
import PySide.QtGui as QtGui
import sys
import yaml


class CONFIG(object):
    BROADCAST_IP = ''
    NETWORK_DRIVE = ''
    OTREE_EXEC = ''


class Ternary(Enum):
    OFF = 0
    ON = 1
    UNKNOWN = 2


def loadYAML(path):
    with open(path, 'r') as f:
        try:
            content = yaml.load(f)
        except yaml.YAMLError as e:
            sendWarning('File {} couldn\'t be loaded' % (path))
            sys.exit()
    return content


def sendWarning(text):
    warnBox = QtGui.QMessageBox()
    warnBox.setWindowTitle('Warnung!')
    warnBox.setText(text)
    warnBox.setStandardButtons(QtGui.QMessageBox.Ok)
    return warnBox.exec_() == QtGui.QMessageBox.Ok


def sendBooleanQuery(text):
    questionBox = QtGui.QMessageBox()
    questionBox.setWindowTitle('Achtung!')
    questionBox.setText(text)
    questionBox.setStandardButtons(QtGui.QMessageBox.Yes)
    questionBox.addButton(QtGui.QMessageBox.No)
    questionBox.setDefaultButton(QtGui.QMessageBox.No)
    return questionBox.exec_() == QtGui.QMessageBox.Yes
