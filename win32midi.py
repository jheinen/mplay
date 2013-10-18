from ctypes import windll, c_void_p, c_int, byref


class midiDevice:
    def __init__(self):
        self.device = c_void_p()
        windll.winmm.midiOutOpen(byref(self.device), -1, 0, 0, 0)

    def midievent(self, buf):
        message = buf[0]
        if len(buf) > 1:
            message += buf[1] * 0x100
        if len(buf) > 2:
            message += buf[2] * 0x10000
        windll.winmm.midiOutShortMsg(self.device, c_int(message))

    def mididataset1(self, address, data):
        pass

    def close(self):
        windll.winmm.midiOutClose(self.device)