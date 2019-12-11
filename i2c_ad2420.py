# Driver for Analog Devices AD2420 A2B Transciever
# At this time just provides basic linkages to master, slave, and peripheral i2c interfaces.

from i2c import i2c

class ad2420():

    # registers
    CHIP            = 0x00
    NODEADR         = 0x01
    VENDOR          = 0x02
    PRODUCT         = 0x03
    VERSION         = 0x04
    CAPABILITY      = 0x05
    SWCTL           = 0x09
    BCDNSLOTS       = 0x0A
    LDNSLOTS        = 0x0B
    LUPSLOTS        = 0x0C
    DNSLOTS         = 0x0D
    UPSLOTS         = 0x0E
    RESPCYCS        = 0x0F
    SLOTFMT         = 0x10
    DATCTL          = 0x11
    CONTROL         = 0x12
    DISCVRY         = 0x13
    SWSTAT          = 0x14
    INTSTAT         = 0x15
    INTSRC          = 0x16
    INTTYPE         = 0x17
    INTPND0         = 0x18
    INTPND1         = 0x19
    INTPND2         = 0x1A
    INTMSK0         = 0x1B
    INTMSK1         = 0x1C
    INTMSK2         = 0x1D
    BECCTL          = 0x1E
    BECNT           = 0x1F
    TESTMODE        = 0x20
    ERRCNT0         = 0x21
    ERRCNT1         = 0x22
    ERRCNT2         = 0x23
    ERRCNT3         = 0x24
    NODE            = 0x29
    DISCSTAT        = 0x2B
    TXACTL          = 0x2E
    TXBCTL          = 0x30
    LINTTYPE        = 0x3E
    I2CCFG          = 0x3F
    PLLCTL          = 0x40
    I2SGCFG         = 0x41
    I2SCFG          = 0x42
    I2SRATE         = 0x43
    I2STXOFFSET     = 0x44
    I2SRXOFFSET     = 0x45
    SYNCOFFSET      = 0x46
    PDMCTL          = 0x47
    ERRMGMT         = 0x48
    GPIODAT         = 0x4A
    GPIODATSET      = 0x4B
    GPIODATCLR      = 0x4C
    GPIOOEN         = 0x4D
    GPIOIEN         = 0x4E
    GPIOIN          = 0x4F
    PINTEN          = 0x50
    PINTINV         = 0x51
    PINCFG          = 0x52
    I2STEST         = 0x53
    RAISE           = 0x54
    GENERR          = 0x55
    I2SRATE         = 0x56
    I2SRRCTL        = 0x57
    I2SRRSOFFS      = 0x58
    CLK1CFG         = 0x59
    CLK2CFG         = 0x5A
    BMMCFG          = 0x5B
    SUSCFG          = 0x5C
    PDMCTL2         = 0x5D
    UPMASK0         = 0x60
    UPMASK1         = 0x61
    UPMASK2         = 0x62
    UPMASK3         = 0x63
    UPOFFSET        = 0x64
    DNMASK0         = 0x65
    DNMASK1         = 0x66
    DNMASK2         = 0x67
    DNMASK3         = 0x68
    DNOFFSET        = 0x69
    CHIPID0         = 0x6A
    CHIPID1         = 0x6B
    CHIPID2         = 0x6C
    CHIPID3         = 0x6D
    CHIPID4         = 0x6E
    CHIPID5         = 0x6F
    GPIODEN         = 0x80
    GPIOD0MSK       = 0x81
    GPIOD1MSK       = 0x82
    GPIOD2MSK       = 0x83
    GPIOD3MSK       = 0x84
    GPIOD4MSK       = 0x85
    GPIOD5MSK       = 0x86
    GPIOD6MSK       = 0x87
    GPIOD7MSK       = 0x88
    GPIODDAT        = 0x89
    GPIODINV        = 0x8A
    MBOX0CTL        = 0x90
    MBOX0STAT       = 0x91
    MBOX0B0         = 0x92
    MBOX0B1         = 0x93
    MBOX0B2         = 0x94
    MBOX0B3         = 0x95
    MBOX1CTL        = 0x96
    MBOX1STAT       = 0x97
    MBOX1B0         = 0x98
    MBOX1B1         = 0x99
    MBOX1B2         = 0x9A
    MBOX1B3         = 0x9B

    def __init__(self, bus, addr=0x68):
        self.i2cbase = i2c(bus, addr)                   # The base address is for talking to master
        self.i2cbus = i2c(bus, addr+1)                  # The bus address is for talking to selected slave, via the master

    # Perform I2C transaction(s) with the master device
    def master_io(self, *specs):
        return self.i2cbase.io(*specs)                  # deliver to the base address

    # Perform I2C transactions with slave device
    def slave_io(self, slave, *specs):
        assert(slave <= 15)
        self.master_io([self.NODEADR, slave])           # first set the master's node address
        return self.i2cbus.io(*specs)                   # then deliver to the bus interface

    # Perform I2C transactions with a slave's peripheral device
    def peripheral_io(self, slave, peripheral, *specs):
        assert(peripheral <= 127)
        self.slave_io(slave, [self.CHIP, peripheral])   # set the slave's chip address
        self.master_io([self.NODEADR, slave | 0x20])    # then set the master's PERI bit
        return self.i2cbus.io(*specs)                   # deliver to the bus interface

if __name__ == "__main__":
    chip = ad2420(bus=1, addr=0x6A)
    vendor, product, version = chip.master_io(ad2420.VENDOR,3)[0]
    chipid = chip.master_io(ad2420.CHIPID0,6)[0]
    print "AD24%02X, vendor 0x%2X, version 0x%2X, id %s" % (product, vendor, version, ''.join("%02X" % b for b in chipid))
    chip.master_io([ad2420.GPIOOEN,2])                  # set gpio01 low
    chip.master_io([ad2420.GPIODATCLR, 2])
