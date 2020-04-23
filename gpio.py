# Python access to gpio's via /dev/gpiochip* devices.

# Note gpio state will not be retained when the program exits, use gpio_sysfs
# if you need that.

from __future__ import print_function
import os, fcntl, glob
from ctypes import *

# For debug, dump ctypes.Structure
# def dump(struct):
#     bytes=map(ord,memoryview(struct).tobytes())
#     for i in struct._fields_:
#         name=i[0]
#         field=struct.__class__.__dict__[name]
#         print("%20s ofs=%04d size=%04d:" % (name,field.offset,field.size)," ".join(map(lambda b:"%02X" % b, bytes[field.offset:field.offset+field.size])))

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

class gpio:

    # Initialize gpio "line" on gpiochip "chip".
    # Config options are:
    #   output     : 0=configure as input, 1=configure as normal output, 2=as open drain output, 3=as open source output. Default is 0.
    #   invert     : if true the the state is inverted relative to gpio input or output signal (i.e. negative logic). Default is False.
    #   state      : if true then output is set, if false output is cleared. Or just reports current status if input (subject to "invert"). Default is False.
    # Unspecified options are 0/False.
    def __init__(self, line, chip=0, invert=False, output=0, state=False):
        self.chip = chip
        self.line = line

        # open the device
        self.chipfd = os.open("/dev/gpiochip%d" % self.chip, os.O_RDWR)

        # pre-allocate data structures for speed
        self.gpiohandle_reqest = gpiohandle_request()
        self.gpiohandle_data = gpiohandle_data()

        # set initial configuration
        self.linefd=None
        self.configure(invert=bool(invert), output=int(output), state=bool(state))

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

    # Alter gpio output, invert, and state as above, but default None means do not change.
    def configure(self, invert=None, output=None, state=None):
        # update specified configs
        if invert is not None:
            self.invert=bool(invert)
        if output is not None:
            self.output=int(output)
        if state is not None:
            self.state=bool(state)

        # update gpio and get new request handle
        self.gpiohandle_reqest.lineoffsets[0] = self.line
        self.gpiohandle_reqest.flags = 0
        self.gpiohandle_reqest.lines = 1
        self.gpiohandle_reqest.consumer_label = b"gpio.py"
        # set the flags
        if self.output:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_OUTPUT
            if self.output == 2: self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_OPEN_DRAIN
            if self.output == 3: self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_OPEN_SOURCE
        else:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_INPUT
        if self.invert:
            self.gpiohandle_reqest.flags |= GPIOHANDLE_REQUEST_ACTIVE_LOW
        # close old handle
        if self.linefd is not None:
            os.close(self.linefd)
        # config and get new handle
        fcntl.ioctl(self.chipfd, GPIO_GET_LINEHANDLE_IOCTL, self.gpiohandle_reqest, True)
        self.linefd = self.gpiohandle_reqest.fd
        # update if input
        if not self.output: self.get_input()

    # change gpio to an normal output and then set high or low
    # type can be 1, 2 or 3 to set the output type
    def set_output(self, state):
        if not self.output:
            # change to output and set the state
            self.configure(output=1, state=state)
        else:
            # already an output, just update the state
            self.state = bool(state)
            self.gpiohandle_data.values[0] = int(state)
            fcntl.ioctl(self.linefd, GPIOHANDLE_SET_LINE_VALUES_IOCTL, self.gpiohandle_data, True)

    # change gpio to an input and return current state
    def get_input(self):
        if self.output:
            # change to an input and update the state
            self.configure(output=0)
        else:
            # already an input, just read current state
            fcntl.ioctl(self.linefd, GPIOHANDLE_GET_LINE_VALUES_IOCTL, self.gpiohandle_data, True)
            self.state = bool(self.gpiohandle_data.values[0])
        return self.state

    # show gpio configuration
    def show(self, label=None):
        print("gpio %d.%d: output=%s state=%s invert=%s" % (self.chip, self.line, self.output, self.state, self.invert))

if __name__ == "__main__":

    # Demo for Raspberry Pi 3B
    gpio5=gpio(5, output=True)   # aka header pin 29
    gpio5.show()

    gpio6=gpio(6, output=True)   # aka header pin 31
    gpio6.show()

    gpio7=gpio(7, invert=True)   # aka header pin 26
    gpio7.show()

    # Sequence gpios 5 and 6 until gpio7 is grounded
    while not gpio7.get_input():
        for n in range(0,4):
            gpio5.set_output(n & 1)
            gpio6.set_output(n & 2)

    # Toggle gpio5 as fast as possible
    while True:
        gpio5.set_output(not gpio5.state)
