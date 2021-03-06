# Driver for ON N24C02 256 byte serial EEPROM

from __future__ import print_function

try: from i2c import i2c, blist
except: from .i2c import i2c, blist

import time

class n24c02:
    def __init__(self, bus, addr=0xa0):
        self.addr = addr
        self.i2c = i2c(bus=bus, addr=addr)

    # read len bytes from offset
    def read(self, offset, len=1):
        assert offset >= 0 and len >= 1 and offset+len <= 256
        return self.i2c.io(offset,len)[0]

    # write data to offset
    def write(self, offset, data):
        data = blist(data)              # convert data to list of ints
        assert offset >= 0 and len(data) >= 1 and offset + len(data) <= 256
        while data:
            chunk = 16 - (offset & 15)  # constrain to 16-byte page
            self.i2c.io([offset]+data[0:chunk])
            time.sleep(0.004)           # requires 4mS
            del data[0:chunk]
            offset += chunk

    # dump EEPROM contents to stdout
    def dump(self):
        data = self.read(0, 256)
        for ofs in range(0, 256, 32):
            print("%02X:" % ofs, "%02X "*32 % tuple(data[ofs:ofs+32]))

if __name__ == "__main__":

    # device address 0x50 on bus 1
    m = n24c02(bus=1, addr=0x50)

    # erase
    m.write(0, [255]*256)

    # write stuff
    m.write(0, [1,2,3,4,5])
    m.write(0x2E, b"Hello there, Mister Bill!")
    m.write(0x80, str(time.time()))
    m.write(0xFF, 0x5A)

    m.dump()
