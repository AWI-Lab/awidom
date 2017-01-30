import PySide.QtCore as QtCore
from PySide.QtCore import QPoint
from PySide.QtCore import QSize
import PySide.QtGui as QtGui
import yaml
import sys
from functools import partial

CLIENTFILE__ = 'clients.yaml'
ORG__ = 'Alfred-Weber-Institut für Wirtschaftwissenschaften'
NAME__ = 'AWIDominator'


class AWIDom(QtGui.QApplication):
    """Handles the whole programm."""
    def __init__(self, cfile=CLIENTFILE__):
        super().__init__(sys.argv)
        self.setOrganizationName(ORG__)
        self.setApplicationName(NAME__)
        self.left = []
        self.right = []
        self.loadConfig(cfile)
        self.mainwindow = MainWindow()
        self.mainwindow.left = self.left
        self.mainwindow.right = self.right
        self.mainwindow.createLayout()

    def loadConfig(self, cfile):
        with open(cfile, 'r') as f:
            try:
                clientsconf = yaml.load(f)
                self.loadPCs(self.left, clientsconf['left'])
                self.loadPCs(self.right, clientsconf['right'])
            except yaml.YAMLError as e:
                print(e)

    def loadPCs(self, target, confs):
        for c in confs:
            target.append(PC(c['id'], c['name'], c['ip'], c['mac']))
        target.sort()

    def run(self):
        self.mainwindow.show()


class PC(object):
    """Handles one PC in the lab"""
    def __init__(self, id, name, ip, mac):
        self.id = id
        self.name = name
        self.ip = ip
        self.mac = mac
        self.online = False
        self.checkbox = self.genCheckbox()

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return repr((self.id, self.name, self.ip, self.mac))

    def __str__(self):
        return ('PC: [id: {}, name: {}, ip: {}, mac: {}]'
                ''.format(self.id, self.name, self.ip, self.mac))

    def ping(self):
        pass

    def genCheckbox(self):
        checkbox = QtGui.QCheckBox(self.name)
        return checkbox


class MainWindow(QtGui.QMainWindow):
    """docstring for MainWindow."""
    def __init__(self):
        super().__init__()

    def createMenus(self):
        self.menuBar = QtGui.QMenuBar()
        helpMenu = QtGui.QMenu('Hilfe')
        self.menuBar.addMenu(helpMenu)
        act = helpMenu.addAction('Über anzeign')
        act.triggered.connect(self.about())

    def createLayout(self):
        self.cwidget = QtGui.QStackedWidget()
        self.setCentralWidget(self.cwidget)
        btngroup = QtGui.QButtonGroup()

        leftrightlayout = QtGui.QHBoxLayout()
        leftrightwidget = QtGui.QGroupBox()

        leftlayout = QtGui.QVBoxLayout()
        leftwidget = QtGui.QGroupBox()
        for pc in self.left:
            button = pc.genCheckbox()
            btngroup.addButton(button)
            leftlayout.addWidget(button)
        leftwidget.setLayout(leftlayout)

        rightlayout = QtGui.QVBoxLayout()
        rightwidget = QtGui.QGroupBox()
        for pc in self.right:
            button = pc.genCheckbox()
            btngroup.addButton(button)
            rightlayout.addWidget(button)
        rightwidget.setLayout(rightlayout)

        leftrightlayout.addWidget(leftwidget)
        leftrightlayout.addWidget(rightwidget)
        leftrightwidget.setLayout(leftrightlayout)

        self.cwidget.addWidget(leftrightwidget)

    def about(self):
        QtGui.QMessageBox.about(self, 'AWIDominator', 'HILFEEEE')


if __name__ == "__main__":
    awidom = AWIDom()
    awidom.run()
    sys.exit(awidom.exec_())
