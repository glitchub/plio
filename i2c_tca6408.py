# Driver for TI TCA6408 GPIO expander

from i2c import i2c
from time import sleep

class tca6408():

    # There are 4 eight-bit registers
    IN  = 0 # 1 = logical input states
    OUT = 1 # 1 = buffered output states
    INV = 2 # 1 = invert the pin's physical state
    DIR = 3 # aka configuration register, 1 = output

    def __init__(self, bus, addr=0x20):
        self.addr = addr
        self.i2c = i2c(bus, addr)
        self.cache = {}

    # Set or clear masked bits in specified register to specified value
    # Values are cached, use only for config registers
    def config(self, reg, mask, value):
        assert 1 <= reg <= 3 and 1 <= mask <= 0xff
        if reg not in self.cache: self.cache[reg] = self.i2c.io(reg,1)[0][0]
        r = (self.cache[reg] & ~mask) | (value & mask)
        if r != self.cache[reg]:
            self.cache[reg]=r
            self.i2c.io([reg, r])

    # change masked gpios to inputs and return set bits.
    # If invert flag is not None, update the inversion register.
    def get_mask(self, mask):
        self.config(self.DIR, mask, mask) # change to inputs
        return self.i2c.io([self.IN, 1])[0][0] & mask

    # change masked gpios to outputs and drive them to specified state.
    def set_mask(self, mask, state):
        self.config(self.DIR, mask, 0) # change to outputs
        self.config(self.OUT, mask, mask if state else 0)

    # Change specified gpio 0-7 to a input and return its state.
    def get_gpio(self, gpio):
        assert 0 <= gpio <= 7
        return bool(self.get_mask(1 << gpio))

    # Change specified gpio 0-7 to an output and set its state.
    def set_gpio(self, gpio, state):
        assert 0 <= gpio <= 7
        self.set_mask(1 << gpio, state)

    # Reset to non-inverted inputs
    def reset(self):
        self.get_mask(0xFF)

if __name__ == "__main__":
    chip = tca6408(0x21)

    # get all gpios in parallel
    print "Input state = 0x02X" % chip.get_mask(0xFF)

    # get them one at a time
    for i in range(0,8):
        print "gpio %d = %r" % (i, chip.get_gpio(i))
