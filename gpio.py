# Python access to /dev/gpiochip* devices

import os, fcntl
from ctypes import *

# For debug, dump ctypes.Structure
# def dump(struct):
#     bytes=map(ord,memoryview(struct).tobytes())
#     for i in struct._fields_:
#         name=i[0]
#         field=struct.__class__.__dict__[name]
#         print "%20s ofs=%04d size=%04d:" % (name,field.offset,field.size)," ".join(map(lambda b:"%02X" % b, bytes[field.offset:field.offset+field.size]))

# This information is from linux/gpiochip.h

GPIOHANDLES_MAX = 64

# configure gpio and get handle
GPIO_GET_LINEHANDLE_IOCTL = 0xC16CB403
GPIOHANDLE_REQUEST_INPUT = 1
GPIOHANDLE_REQUEST_OUTPUT = 2
GPIOHANDLE_REQUEST_ACTIVE_LOW = 4
GPIOHANDLE_REQUEST_OPEN_DRAIN = 8
GPIOHANDLE_REQUEST_OPEN_SOURCE = 16
class gpiohandle_request(Structure):
    _fields_ = [
        ("lineoffsets", c_uint * GPIOHANDLES_MAX),          # up to 64 line numbers (we only use the first one)
        ("flags", c_uint),                                  # see below
        ("default_values", c_ubyte * GPIOHANDLES_MAX),      # default values
        ("consumer_label", c_char * 32),                    # arbitrary label for handle
        ("lines", c_uint),                                  # number of lineoffsets
        ("fd", c_int),                                      # return descriptor
    ]

# set or get gpio state
GPIOHANDLE_GET_LINE_VALUES_IOCTL = 0xC040B408
GPIOHANDLE_SET_LINE_VALUES_IOCTL = 0xC040B409
class gpiohandle_data(Structure):
    _fields_ = [("values", c_ubyte * GPIOHANDLES_MAX)]      # desired output or current input state (we only use the first one)

# Open and manipulate gpio "line" on gpiochip "chip".
# Config options are:
#   output     : if true then configure the gpio as an output, else an input
#   active_low : if true the the state is inverted relative to gpio input or output signal (i.e. negative logic).
#   open_drain : if true then the gpio is configured for open_drain, this is hardware dependent
#   open_drain : if true then the gpio is configured for open_source, this is hardware dependent
#   state      : if true then the output will be set, if false it is cleared (subject to inversion bu "active_low")
# Unspecified config options will be False
class gpio():

    def __init__(self, chip, line, active_low=False, open_drain=False, open_source=False, output=False, state=False):
        self.chip = chip
        self.line = line

        # open the device
        self.chipfd = os.open("/dev/gpiochip%d" % self.chip, os.O_RDWR)

        # pre-allocate data structures for speed
        self.gpiohandle_reqest = gpiohandle_request()
        self.gpiohandle_data = gpiohandle_data()

        # set initial configuration
        self.linefd=None
        self.configure(active_low=active_low, open_source=open_source, open_drain=open_drain, output=output, state=state)

    def __del__(self):
        # close file handles
        try:
            os.close(self.linefd)
        except:
            pass
        try:
            os.close(self.chipfd)
        except:
            pass

    # Configure gpio, config options as above but if not specified then are not changed
    def configure(self, active_low=None, open_drain=None, open_source=None, output=None, state=None):
        # update specified configs
        if output is not None:
            self.output=bool(output)
        if state is not None:
            self.state=bool(state)
        if active_low is not None:
            self.active_low=bool(active_low)
        if open_drain is not None:
            self.open_drain=bool(open_drain)
        if open_source is not None:
            self.open_source=bool(open_source)

        # update gpio and get new request handle
        self.gpiohandle_reqest.lineoffsets[0] = self.line
        self.gpiohandle_reqest.flags = 0
        self.gpiohandle_reqest.lines = 1
        self.gpiohandle_reqest.consumer_label = "gpio.py"
        # set the flags
        if self.output:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_OUTPUT
        else:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_INPUT
        if self.active_low:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_ACTIVE_LOW
        if self.open_drain:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_OPEN_DRAIN
        elif self.open_source:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_OPEN_SOURCE
        # close old handle
        if self.linefd is not None:
            os.close(self.linefd)
        # config and get new handle
        fcntl.ioctl(self.chipfd, GPIO_GET_LINEHANDLE_IOCTL, self.gpiohandle_reqest, True)
        self.linefd = self.gpiohandle_reqest.fd
        # update if input
        if not self.output: self.get_input()

    # change gpio to an output and set high or low
    def set_output(self, state):
        if not self.output:
            # change to output and set the state
            self.configure(output=True, state=state)
        else:
            # already an output, just update the state
            self.state = bool(state)
            self.gpiohandle_data.values[0] = int(state)
            fcntl.ioctl(self.linefd, GPIOHANDLE_SET_LINE_VALUES_IOCTL, self.gpiohandle_data, True)

    # change gpio to an input and return current state
    def get_input(self):
        if self.output:
            # change to an input and update the state
            self.configure(output=False)
        else:
            # already an input, just read current state
            fcntl.ioctl(self.linefd, GPIOHANDLE_GET_LINE_VALUES_IOCTL, self.gpiohandle_data, True)
            self.state = bool(self.gpiohandle_data.values[0])
        return self.state

    # show gpio configuration
    def show(self, label=None):
        print "gpio %d.%d: output=%s state=%s active_low=%s open_drain=%s open_source=%s" % (
            self.chip, self.line, self.output, self.state, self.active_low, self.open_drain, self.open_source)

if __name__ == "__main__":

    # Demo for Raspberry Pi 3B

    from time import sleep

    gpio5=gpio(0, 5)    # aka header pin 29
    gpio5.show()

    gpio6=gpio(0, 6)    # aka header pin 31
    gpio6.show()

    gpio7=gpio(0, 7)    # aka header pin 26
    gpio7.show()

    # inputs float high, sequence gpios 5 and 6 until gpio7 is grounded
    while gpio7.get_input():
        for n in range(0,4):
            gpio5.set_output(n&1)
            gpio6.set_output(n&2)

    # toggle gpio5 as fast as possible (about 32Khz on an idle system)
    while True:
        gpio5.set_output(not gpio5.state)
