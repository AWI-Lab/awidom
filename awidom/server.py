from awidom import utils
from awidom.utils import CONFIG
from awidom.utils import Ternary
import os
from platform import system as system_name
import PySide.QtCore as QtCore
from PySide.QtCore import QDir
from PySide.QtCore import QPoint
from PySide.QtCore import QSize
import PySide.QtGui as QtGui
import random
import struct
import socket
import sys
import threading


# Runtime globals
class ICONS(object):
    ON = 0
    OFF = 0
    UNKOWN = 0


class AWIDom(QtGui.QApplication):
    """Handles the whole program."""

    def __init__(self, configfile):
        """
        Consturct a AWIDOM

        Args:
            configfile (string, optional): The path to the configuration file.
        """
        super().__init__(sys.argv)
        self.loadConfig(configfile)
        self.settings = QtCore.QSettings()
        self.executions = {}
        self.loadIcons()
        self.createWindow()

    def loadConfig(self, configfile):
        config = utils.loadYAML(configfile)
        self.setApplicationName(config['app_name'])
        self.setOrganizationName(config['organisation'])
        self.loadPCs(config['client_file'])
        CONFIG.BROADCAST_IP = config['broadcast_ip']
        CONFIG.NETWORK_DRIVE = config['root_path']
        CONFIG.OTREE_EXEC = config['otree_command']
        CONFIG.OTREE_URI = config['otree_uri']

    def loadPCs(self, clientfile):
        clientsconf = utils.loadYAML(clientfile)
        self.left = PCList('Left side', self.execute)
        self.right = PCList('Right side', self.execute)
        [self.left.append(PC(c['id'], c['name'], c['ip'], c['mac'],
                             self.execute)) for c in clientsconf['left']]
        [self.right.append(PC(c['id'], c['name'], c['ip'], c['mac'],
                             self.execute)) for c in clientsconf['right']]

    def loadIcons(self):
        pixmap_on = QtGui.QPixmap('./assets/font_awesome_toggle_on.png')
        pixmap_off = QtGui.QPixmap('./assets/font_awesome_toggle_off.png')
        pixmap_question = QtGui.QPixmap('./assets/font_awesome_question.png')
        ICONS.ON = QtGui.QIcon(pixmap_on)
        ICONS.OFF = QtGui.QIcon(pixmap_off)
        ICONS.QUESTION = QtGui.QIcon(pixmap_question)

    def createWindow(self):
        """Creates the window for the application without showing/displaying it.
        """
        self.mainwindow = MainWindow()
        self.mainwindow.createLayout()
        self.mainwindow.pclistswidget.addList(self.left)
        self.mainwindow.pclistswidget.addList(self.right)

    def execute(clients, commands, wait=False):
        '''Adds a command to the execution waiting list.

        Args:
            clients (list(str)): The list of clients to add the command for.
            commands (str, list): The command or list of commands to add
            wait (bool, optional): Whether to wait with execution until further
                notice.
        '''
        if not isinstance(commands, list):
            commands = list(commands)
        for client in clients:
            if client in self.executions:
                self.executions[client].extend(commands)
            else:
                self.executions[client] = commands
        if not wait:
            self.flushExecutions()

    def flushExecutions():
        '''Will save all pending executions to the file so they can be run.'''
        pass

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
        super().__init__('{}: {}'.format(id, name))
        self.id = id
        self.name = name
        self.ip = ip
        self.setMac(mac)
        self.setOnline(Ternary.UNKNOWN)
        self.isPinging = False

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

    def setMac(self, mac):
        if len(mac) == 12:
            pass
        elif len(mac) == 12 + 5:
            sep = mac[2]
            mac = mac.replace(sep, '')
        else:
            raise ValueError('Incorrect MAC address format')
        self.mac = mac

    def setOnline(self, status):
        self.online = Ternary(status)
        self.setOnlineIcon()

    def setOnlineIcon(self):
        if self.online == Ternary.ON:
            self.setIcon(ICONS.ON)
        elif self.online == Ternary.OFF:
            self.setIcon(ICONS.OFF)
        else:
            self.setIcon(ICONS.QUESTION)
        self.setIconSize(QtCore.QSize(16, 16))

    def _ping(self):
        """Ping this PC"""
        self.isPinging = True
        self.setOnline(Ternary.UNKNOWN)
        if system_name().lower() == 'windows':
            ping_param = '-n 1 {} >nul 2>&1'.format(self.name)
        else:
            ping_param = '-c 1 {}'.format(self.ip)
        print('Pinging {}'.format(self.name))
        isOnline = os.system('ping {}'.format(ping_param)) == 0
        if isOnline:
            self.setOnline(Ternary.ON)
        else:
            self.setOnline(Ternary.OFF)
        self.isPinging = False
        return isOnline

    def ping(self):
        if not self.isPinging:
            ping_thread = threading.Thread(target=self._ping)
            ping_thread.start()

    def _wake(self):
        # Pad the synchronization stream.
        print('Sending magic packet to {}'.format(self.name))
        data = ''.join(['FFFFFFFFFFFF', self.mac * 20])
        send_data = b''

        # Split up the hex values and pack.
        for i in range(0, len(data), 2):
            send_data = b''.join([send_data,
                                  struct.pack('B', int(data[i: i + 2], 16))])

        # Broadcast it to the LAN.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(send_data, (CONFIG.BROADCAST_IP, 7))
        return True

    def wake(self):
        if not self.isChecked():
            return True
        if self.online != Ternary.ON:
            self._wake()
            self.setOnline(Ternary.UNKNOWN)
            # self.checked = False
        else:
            utils.sendWarning('{} is already alive.'.format(self.name))


class PCList(QtGui.QGroupBox):
    """A List of Buttons/Models of PCs, used to display as a list."""

    def __init__(self, title, executer, pc_list=None):
        """Consturcts a new PCList.

        Args:
            title (str): The Title for the list, will be shown.
            executer (function): The function to add command executions for a
                list of client PCs
            pc_list (list, optional): The List of PCs added to the object.
        """
        super().__init__(title)
        self.layout = QtGui.QVBoxLayout()
        self.executer = executer
        if pc_list is not None:
            self.load(pc_list)

    def __iter__(self):
        return iter(self.children())

    def load(self, pc_list):
        """Append all PCs in a list to this PCList.

        Args:
            pc_list (list): A list of PCs.
        """
        return [self.append(pc) for pc in pc_list]

    def append(self, pc):
        """Append a single pc to the List:

        Args:
            pc (PC): The pc.
        """
        self.layout.addWidget(pc)
        pc.ping()
        self.setLayout(self.layout)

    def selectAll(self):
        return [i.setChecked(True) for i in self if isinstance(i, PC)]

    def wake(self):
        return [i.wake() for i in self if isinstance(i, PC)]

    def execute(self, command, wait=False):
        clients = [pc for pc in self if isinstance(pc, PC) and pc.isChecked()]
        self.executer(clients, command, wait)

    def ping(self):
        [i.ping() for i in self if isinstance(i, PC) and i.isChecked()]


class PCListsWidget(QtGui.QWidget):
    """A widget to display multiple PCLists side by side."""

    def __init__(self):
        """Construct a new PCListsWidget."""
        super().__init__()
        self.createLayout()

    def __iter__(self):
        return iter(self.lists.children())

    def createLayout(self):
        self.layout = QtGui.QVBoxLayout()
        self.listsLayout = QtGui.QHBoxLayout()
        self.controlsLayout = QtGui.QHBoxLayout()
        self.lists = QtGui.QWidget()
        self.controls = QtGui.QWidget()
        self.lists.setLayout(self.listsLayout)
        self.controls.setLayout(self.controlsLayout)
        self.layout.addWidget(self.lists)
        self.layout.addWidget(self.controls)
        self.setLayout(self.layout)

    def addList(self, pclist):
        """Add a new PCList to the widget.

        Args:
            pclist (PCList): The new list
        """
        selectAllButton = QtGui.QPushButton('Select all')
        selectAllButton.clicked.connect(pclist.selectAll)
        self.listsLayout.addWidget(pclist)
        self.controlsLayout.addWidget(selectAllButton)
        self.lists.setLayout(self.listsLayout)
        self.controls.setLayout(self.controlsLayout)


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        """Construct a new MainWindow"""
        super().__init__()
        self.PCButtonGroup = QtGui.QButtonGroup()
        self.executeable = ('','')

    def createLayout(self):
        self.cwidget = QtGui.QWidget()
        self.clayout = QtGui.QVBoxLayout()
        self.setCentralWidget(self.cwidget)
        self.pclistswidget = PCListsWidget()
        self.clayout.addWidget(self.pclistswidget)
        self.clayout.addWidget(self.createControls())
        self.cwidget.setLayout(self.clayout)

    def createControls(self):
        controlwidget = QtGui.QWidget()
        controllayout = QtGui.QGridLayout()
        controllayout.addWidget(self._button('Ping',
                                             self.ping), 0, 0)
        controllayout.addWidget(self._button('Wake up',
                                             self.wake), 0, 1)
        controllayout.addWidget(self._button('Shutdown',
                                             self.shutdown), 0, 2)
        controllayout.addWidget(self._button('Select executeable',
                                             self.commandSelector), 1, 0)
        controllayout.addWidget(self._button('Execute',
                                             self.execute), 1, 1)
        controllayout.addWidget(self._button('oTree',
                                             self.startOTree), 1, 2)
        controlwidget.setLayout(controllayout)
        return controlwidget

    def _button(self, name, func):
        button = QtGui.QPushButton(name)
        button.clicked.connect(func)
        return button

    def ping(self):
        return [i.ping() for i in self.pclistswidget if isinstance(i, PCList)]

    def execute(self, executeable=None):
        if executeable is None:
            executeable = self.executeable
        return [i.execute(executeable) for i in self.pclistswidget
                if isinstance(i, PCList)]

    def wake(self):
        return [i.wake() for i in self.pclistswidget if isinstance(i, PCList)]

    def shutdown(self):
        self.execute('shutdown-command')

    def commandSelector(self):
        e = QtGui.QFileDialog.getOpenFileName(self, 'Find the executeable',
                                                    CONFIG.NETWORK_DRIVE,
                                                    '')[0]
        if system_name().lower() == 'windows':
            e = e.replace('/','\\')
        self.executeable = e

    def startOTree(self):
        utils.sendWarning('Not implemented yet!')
        # return [i.execute(self.OTREE_EXEC__) for i in self.pclistswidget
                # if isinstance(i, PCList)]

    def about(self):
        pass
