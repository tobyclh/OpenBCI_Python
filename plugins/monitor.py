import plugin_interface as plugintypes
import threading
import peakutils
from PyQt5.QtWidgets import *
import sys
from PyQt5.QtCore import QSize, QBasicTimer, Qt
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont
from PyQt5.QtWidgets import *
import numpy as np
from threading import Thread
import matplotlib.animation as animation
import matplotlib.pyplot as plt


class PluginPeakMonitor(plugintypes.IPluginExtended):
    def activate(self):
        def gui_thread():
            app = QApplication(sys.argv)
            oMainwindow = MainWindow(self)
            app.exec_()
        t = Thread(target=gui_thread)
        t.daemon = True
        t.start()
        self.memory = 200
        self.past_data = np.zeros([8, 1])
        self.count = 0
        print("PeakMonitor activated")

    def deactivate(self):
        print("PeakMonitor Goodbye")

    def show_help(self):
        print("Add callback function to peaks.")

    def __call__(self, sample):
        if sample:
            data = np.asarray(sample.channel_data).reshape([8,1])
            self.past_data = np.concatenate([self.past_data, data])
            print('data : {}'.format(data))
            idxes = [peakutils.indexes(self.past_data[chnl,:], thres=0.5, min_dist=30) for chnl in range(self.past_data.shape[0])]

            print('peak {}'.format(len(idxes)))
            if self.past_data.shape[1] > self.memory:
                self.past_data = self.past_data[-self.memory:, :]


class MainWindow(QWidget):
    def __init__(self, monitor):
        QWidget.__init__(self)
        self.setGeometry(100, 100, 900, 395)
        oImage = QImage("plugins/minion_background.gif")
        # resize Image to widgets size
        sImage = oImage.scaled(QSize(900, 395))
        palette = QPalette()
        # 10 = Windowrole
        palette.setBrush(10, QBrush(sImage))
        self.setPalette(palette)
        self.timer = QBasicTimer()
        self.steps = np.zeros(6)
        # test, if it's really backgroundimage
        # self.label = QLabel('Test', self)
        # self.label.setGeometry(50, 50, 200, 50)

        self.pbar = []
        parts = ['Upper Arm', 'Lower Arm', 'Leg']
        f = QFont("Arial", 14)
        for i, part in enumerate(parts):
            part_name = 'Left ' + part
            label = QLabel(part_name, self)
            label.setGeometry(50, 40 + i * 120, 200, 30)
            label.setFont(f)
            bar = QProgressBar(self)
            bar.setGeometry(50, 70 + i * 120, 200, 30)
            self.pbar.append(bar)
        for i in range(3):
            part_name = 'Right ' + part
            label = QLabel(part_name, self)
            label.setGeometry(650, 40 + i * 120, 200, 30)
            label.setFont(f)
            bar = QProgressBar(self)
            bar.setGeometry(650, 70 + i * 120, 200, 30)
            self.pbar.append(bar)

        self.show()
        self.timer.start(100, self)

    def timerEvent(self, e):
        if np.any(self.steps >= 100):
            # self.timer.stop()
            self.setWindowState(self.windowState() & ~
                                Qt.WindowMinimized | Qt.WindowActive)
            # this will activate the window
            self.activateWindow()
        # print('steps adding {}'.format(self.steps))
        self.steps += 1
        self.steps = np.minimum(self.steps, 100)
        for step, bar in zip(self.steps, self.pbar):
            bar.setValue(step)

    def reset_metre(self, idx):
        self.steps[idx] = 0
        self.pbar[idx].setValue(0)

    def reduce_metre(self, idx, value):
        self.steps[idx] -= value
        self.pbar[idx].setValue(self.steps[idx])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    oMainwindow = MainWindow()
    sys.exit(app.exec_())
