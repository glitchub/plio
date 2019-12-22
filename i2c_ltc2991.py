# Driver for Linear LTC2991 E/I/T monitor
# Supports single-ended, differential and temperature reads from all inputs

from __future__ import print_function, division
from i2c import i2c

class ltc2991():

    # Registers of interest
    TRIGGER     = 0x01
    V1234CTL    = 0x06
    V5678CTL    = 0x07
    CTL         = 0x08
    V1_T1       = 0x0A # single-ended V1 or temp 1
    V2_D1       = 0x0C # single-ended V2 or differential V1-V2
    V3_T2       = 0x0E # single-ended V3 or temp 2
    V4_D2       = 0x10 # single-ended V4 or differential V3-V4
    V5_T3       = 0x12 # single-ended V5 or temp 3
    V6_D3       = 0x14 # single-ended V6 or differential V5-V6
    V7_T4       = 0x16 # single-ended V7 or temp 4
    V8_D4       = 0x18 # single-ended V8 or diffential V7-V8
    TEMP        = 0x1A # internal temp (aka temp 0)
    VCC         = 0x1C # VCC (aka single-ended V0)

    def __init__(self, bus, addr=0x48):
        self.addr = addr
        self.i2c = i2c(bus=bus, addr=addr)
        self.cache = None   # cached control registers

    # set control registers with three specified values
    # they are cached so only update if needed
    def _control(self, v1234ctl, v5678ctl, ctl):
        # cache three control registers
        if self.cache is None:
            self.cache = self.i2c.io(self.V1234CTL, 3)
        controls = [v1234ctl, v5678ctl, ctl]
        if controls != self.cache:
            self.cache = controls
            self.i2c.io([self.V1234CTL]+controls)

    # Trigger channel 0-4 and spin until conversion complete. Channel 0 is
    # internal.
    def _trigger(self, channel):
        assert 0 <= channel <= 4
        self.i2c.io([self.TRIGGER, 1<<(channel+3)])
        while self.i2c.io(self.TRIGGER, 1)[0][0] & 4: pass

    # Convert 2-byte sample registers, and uV per step, return voltage.
    @staticmethod
    def _uV(hi, lo, uV):
        n = ((hi << 8) | lo) & 0x3fff           # actual value in low 14 bits
        if hi & 0x40: n = -1-(n ^ 0x3fff)       # but invert if signed
        return n * (uV / 100000)                # return microvolts

    # Return celsius of temperature input 0 through 4, where 0 is internal temperature, 1 is T1, etc.
    # eta is the sensor diode ideality factor, if None then just use chip's default (1.004)
    def temperature(self, input, eta=None):
        assert 0 <= input <= 4
        self._control(0x66, 0x66, 0x04)         # set controls for kelvin
        self._trigger(input)                    # trigger requested channel
        rreg = [self.TEMP, self.V1_T1, self.V3_T2, self.V5_T3, self.V7_T4][input]
        hi, lo = self.i2c.io(rreg, 2)[0]        # get two byte result
        v = ((hi << 8) + lo) & 0x1fff
        kelvin = v / 16
        if eta is not None: kelvin *= (1.004 / eta)
        return kelvin - 273.15                  # return celsius

    # Return voltage on single-ended input 0 through 8, where 0 is internal VCC, 1 is V1, etc
    def voltage(self, input):
        assert 0 <= input <= 8
        self._control(0x00, 0x00, 0x00)         # set controls for single-ended
        self._trigger(input+1//2)               # trigger 0->0, 1|2->1, 3|4->2, 5|6->3, 7|8->4
        rreg = [self.VCC, self.V1_T1, self.V2_D1, self.V3_T2, self.V4_D2, self.V5_T3, self.V6_D3, self.V7_T4, self.V8_D4][input]
        hi, lo = self.i2c.io(rreg, 2)[0]        # get two-byte result
        return self._uV(hi, lo, 305.18)         # 305.18 uV per step

    # Get voltage on differential input 1 through 4
    # 1 is V2-V1, 2 is V4-V3, etc.
    def differential(self, input):
        assert 1 <= input <= 4
        self._control(0x11, 0x11, 0x00)         # set controls for differential
        self._trigger(input)                    # trigger the requested channel
        rreg = [self.V2_D1, self.V4_D2, self.V6_D3, self.V8_D4][input-1]
        hi, lo = self.i2c.io(rreg, 2)[0]        # get two byte result
        return self._uV(hi, lo, 19.075)         # 19.075 uV per step

if __name__ == "__main__":
    chip = ltc2991(bus=1, addr=0x48)
    print("Ambient = %fC" % chip.temperature(0))
    print("VCC = %fV" % (chip.voltage(0)*2,))
