# Python access to gpios via /sys/class/gpio*.

# This is an order of magnitude slower than gpio.py but state is retained after
# program exit.

import os, re

base="/sys/class/gpio"
assert os.path.isdir(base)

# given a gpiochip index, name, or label, return the appropriate "gpiochipXXX" from the base directory.
def gpiochip(chip):

    gpiochips=filter(lambda p : os.path.isfile(base+"/%s/base" % p), os.listdir(base))
    assert gpiochips
    # if 'chip' is listed, then use as is
    if chip in gpiochips: return chip
    try:
        # if 'chip' is an int, then ise as a list index
        chip=int(chip)
        if len(gpiochips) <= chip: raise Exception("No gpiochip index '%d'" % chip)
        def _int(s):
            try: return int(s)
            except: return s
        # sort numerically, i.e. gpiochip11 is before chipchip101
        return sorted(gpiochips, key=lambda p:map(_int,re.split('(\d)+',p)))[chip]
    except ValueError:
        # here, maybe 'chip' is a label
        for g in gpiochips:
            with open(base+"/%s/label" % g) as f:
                if f.readline().strip() == chip: return g
        raise Exception("No gpiochip label '%s'" % chip);

class gpio():
    # Open and manipulate gpio "line" of chip "chip". Options are:
    #   output     : True=gpio is an output, False=gpio is an input, None=use current configuration (default False)
    #   invert     : True=gpio is inverted, False=gpio not inverted, None=use current inversion (default False)
    #   state      : True=set output high, False=set output low, None=retain current output (default False)
    #   persistent : True=leave gpio configured on object delete, False=unconfigure gpio on object delete (default True)
    # "chip" is a numeric index, a name "gpiochipxxx", or a label.
    # The line number is always 0-based and will be offset to the base of the specified chip.
    def __init__(self, line, chip=0, invert=False, output=False, state=False, persistent=True):
        # find the specified gpiochip
        self.gpiochip=gpiochip(chip)
        # offset the specified line by the gpiochip base
        with open(base+"/%s/base" % self.gpiochip) as f: self.line=int(line)+int(f.readline())
        self.base = base+"/gpio%d" % self.line
        if not os.path.isdir(self.base):
            with open(base+"/export","w") as f: f.write("%d\n" % self.line)
        with open(self.base+"/direction") as f: self.output = f.readline().strip() == 'out'
        with open(self.base+"/active_low") as f: self.invert = bool(int(f.readline()))
        with open(self.base+"/value") as f: self.state=bool(int(f.readline()))
        self.persistent=persistent
        self.configure(invert = invert, output = output, state = state)

    # destructor, unexport if not persistent
    def __del__(self):
        try:
            if not self.persistent:
                with open(base+"/unexport","w") as f:
                    f.write("%d\n" % self.line)
        except: pass

    # Configure gpio, config options as above but if not specified then are not changed
    def configure(self, invert=None, output=None, state=None):
        if invert is not None and invert != self.invert:
            self.invert = bool(invert)
            with open(self.base+"/active_low","w") as f: f.write("%d\n" % (1 if self.invert else 0))
        if output is not None and output != self.output:
            self.output = bool(output)
            with open(self.base+"/direction","w") as f: f.write("%s\n" % ("out" if self.output else "in"))
        if self.output:
            if state is not None and state != self.state:
                self.state = bool(state)
                with open(self.base+"/value","w") as f: f.write("%d\n" % (1 if self.state else 0))
        else:
            with open(self.base+"/value") as f: self.state=bool(int(f.readline()))

    # change gpio to an output and set high or low
    def set_output(self, state):
        self.configure(output=True, state=state)

    # change gpio to an input and return current state
    def get_input(self):
        self.configure(output=False)
        return self.state

    # show gpio configuration
    def show(self, label=None):
        if label: print label,
        print "%s %d: output=%s state=%s invert=%s" % (self.gpiochip, self.line, self.output, self.state, self.invert)

if __name__ == "__main__":

    # Demo for Raspberry Pi 3B

    gpio5=gpio(5, output=True, persistent=False) # aka header pin 29
    gpio5.show()

    gpio6=gpio(6, output=True, persistent=False) # aka header pin 31
    gpio6.show()

    gpio7=gpio(7, invert=True, persistent=False) # aka header pin 26, note input floats high until grounded
    gpio7.show()

    # Sequence gpios 5 and 6 until gpio7 is grounded
    while not gpio7.get_input():
        for n in range(0,4):
            gpio5.set_output(n & 1)
            gpio6.set_output(n & 2)

    # Toggle gpio5 as fast as possible
    while True:
        gpio5.set_output(not gpio5.state)
