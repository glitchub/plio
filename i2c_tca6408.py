# Driver for TI TCA6408 GPIO expander

from __future__ import print_function

try: from i2c import i2c
except: from .i2c import i2c

class tca6408:

    # Registers have one bit per pin
    IN  = 0     # 1 = input pin is logic high
    OUT = 1     # 1 = output pin is logic high
    INV = 2     # 1 = pin logical state is inverse of physicall
    DIR = 3     # 1 = pin is input

    # Create a tca6408 object with given bus and slave address
    def __init__(self, bus, addr=0x20):
        self.addr = addr
        self.i2c = i2c(bus=bus, addr=addr)
        self.cache = {}

    # Set or clear masked bits in specified register to specified value
    # Values are cached!
    def _register(self, reg, mask, value):
        assert 1 <= reg <= 3 and 1 <= mask <= 0xff
        if reg not in self.cache: self.cache[reg] = self.i2c.io(reg,1)[0][0]
        r = (self.cache[reg] & ~mask) | (value & mask)
        if r != self.cache[reg]:
            self.cache[reg] = r
            self.i2c.io([reg, r])

    # change masked gpios to inputs and return their states
    def input(self, mask):
        self._register(self.DIR, mask, mask)           # change to inputs
        return self.i2c.io([self.IN, 1])[0][0] & mask   # return masked states

    # change masked gpios to outputs and set them to specified state.
    def output(self, mask, states):
        self._register(self.DIR, mask, 0)              # change to outputs
        self._register(self.OUT, mask, states)         # set masked states

    # set inversion for masked gpios (whether input or output)
    def invert(self, mask, states):
        self._register(self.INV, mask, states)         # set inversion states

    # reset to HI-Z, disable inversion
    def reset(self):
        self.input(0xFF)
        self.invert(0xFF, 0x00)

    # class for a single gpio
    class _gpio:
        def __init__(self, parent, gpio):
            assert 0 <= gpio <= 7
            self.gpio = 1 << gpio
            self.parent = parent
        def output(self, state): self.parent.output(self.gpio, 0xFF if state else 0)   # Change the gpio to output and set its state
        def input(self): return bool(self.parent.input(self.gpio))                     # Change the gpio to input and return its state
        def invert(self, state): self.parent.invert(self.gpio, 0xFF if state else 0)   # Set the gpio inversion

    # return a _gpio for specified gpio number 0-7
    def gpio(self, gpio): return self._gpio(self, gpio)

if __name__ == "__main__":
    chip = tca6408(bus=1, addr=0x21)
    chip.reset()

    # show current input states
    print("Inputs = 0x02X" % chip.input(0xFF))

    # fiddle with discrete gpios
    g0=chip.gpio(0)             # g0 is pin 0
    g1=chip.gpio(1)             # g1 is pin 1
    g2=chip.gpio(2)             # g2 is pin 2

    g0.output(0)                # set g0
    g1.invert(1)                # invert g1
    g1.output(1)                # clear g1, which actually sets it
    print("g2 is ",g2.input())  # report g2
