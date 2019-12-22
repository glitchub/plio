""" SPI control via /dev/spidev* """

from __future__ import print_function, division
import os, fcntl
from ctypes import *

# This information is from linux/spi/spidev.h

# strucutre is 32 bytes long
class spi_ioc_transfer(Structure):
    _fields_ = [
        ("tx_buf",         c_longlong), # address of userspace transmit data, or 0 to send len zeros
        ("rx_buf",         c_longlong), # address of userspace receive buffer, or 0 to discard receive
        ("len",            c_uint),     # length of tx/rx buffer, in bytes
        ("speed_hz",       c_uint),     # if non-zero, override clock
        ("delay_usecs",    c_ushort),   # if non-zero, usecs to delay after transfer complete (but before cs_change)
        ("bits_per_word",  c_ubyte),    # if non-zero, override bits per word
        ("cs_change",      c_ubyte),    # if non-zero, strobe cycle chip select after transfer complete
        ("tx_nbits",       c_ubyte),    # unused
        ("rx_nbits",       c_ubyte),    # unused
        ("pad",            c_ushort),
    ]

# ioctl definitions

# send N spi_ioc_transfers
def SPI_IOC_MESSAGE(N): return 0x40006B00+((N*sizeof(spi_ioc_transfer))<<16)

SPI_IOC_RD_MODE            = 0x80016B01 # get SPI_MODE (see below)
SPI_IOC_WR_MODE            = 0x40016B01 # set SPI_MODE
SPI_IOC_RD_LSB_FIRST       = 0x80016B02 # return true if sending LSB first
SPI_IOC_WR_LSB_FIRST       = 0x40016B02 # set LSB first
SPI_IOC_RD_BITS_PER_WORD   = 0x80016B03 # return number of bits per word (irrelevant if not LSB first)
SPI_IOC_WR_BITS_PER_WORD   = 0x40016B03 # set number of bits per word
SPI_IOC_RD_MAX_SPEED_HZ    = 0x80046B04 # get current clock speed Hz
SPI_IOC_WR_MAX_SPEED_HZ    = 0x40046B04 # set clock speed Hz

# Values for RD_MODE/WR_MODE (see https://en.wikipedia.org/wiki/Serial_Peripheral_Interface#Clock_polarity_and_phase)
SPI_MODE_0                 = 0x00       # SCL is normally low, data samples on leading (rising) edge
SPI_MODE_1                 = 0x01       # SCL is normally low, data samples on trailing (falling) edge
SPI_MODE_2                 = 0x02       # SCL is normally high, data samples on leading (falling) edge
SPI_MODE_3                 = 0x03       # SCL is normally high, data samples on trailing (rising) edgfe

class spi():
    # Given a bus and chip select number, open SPI device and optionally init
    # various properties via ioctl
    def __init__(self, bus, chipselect, spi_mode=None, lsb_first=None, bits_per_word=None, speed_hz=None):
        self.fd=os.open("/dev/spidev%d.%d" % (bus, chipselect), os.O_RDWR)
        if spi_mode is not None: self.set_spi_mode(spi_mode)
        if lsb_first is not None: self.set_lsb_first(lsb_first)
        if bits_per_word is not None: self.set_bits_per_word(bits_per_word)
        if speed_hz is not None: self.set_speed_hz(speed_hz)

    # Given one or more spi transfer specifications, perform an atomic SPI
    # transaction. Each spec can be:
    #   an int, send that many zeros (in order to read the response)
    #   a list, send the byte values
    #   a dict, key "data" is one of the above, and the rest are optional:
    #       "speed_hz":       # 32 bits, override SPI clock speed
    #       "bits_per_word"   # 8 bits, override bits per word
    #       "delay_usecs"     # 16 bits, delay after transaction
    #       "cs_change"       # 8 bits: if non-zero cycle chip select before next transfer (after delay_usecs)
    # Return a list of lists of response bytes for each specification (caller
    # ignores uninteresting responses)
    def io(self, *specs):
        transfers=[] # list of transfers
        buffers=[]   # transaction buffers
        for s in specs:
            if type(s) == dict:
                data=s["data"]
                # spi_ioc_transfer flags after 'len'
                options=[int(s.get("speed_hz",0)), int(s.get("delay_usecs",0)), int(s.get("bits_per_word",0)), int(s.get("cs_change",0)), 0, 0]
            else:
                data=s
                options=[0, 0, 0, 0, 0, 0]

            if type(data) is int:
                # single byte, just read that many
                size=data
                buffers.append(create_string_buffer(size))
                buffer = addressof(buffers[-1])
                transfers.append(spi_ioc_transfer(0, buffer, size, *options))
            else:
                # send list/tuple/bytes/str/bytearray
                data=self.blist(data)
                size=len(data)
                buffers.append(create_string_buffer(bytes(bytearray(data)), size))
                buffer = addressof(buffers[-1])
                transfers.append(spi_ioc_transfer(buffer, buffer, size, *options))

        t=(spi_ioc_transfer*len(transfers))(*transfers)
        fcntl.ioctl(self.fd, SPI_IOC_MESSAGE(len(t)), t, False)

        # collect the responses
        return [list(bytearray(m.raw)) for m in buffers]

    # return the spi transfer mode 0-3
    def get_spi_mode(self):
        u8 = (c_ubyte*1)(0)
        fcntl.ioctl(self.fd, SPI_IOC_RD_MODE, u8, True)
        return u8[0] & 3

    # set the spi transfer mode 0-3
    def set_spi_mode(self, spi_mode):
        u8 = (c_ubyte*1)(spi_mode & 3)
        fcntl.ioctl(self.fd, SPI_IOC_WR_MODE, u8, False)

    # return true if data is sent LSB first
    def get_lsb_first(self):
        u8 = (c_ubyte*1)(0)
        fcntl.ioctl(self.fd, SPI_IOC_RD_LSB_FIRST, u8, True)
        return bool(u8[0])

    # enable LSB first or MSB first
    def set_lsb_first(self, lsb_first):
        u8 = (c_ubyte*1)(1 if lsb_first else 0)
        fcntl.ioctl(self.fd, SPI_IOC_WR_LSB_FIRST, u8, False)

    # get number of bits per word
    def get_bits_per_word(self):
        u8 = (c_ubyte*1)(0)
        fcntl.ioctl(self.fd, SPI_IOC_RD_BITS_PER_WORD, u8, True)
        return u8[0] or 8

    # set number of bits per word
    def set_bits_per_word(self, bits_per_word):
        u8 = (c_ubyte*1)(bits_per_word)
        fcntl.ioctl(self.fd, SPI_IOC_WR_BITS_PER_WORD, u8, False)

    # get clock speed
    def get_speed_hz(self):
        u32 = (c_uint*1)(0)
        fcntl.ioctl(self.fd, SPI_IOC_RD_MAX_SPEED_HZ, u32, True)
        return u32[0]

    # set clock speed
    def set_speed_hz(self, speed_hz):
        u32 = (c_uint*1)(speed_hz)
        fcntl.ioctl(self.fd, SPI_IOC_WR_MAX_SPEED_HZ, u32, False)

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

    # open gizmo on spidev0.0, clock at 125KHz
    gizmo=spi(0, 0, spi_mode=SPI_MODE_1, bits_per_word=8, lsb_first=False, speed_hz=125000)

    print("spi_mode      =",gizmo.get_spi_mode())
    print("lsb_first     =",gizmo.get_lsb_first())
    print("bits_per_word =",gizmo.get_bits_per_word())
    print("speed_hz      =",gizmo.get_speed_hz())
    print("Sending packets...")

    while True:
        # Send 3 bytes and delay 1 mS
        # Send 3 zeros at 250KHz and strobe cs
        # Send 3 more bytes
        print(gizmo.io({"data":[0xFF]*3, "delay_usecs":1000}, {"data":3, "speed_hz":250000, "cs_change":True}, [0xF0, 0x55, 0x81]))
        sleep(.1)
