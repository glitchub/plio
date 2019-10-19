""" Driver for ON N24C02 256 byte serial EEPROM """

from i2c import i2c
from time import time

class n24c02():
    def __init__(self, bus, addr=0xa0):
        self.addr = addr
        self.i2c = i2c(bus,addr)

    # read len bytes from offset
    def read(self, offset, len=1):
        # avoid wrapping
        assert offset >= 0 and len >= 1 and offset+len <= 256

        start=time()
        while True:
            try:
                return self.i2c.io(offset,len)[0]
            except IOError as e:
                # chip may be busy, give it .5 seconds
                if time()-start < .5: continue
                raise e

    # write data list to offset
    def write(self, offset, data):
        # avoid wrapping
        assert offset >= 0 and len(data) >= 1 and offset + len(data) <= 256

        # write 16-byte chunks
        for p in range(0,data,16):
            start=time()
            while True:
                try:
                    # up to 17 bytes total
                    self.i2c.io([offset]+data[p:p+16])
                except IOError as e:
                    # chip may be busy, give it .5 seconds
                    if time()-start < .5: continue
                    raise e
                offset += 16

if __name__ == "__main__":

    # device address 0x50 on bus 1
    m = n24c02(1,0x50)

    # dump 256 bytes
    print m.read(0,256)
