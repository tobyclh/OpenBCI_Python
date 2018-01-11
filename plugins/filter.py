import plugin_interface as plugintypes
import threading
import peakutils
from PyQt5.QtWidgets import *
import sys
import numpy as np
from threading import Thread
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import *
import sys
from PyQt5.QtCore import QSize, QBasicTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont
from PyQt5.QtWidgets import *
from scipy.signal import butter, lfilter
import skimage.io
import time

class SignalCollection(QObject):
    timer_trigger = pyqtSignal()
    reduce_trigger = pyqtSignal(int , int)
    set_trigger = pyqtSignal([list])

class Filter(plugintypes.IPluginExtended):
    def activate(self):
        self.memory = 1000
        self.past_data = []
        for i in range(self.memory):
            self.past_data.append(np.zeros([8]))
        self.count = 0
        self.sampling_rate = 250
        self.notch_filter = 50
        self.window = None
        self.signals = SignalCollection()
        # def gui_thread():
        #     app = QApplication(sys.argv)
        #     self.window = MainWindow(np.zeros([400, 400, 3]))
        #     app.exec_()
        # t = Thread(target=gui_thread)
        # t.daemon = True
        # t.start()
        self.averages = [0 for _ in range(8)]
        self.minion_window = None
        self.steps = [0 for _ in range(8)]
        def minion_thread():
            app = QApplication(sys.argv)
            self.minion_window = MinionWindow()
            app.exec_()
        t = Thread(target=minion_thread)
        t.daemon = True
        t.start()

        
        print("Filter activated")

    def deactivate(self):
        print("Filter Goodbye")

    def show_help(self):
        print("Add callback function to peaks.")

    def __call__(self, sample):
        self.signals.set_trigger.connect(self.minion_window.set_metre)
        if sample:
            # print('called')
            data = np.asarray(sample.channel_data).reshape([8])
            self.past_data.append(data)
            if len(self.past_data) > self.memory:
                del self.past_data[0]
            self.count += 1
            if self.count is 200:
                for i, _ in enumerate(self.steps):
                    self.steps[i] += 2
                    self.steps[i] = np.minimum(100, self.steps[i])
                self.signals.set_trigger.emit(self.steps)
                self.count = 0
                t = Thread(target=self.update_plot)
                t.daemon = True
                t.start()

    def update_plot(self):
        print('update_plot')
        raw_data = np.asarray(np.copy(self.past_data)).squeeze().T
        # print(raw_data.shape)
        filtered = [butter__filter(raw_data[i, :], self.notch_filter - 1,
                                           self.notch_filter + 1, self.sample_rate, filter_type='bandstop') for i in range(8)]
        filtered = [butter__filter(filtered[i], 7,
                                           13, self.sample_rate, filter_type='bandpass') for i in range(8)]
        filtered = np.asarray(filtered)
        
        averages = np.abs(filtered).mean(axis=1)
        print('averages {} past {}'.format(averages, self.averages))
        active_channels = np.asarray(np.where(np.abs(filtered[:,-1])*0.9 - self.averages > 0))

        print('active_channels {}, {}'.format(active_channels, active_channels.shape))
        used_channel = [2,3]
        active_channels = [element for element in used_channel if element in active_channels]
        print('filtered active_channels {}'.format(active_channels))
        print('step {}'.format(self.steps))
        self.averages = averages
        
        channel2parts = {2:0, 3:3}
        if len(active_channels) > 0:
            for channel in active_channels:
                if channel2parts[channel] < 0 or channel2parts[channel] > len(self.steps):
                    continue
                self.steps[channel2parts[channel]] -= 5
                self.steps[channel2parts[channel]] = np.maximum(0, self.steps[channel2parts[channel]])


        # fig = plt.figure()
        # plot = fig.add_subplot(111)
        # plot.plot(filtered[2,int(self.memory * 0.2):])
        # plot.plot(filtered[3, int(self.memory * 0.2):]+400)
        # fig.canvas.draw()
        # data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        
        # plt.close()
        # fig.clear()

        # self.plot = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        # skimage.io.imsave('foo.jpg', self.plot)
        # self.window.update_image(self.plot)


def butter__filter(data, lowcut, highcut, fs, order=5, filter_type='bandpass'):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype=filter_type)
    y = lfilter(b, a, data)
    return y


class MainWindow(QWidget):
    def __init__(self, image):
        QWidget.__init__(self)
        self.scale = 800
        self.setGeometry(0, 0, self.scale, self.scale)
        self.palette = QPalette()
        qImg = self.get_qimage(image)
        self.palette.setBrush(10, QBrush(qImg))
        self.setPalette(self.palette)
        self.show()

    def get_qimage(self, image):
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImg = QImage(image, width, height, bytesPerLine, QImage.Format_RGB888).scaled(
            QSize(self.scale, self.scale))
        return qImg

    def update_image(self, image):
        qImg = self.get_qimage(image)
        self.palette.setBrush(10, QBrush(qImg))
        self.setPalette(self.palette)
        self.show()



class MinionWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setGeometry(100, 100, 900, 395)
        oImage = QImage("plugins/minion_background.gif")
        # resize Image to widgets size
        sImage = oImage.scaled(QSize(900, 395))
        palette = QPalette()
        # 10 = Windowrole
        palette.setBrush(10, QBrush(sImage))
        self.setPalette(palette)
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
        for i, part in enumerate(parts):
            part_name = 'Right ' + part
            label = QLabel(part_name, self)
            label.setGeometry(650, 40 + i * 120, 200, 30)
            label.setFont(f)
            bar = QProgressBar(self)
            bar.setGeometry(650, 70 + i * 120, 200, 30)
            self.pbar.append(bar)

        self.show()
        # self.timer = QBasicTimer()
        # self.timer.start(100, self)

    def timerEvent(self, e=0):
        if np.any(self.steps >= 100):
            # self.timer.stop()
            self.setWindowState(self.windowState() & ~
                                Qt.WindowMinimized | Qt.WindowActive)
            # this will activate the window
            self.activateWindow()
        print('steps adding {}'.format(self.steps))
        self.steps += 0.01
        self.steps = np.minimum(self.steps, 100)
        for step, bar in zip(self.steps, self.pbar):
            bar.setValue(int(step))
        
    def set_metre(self, values):
        self.steps = values
        if np.asarray(self.steps).max() >= 100:
            # self.timer.stop()
            self.setWindowState(self.windowState() & ~
                                Qt.WindowMinimized | Qt.WindowActive)
            # this will activate the window
            self.activateWindow()

        for step, bar in zip(self.steps, self.pbar):
            bar.setValue(int(step))

    def reset_metre(self, idx):
        self.steps[idx] = 0
        self.pbar[idx].setValue(0)

    def reduce_metre(self, idx, value):
        # print('idx')
        # print(idx)
        if idx < 0 or idx > len(self.steps):
            return
        self.steps[idx] -= value
        self.steps = np.maximum(self.steps, 0)
        print('reducing steps {}'.format(self.steps))
        self.pbar[idx].setValue(int(self.steps[idx]))
        return
