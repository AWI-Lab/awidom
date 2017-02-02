import copy
from enum import Enum
from functools import partial
import PySide.QtCore as QtCore
from PySide.QtCore import QDir
from PySide.QtCore import QPoint
from PySide.QtCore import QSize
import PySide.QtGui as QtGui
import random
import sys
import yaml

CLIENTFILE__ = 'clients.yaml'
OTREE_EXEC__ = 'chrome.exe'
ORG__ = 'Alfred-Weber-Institut für Wirtschaftwissenschaften'
NAME__ = 'AWIDominator'


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
        for c in confs:
            target.append(PC(c['id'], c['name'], c['ip'], c['mac']))
        # target.sort()

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
        self.mac = mac
        self.online = Ternary(Ternary.UNKNOWN)
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

    def ping(self):
        """Ping this PC"""
        if bool(random.randint(0, 1)):
            self.online = Ternary.ON
        elif bool(random.randint(0, 1)):
            self.online = Ternary.OFF
        self.setOnlineIcon()
        return self.online

    def wakeUp(self):
        # TODO(d1): docstring
        if not self.isChecked():
            return True
        if self.online != Ternary.ON:
            print('Waking up {}'.format(self.name))
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
        for pc in pc_list:
            self.append(pc)

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
        for i in self:
            if isinstance(i, PC):
                i.setChecked(True)

    def wakeUp(self):
        # TODO(d1): docstring
        for i in self:
            if isinstance(i, PC):
                i.wakeUp()

    def execCommand(self, command):
        # TODO(d1): docstring
        for i in self:
            if isinstance(i, PC):
                i.execCommand(command)


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
        controllayout.addWidget(self.wakeUpButton(), 0, 0)
        controllayout.addWidget(self.oTreeButton(), 0, 1)
        controllayout.addWidget(self.selectButton(), 1, 0)
        controllayout.addWidget(self.execButton(), 1, 1)
        controlwidget.setLayout(controllayout)
        return controlwidget

    def selectButton(self):
        # TODO(d1): docstring
        selectbutton = QtGui.QPushButton('Select executeable')
        selectbutton.clicked.connect(self.commandSelector)
        return selectbutton

    def commandSelector(self):
        # TODO(d1): docstring
        self.executeable = QtGui.QFileDialog.getOpenFileName(self, 'Find the executeable', '/', '')

    def execButton(self):
        # TODO(d1): docstring
        execbutton = QtGui.QPushButton('Execute')
        execbutton.clicked.connect(partial(self.execCommand, command=self.executeable))
        return execbutton

    def execCommand(self, command):
        # TODO(d1): docstring
        print(self.executeable[0])
        for i in self.pclistswidget:
            if isinstance(i, PCList):
                i.execCommand(command)

    def wakeUpButton(self):
        # TODO(d1): docstring
        wolbutton = QtGui.QPushButton('Wake Up')
        wolbutton.clicked.connect(self.wakeUp)
        return wolbutton

    def wakeUp(self):
        # TODO(d1): docstring
        for i in self.pclistswidget:
            if isinstance(i, PCList):
                i.wakeUp()

    def oTreeButton(self):
        # TODO(d1): docstring
        otreebutton = QtGui.QPushButton('oTree')
        otreebutton.clicked.connect(self.startOTree)
        return otreebutton

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
