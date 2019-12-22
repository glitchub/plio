""" Provide access to /dev/i2c-* devices """

from __future__ import print_function
import os, fcntl
from ctypes import *
from itertools import count

# This information from linux/i2c-dev.h and linux/i2c.h

class i2c_msg(Structure):
    _fields_ = [
        ("addr",  c_ushort),    # slave address
        ("flags", c_ushort),    # 0 or I2C_M_RD
        ("len",   c_ushort),    # length of buffer
        ("buf",   c_void_p)     # pointer to buffer
    ]
I2C_M_RD = 1                    # if set, read from slave

class i2c_rdwr_ioctl_data(Structure):
    _fields_ = [
        ("msgs",  c_void_p),    # address of array of i2c_msgs
        ("nmsgs", c_uint)       # number of i2c_msgs in the array
    ]

I2C_RDWR_IOCTL_MAX_MSGS = 42    # max value of nmsgs

# Various IOCTLs
I2C_RDWR    = 0x0707            # perform combined R/W transfer (one STOP only)
I2C_RETRIES = 0x0701            # number of times a device address should be polled when not acknowledging
I2C_TIMEOUT = 0x0702            # set timeout in units of 10 ms

class i2c():

    # init i2c controller, note bus == None enables stub operation
    def __init__(self, bus, addr, retries=None, timeout=None):
        assert 0x07 < addr < 0x78 # disallow address ranges 0000xxx and 1111xxx
        if bus is not None: self.fd=os.open("/dev/i2c-%d" % bus, os.O_RDWR)
        else: self.fd = None
        self.addr=addr
        if retries is not None: self.set_retries(retries)
        if timeout is not None: self.set_timeout(timeout)

    # Perform atomic I2C operations with a single STOP.
    #
    # The argument list consists of alternating write and read specifications,
    # starting with write.
    #
    # A write specification can be 'None' (skip write operation), an int (write
    # that single byte), or a tuple/list (write the list of bytes).
    #
    # A read specification can be 'None' (skip read operation), or an int (read
    # that many bytes)
    #
    # Returns a list of lists of read bytes, or [] if no reads requested.
    def io(self, *specs):
        assert 0 < len(specs) <= I2C_RDWR_IOCTL_MAX_MSGS
        wbufs=[]    # persistent write buffers
        rbufs=[]    # persistent read buffers
        messages=[] # messages to be sent
        for n in range(0,len(specs)):
            if specs[n] is None: continue
            if not n & 1:
                data = self.blist(specs[n])
                size = len(data)
                wbufs.append(create_string_buffer(bytes(bytearray(data)),size))
                messages.append(i2c_msg(addr=self.addr, flags=0, len=size, buf=addressof(wbufs[-1])))
            else:
                size = int(specs[n])
                rbufs.append(create_string_buffer(size))
                messages.append(i2c_msg(addr=self.addr, flags=I2C_M_RD, len=size, buf=addressof(rbufs[-1])))

        t = (i2c_msg*len(messages))(*messages)
        if self.fd is not None:
            fcntl.ioctl(self.fd, I2C_RDWR, i2c_rdwr_ioctl_data(msgs=addressof(t), nmsgs=len(t)), False)
        else:
            # bus == None, just dump to stdout
            print("%d messages:" % len(t))
            for m in t:
                if m.flags:
                    print("  %X: read %d to %X" % (m.addr, m.len, m.buf))
                else:
                    print("  %X: write %d from %X" % (m.addr, m.len, m.buf),[hex(b) for b in bytearray(string_at(m.buf, m.len))])

        return [list(bytearray(m.raw)) for m in rbufs]

    # set number of retries on NACK
    def set_retries(self, n):
        fcntl.ioctl(self.fd, I2C_RETRIES, c_uint(n), False)

    # set NACK timeout in tenths of a second
    def set_timeout(self, n):
        fcntl.ioctl(self.fd, I2C_TIMEOUT, c_uint(n), False)

    # cast data object to a list of bytes, works with python 2 or 3
    @staticmethod
    def blist(data):
        if type(data) is int: data=[data]
        elif type(data) is bytes: data = bytearray(data)
        elif type(data) is str: data = bytearray(data.encode("utf8"))
        if type(data) is not list: data=list(data)
        return data

if __name__ == "__main__":

    from time import sleep

    # Open device with address 0x45
    # bus == None, just dump packet info to stdout
    gizmo=i2c(bus=None, addr=0x45)

    # Send 0x4142, receive 7-byte response, then send 3 zeros
    print(gizmo.io([0x41, 0x42], 7, [0, 0, 0]))
