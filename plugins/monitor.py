import plugin_interface as plugintypes
import PyQt5
import threading
from peakutils.peak import indexes

class PluginPeakMonitor(plugintypes.IPluginExtended):
    def activate(self):
        print("PeakMonitor activated")

    def deactivate(self):
        print("PeakMonitor Goodbye")

    def show_help(self):
        print("Add callback function to peaks.")

    def __call__(self, sample):
        if sample:
            if self.imp_channels > 0:
                sample_string = "ID: %f\n%s\n%s\n%s" % (sample.id, str(sample.channel_data)[
                                                        1:-1], str(sample.aux_data)[1:-1], str(sample.imp_data)[1:-1])
            else:
                sample_string = "ID: %f\n%s\n%s" % (sample.id, str(sample.channel_data)[
                                                    1:-1], str(sample.aux_data)[1:-1])
            print("---------------------------------")
            print(sample_string)
            print("---------------------------------")
            


        # DEBBUGING
        # try:
        #     sample_string.decode('ascii')
        # except UnicodeDecodeError:
        #     print("Not a ascii-encoded unicode string")
        # else:
        #     print(sample_string)
