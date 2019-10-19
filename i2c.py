""" Provide access to /dev/i2c-* devices """

import os, struct, fcntl
from ctypes import *

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
    def __init__(self, bus, addr, retries=None, timeout=None):
        self.addr=addr
        self.fd=os.open("/dev/i2c-%d" % bus, os.O_RDWR)
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
        messages=[]
        for n in range(0,len(specs)):
            if specs[n] is None: continue
            if not n & 1:
                data =specs[n]
                if type(data) not in (tuple, list): data = [data]
                size=len(data)
                buffer = create_string_buffer(struct.pack("%dB" % size,*data),size)
                messages.append(i2c_msg(addr=self.addr, flags=0, len=size, buf=addressof(buffer)))
            else:
                size = int(specs[n])
                buffer = create_string_buffer(size)
                messages.append(i2c_msg(addr=self.addr, flags=I2C_M_RD, len=size, buf=addressof(buffer)))
        t = (i2c_msg*len(messages))(*messages)
        fcntl.ioctl(self.fd, I2C_RDWR, i2c_rdwr_ioctl_data(msgs=addressof(t), nmsgs=len(t)), False)
        return map(lambda m:map(ord,list(string_at(m.buf,m.len))),filter(lambda m:m.flags & I2C_M_RD, messages))

    # set number of retries on NACK
    def set_retries(self, n):
        fcntl.ioctl(self.fd, I2C_RETRIES, c_uint(n), False)

    # set NACK timeout in tenths of a second
    def set_timeout(self, n):
        fcntl.ioctl(self.fd, I2C_TIMEOUT, c_uint(n), False)

if __name__ == "__main__":

    from time import sleep

    # Open /dev/i2c-1 which attaches to some gizmo
    gizmo=i2c(0,1)

    while True:
        # Send 0x4142
        # Receive 7-byte response
        # Send 3 zeros
        print gizmo.io([0x41,42], 7, [0,0,0])
        sleep(.1)
