import concurrent.futures
import copy
from enum import Enum
from functools import partial
import os
from platform import system as system_name
import PySide.QtCore as QtCore
from PySide.QtCore import QDir
from PySide.QtCore import QPoint
from PySide.QtCore import QSize
import PySide.QtGui as QtGui
import random
import sys
import threading
import yaml

CLIENTFILE__ = 'clients.yaml'
OTREE_EXEC__ = 'chrome.exe'
ORG__ = 'Alfred-Weber-Institut für Wirtschaftwissenschaften'
NAME__ = 'AWIDominator'
PSEXEC__ = '.\psexec.exe'
BROADCAST_IP__ = '255.255.255.255'


def sendWarning(text):
    # TODO(d1): docstring
    warnBox = QtGui.QMessageBox()
    warnBox.setWindowTitle('Warnung!')
    warnBox.setText(text)
    warnBox.setStandardButtons(QtGui.QMessageBox.Ok)
    return warnBox.exec_() == QtGui.QMessageBox.Ok


def sendBooleanQuery(text):
    # TODO(d1): docstring
    questionBox = QtGui.QMessageBox()
    questionBox.setWindowTitle('Achtung!')
    questionBox.setText(text)
    questionBox.setStandardButtons(QtGui.QMessageBox.Yes)
    questionBox.addButton(QtGui.QMessageBox.No)
    questionBox.setDefaultButton(QtGui.QMessageBox.No)
    return questionBox.exec_() == QtGui.QMessageBox.Yes


class Ternary(Enum):
    # TODO(d1): docstring
    OFF = 0
    ON = 1
    UNKNOWN = 2


class AWIDom(QtGui.QApplication):
    """Handles the whole program."""

    def __init__(self, cfile=CLIENTFILE__):
        """
        Consturct a AWIDOM

        Args:
            cfile (string, optional): The path to the configuration file.
        """
        super().__init__(sys.argv)
        self.setOrganizationName(ORG__)
        self.setApplicationName(NAME__)
        self.left = PCList('Linke Seite')
        self.right = PCList('Rechte Seite')
        self.otree_uri = ''
        self.loadConfig(cfile)
        self.createWindow()

    def loadConfig(self, cfile):
        """Loads a configuration file and fills the memebers accordingly.

        Args:
            cfile (string): The path to the configuration file
        """
        with open(cfile, 'r') as f:
            try:
                clientsconf = yaml.load(f)
                self.loadPCs(self.left, clientsconf['left'])
                self.loadPCs(self.right, clientsconf['right'])
                self.otree_uri = clientsconf['otree-uri']
            except yaml.YAMLError as e:
                print(e)
                sendWarning('Configuration couldn\'t be loaded')
                sys.exit()

    def loadPCs(self, target, confs):
        """Goes throgh a list of PCs from a conf file and appends them to a
        PCList.

        Args:
            target (PCList): A PCList to append the new PCs to.
            confs (list): A list of PCs in dict form
        """
        return [target.append(PC(c['id'], c['name'], c['ip'], c['mac'])),
                for c in confs]

    def createWindow(self):
        """Creates the window for the application without showing/displaying it.
        """
        self.mainwindow = MainWindow()
        self.mainwindow.createLayout()
        self.mainwindow.pclistswidget.addList(self.left)
        self.mainwindow.pclistswidget.addList(self.right)

    def run(self):
        """Showing the constructed window to the user."""
        self.mainwindow.show()


class PC(QtGui.QCheckBox):
    """Handles one PC in the lab"""

    def __init__(self, id, name, ip, mac):
        """Initalizes the PC

        Args:
            id (int): The id for this PC
            name (str): A string as identifier
            ip (str): The IPv4-address
            mac (str): the MAC-address of this PC
        """
        super().__init__(name)
        self.id = id
        self.name = name
        self.ip = ip
        self.setMac(mac)
        self.online = Ternary(Ternary.UNKNOWN)
        self.isPinging = False
        self.loadIcons()

    def __lt__(self, other):
        """Less then comparison operator

        Args:
            other (PC): The other PC
        Returns:
            self.id < other.id
        """
        return self.id < other.id

    def __repr__(self):
        """Representation of a PC"""
        return repr((self.id, self.name, self.ip, self.mac))

    def __str__(self):
        """Nice formatted string output for a PC"""
        return ('PC: [id: {}, name: {}, ip: {}, mac: {}]'
                ''.format(self.id, self.name, self.ip, self.mac))

    def loadIcons(self):
        # TODO(d1): docstring
        pixmap_on = QtGui.QPixmap('./assets/font_awesome_toggle_on.png')
        pixmap_off = QtGui.QPixmap('./assets/font_awesome_toggle_off.png')
        pixmap_question = QtGui.QPixmap('./assets/font_awesome_question.png')
        self._icon_on = QtGui.QIcon(pixmap_on)
        self._icon_off = QtGui.QIcon(pixmap_off)
        self._icon_question = QtGui.QIcon(pixmap_question)

    def setMac(mac):
        if len(mac) == 12:
            pass
        elif len(mac) == 12 + 5:
            sep = mac[2]
            mac = mac.replace(sep, '')
        else:
            raise ValueError('Incorrect MAC address format')
        self.mac = mac

    def setOnline(self, status):
        # TODO(d1): docstring
        self.online = status
        self.setOnlineIcon()

    def setOnlineIcon(self):
        # TODO(d1): docstring
        if self.online == Ternary.ON:
            self.setIcon(self._icon_on)
        elif self.online == Ternary.OFF:
            self.setIcon(self._icon_off)
        else:
            self.setIcon(self._icon_question)
        self.setIconSize(QtCore.QSize(16, 16))

    def _ping(self):
        """Ping this PC"""
        self.isPinging = True
        self.setOnline(Ternary.UNKNOWN)
        ping_param = '-n 1' if system_name().lower() == 'windows' else '-c 1'
        isOnline = os.system('ping {} {}'.format(ping_param, self.ip)) == 0
        if isOnline:
            self.setOnline(Ternary.ON)
        else:
            self.setOnline(Ternary.OFF)
        self.isPinging = False
        return isOnline

    def ping(self):
        # TODO(d1): docstring
        if not self.isPinging:
            ping_thread = threading.Thread(target=self._ping)
            ping_thread.start()

    def _wake(host):
        # TODO(d1): docstring
        # Pad the synchronization stream.
        data = ''.join(['FFFFFFFFFFFF', self.mac * 20])
        send_data = b''

        # Split up the hex values and pack.
        for i in range(0, len(data), 2):
            send_data = b''.join([send_data,
                                  struct.pack('B', int(data[i: i + 2], 16))])

        # Broadcast it to the LAN.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(send_data, (BROADCAST_IP__, 7))
        return True

    def wake(self):
        # TODO(d1): docstring
        if not self.isChecked():
            return True
        if self.online != Ternary.ON:
            self._wake()
            self.setOnline(Ternary.UNKNOWN)
            # self.checked = False
        else:
            sendWarning('{} is already alive.'.format(self.name))

    def execCommand(self, command):
        # TODO(d1): docstring
        if not self.isChecked():
            return True
        if self.online == Ternary.ON:
            self.setChecked(False)
            print('Executing {} on {}'.format(command, self.name))
        else:
            sendWarning('{} is not alive.'.format(self.name))


class PCList(QtGui.QGroupBox):
    """A List of Buttons/Models of PCs, used to display as a list."""

    def __init__(self, title, pc_list=None):
        """Consturcts a new PCList.

        Args:
            title (str): The Title for the list, will be shown.
            pc_list (list, optional): The List of PCs added to the object.
        """
        super().__init__(title)
        self.layout = QtGui.QVBoxLayout()
        self.setSelectAllButton()
        if pc_list is not None:
            self.load(pc_list)

    def __iter__(self):
        return iter(self.children())

    def setSelectAllButton(self):
        self.selectall = QtGui.QPushButton('Select all')
        self.selectall.clicked.connect(self.selectAll)
        self.append(self.selectall)

    def load(self, pc_list):
        """Append all PCs in a list to this PCList.

        Args:
            pc_list (list): A list of PCs.
        """
        return [self.append(pc) for pc in pc_list]

    def append(self, item):
        """Append a single item to the List:

        Args:
            item (QWidget): The item.
        """
        self.layout.addWidget(item)
        if isinstance(item, PC):
            item.ping()
            self.layout.removeWidget(self.selectall)
            self.layout.addWidget(self.selectall)
        self.setLayout(self.layout)

    def selectAll(self):
        # TODO(d1): docstring
        return [i.setChecked() for i in self if isinstance(i, PC)]

    def wake(self):
        # TODO(d1): docstring
        return [i.wake() for i in self if isinstance(i, PC)]

    def execCommand(self, command):
        # TODO(d1): docstring
        return [i.execCommand(command) for i in self if isinstance(i, PC)]

    def ping(self):
        # TODO(d1): docstring
        return [i.ping() for i in self if isinstance(i, PC)]


class PCListsWidget(QtGui.QWidget):
    """A widget to display multiple PCLists side by side."""

    def __init__(self):
        """Construct a new PCListsWidget."""
        super().__init__()
        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)

    def __iter__(self):
        # TODO(d1): docstring
        return iter(self.children())

    def addList(self, pclist):
        """Add a new PCList to the widget.

        Args:
            pclist (PCList): The new list
        """
        self.layout.addWidget(pclist)
        self.setLayout(self.layout)


class MainWindow(QtGui.QMainWindow):
    # TODO(d1): docstring
    def __init__(self):
        """Construct a new MainWindow"""
        super().__init__()
        self.PCButtonGroup = QtGui.QButtonGroup()
        self.executeable = ('','')

    def createLayout(self):
        # TODO(d1): docstring
        self.cwidget = QtGui.QWidget()
        self.clayout = QtGui.QVBoxLayout()
        self.setCentralWidget(self.cwidget)
        self.pclistswidget = PCListsWidget()
        self.clayout.addWidget(self.pclistswidget)
        self.clayout.addWidget(self.createControls())
        self.cwidget.setLayout(self.clayout)

    def createControls(self):
        # TODO(d1): docstring
        controlwidget = QtGui.QWidget()
        controllayout = QtGui.QGridLayout()
        controllayout.addWidget(self.pingButton(), 0, 0)
        controllayout.addWidget(self.wakeButton(), 0, 1)
        controllayout.addWidget(self.oTreeButton(), 0, 2)
        controllayout.addWidget(self.selectButton(), 1, 0)
        controllayout.addWidget(self.execButton(), 1, 1)
        controlwidget.setLayout(controllayout)
        return controlwidget

    def _button(self, name, func):
        button = QtGui.QPushButton(name)
        button.clicked.connect(func)
        return button

    def pingButton(self):
        return self._button('Ping', self.ping)

    def execButton(self):
        # TODO(d1): docstring
        return self._button('Execute',
                            partial(self.execCommand,
                                    command=self.executeable))

    def selectButton(self):
        # TODO(d1): docstring
        return self._button('Select executeable', self.commandSelector)

    def wakeButton(self):
        # TODO(d1): docstring
        return self._button('Wake up', self.wake)

    def oTreeButton(self):
        # TODO(d1): docstring
        return self._button('oTree', self.startOTree)

    def ping(self):
        return [i.ping() for i in self.pclistswidget if isinstance(i, PCList)]

    def execCommand(self, command):
        # TODO(d1): docstring
        return [i.execCommand(command) for i in self.pclistswidget
                if isinstance(i, PCList)]

    def wake(self):
        # TODO(d1): docstring
        return [i.wake() for i in self.pclistswidget if isinstance(i, PCList)]

    def commandSelector(self):
        # TODO(d1): docstring
        self.executeable = QtGui.QFileDialog.getOpenFileName(self, 'Find the executeable', '/', '')

    def startOTree(self):
        # TODO(d1): docstring
        self.execCommand(OTREE_EXEC__)

    def about(self):
        # TODO(d1): docstring
        QtGui.QMessageBox.about(self, 'AWIDominator', 'HILFEEEE')


if __name__ == "__main__":
    awidom = AWIDom()
    awidom.run()
    sys.exit(awidom.exec_())
