# Driver for Linear LTC2945 Wide Range Power Monitor. Supports snapshot mode
# only!

# I2C address is based on ADR1 and AR0 pins:
#   ADR1  ADR0 =  address
#    H     L   =  67
#    NC    L   =  68
#    H     H   =  69
#    NC    NC  =  6A
#    NC    L   =  6B
#    L     H   =  6C
#    H     NC  =  6D
#    L     NC  =  6E
#    L     L   =  6F

from __future__ import print_function, division
from i2c import i2c

class ltc2945():

    # Registers of interest
    CONTROL     = 0x00
    SENSE_MSB   = 0x14
    SENSE_MSB   = 0x15
    VIN_MSB     = 0x1E
    VIN_LSB     = 0x1F
    ADIN_MSB    = 0x28
    ADIN_LSB    = 0x29

    def __init__(self, bus, addr=0x6A):
        self.addr = addr
        self.i2c = i2c(bus,addr)

    # Trigger conversion from specified source 0=delta SENSE, 1=SENSE+, 2=VDD,
    # 3=ADIN, wait for it to complete, then return 12-bit result
    def convert(self, source, result):
        # Control bits:
        #   0x80 ; 1 = snapshot mode, always set
        #   0x40 : 0 = input from delta SENSE or VIN, 1 input from ADIN
        #   0x20 : 0 = input from delta SENSE or ADIN, 1 inputs from Vin
        #   0x04 : 0 = Vin from VDD, 1 = Vin from SENSE+
        self.i2c.io([self.CONTROL, [0x80, 0xA4, 0xA0, 0xC0][source]])
        while self.i2c.io(0,1)[0][0] & 4: pass  # spin until conversion complete
        msb, lsb =self.i2c.io(result,2)[0]      # read result registers
        return msb << 4 | lsb >> 4              # 12 bits

    # Measure delta SENSE voltage 0 - 102.375mV aka 25 uV per step. Then derive
    # current assuming nominal 0.02 resistor for range 0 - 5.12 amps.
    def i_sense(self, ohms=.02):
        v = self.convert(0, self.SENSE_MSB) * 0.000025
        return v / ohms

    # Return SENSE+ voltage, 0 to 102.375V volts, aka 25mV per step
    def v_sense(self):
        return self.convert(1, self.VIN_MSB) * 0.025

    # Return VDD voltage, 0 to 102.375V aka 25mV per step
    def v_vdd(self):
        return self.convert(2, self.VIN_MSB) * 0.025

    # return ADIN voltage 0 to 2.0475V aka .5 mV per step
    def v_adin(self):
        return self.convert(3, self.ADIN_MSB) * 0.0005

if __name__ == "__main__":
    chip = ltc2945(1, 0x69)
    print("Input %g volts, %g amps" % (chip.v_sense(), chip.i_sense()))
