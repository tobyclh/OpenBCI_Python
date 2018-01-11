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
from PyQt5.QtCore import QSize, QBasicTimer, Qt
from PyQt5.QtGui import QImage, QPalette, QBrush, QFont
from PyQt5.QtWidgets import *
from scipy.signal import butter, lfilter
import skimage.io


class Filter(plugintypes.IPluginExtended):
    def activate(self):
        self.memory = 5000
        self.past_data = []
        for i in range(self.memory):
            self.past_data.append(np.zeros([8]))
        self.count = 0
        self.sampling_rate = 250
        self.notch_filter = 50
        self.window = None

        def gui_thread():
            app = QApplication(sys.argv)
            self.window = MainWindow(np.zeros([400, 400, 3]))
            app.exec_()
        t = Thread(target=gui_thread)
        t.daemon = True
        t.start()
        
        print("Filter activated")

    def deactivate(self):
        print("Filter Goodbye")

    def show_help(self):
        print("Add callback function to peaks.")

    def __call__(self, sample):
        if sample:
            # print('called')
            data = np.asarray(sample.channel_data).reshape([8])
            self.past_data.append(data)
            if len(self.past_data) > self.memory:
                del self.past_data[0]
            self.count += 1

    def update_plot(self):
        print('update_plot')
        raw_data = np.asarray(np.copy(self.past_data)).squeeze().T
        # print(raw_data.shape)
        filtered = [butter__filter(raw_data[i, :], self.notch_filter - 1,
                                           self.notch_filter + 1, self.sample_rate, filter_type='bandstop') for i in range(8)]
        filtered = [butter__filter(filtered[i], 7,
                                           13, self.sample_rate, filter_type='bandpass') for i in range(8)]
        fig = plt.figure()
        plot = fig.add_subplot(111)
        plot.plot(raw_data[0, int(self.memory * 0.2):]*0.0001)
        plot.plot(filtered[0][int(self.memory * 0.2):])
        fig.canvas.draw()
        data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        
        plt.close()
        fig.clear()

        self.plot = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        # skimage.io.imsave('foo.jpg', self.plot)
        self.window.update_image(self.plot)


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
        # resize Image to widgets size
        # 10 = Windowrole
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
