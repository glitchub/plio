# Python access to gpios via /sys/class/gpio*.

# This is an order of magnitude slower than gpio.py but state is retained after
# program exit.

import os

base="/sys/class/gpio"
assert os.path.isdir(base)

# Open and manipulate gpio "line". Options are:
#   output     : True=gpio is an output, False=gpio is an input, None=use current configuration (or default to input)
#   invert     : True=gpio is inverted, False=gpio not inverted, None=use current inversion (or default to uninverted)
#   state      : True=set output high, False=set output low, None=retain current output (ignored if not output)
# Default for all is FALSE, you must explicity set None to retain the existing state
class gpio():
    def __init__(self, line, invert=False, output=False, state=False):
        self.line = line
        self.base = base+"/gpio%d" % line
        if not os.path.isdir(self.base):
            with open(base+"/export","w") as f: f.write("%d\n" % line)
        with open(self.base+"/direction") as f: self.output = f.readline().strip() == 'out'
        with open(self.base+"/active_low") as f: self.invert = bool(int(f.readline()))
        with open(self.base+"/value") as f: self.state=bool(int(f.readline()))
        self.configure(invert = invert, output = output, state = state)

    # Configure gpio, config options as above but if not specified then are not changed
    def configure(self, invert=None, output=None, state=None):
        if invert is not None and invert != self.invert:
            self.invert=invert
            with open(self.base+"/active_low","w") as f: f.write("%d\n" % (1 if self.invert else 0))
        if output is not None and output != self.output:
            self.output=output
            with open(self.base+"/direction","w") as f: f.write("%s\n" % ("out" if self.output else "in"))
        if self.output:
            if state is not None and state != self.state:
                self.state = state
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
        print "gpio %d: output=%s state=%s invert=%s" % (self.line, self.output, self.state, self.invert)

    # Release the gpio from sysfs, it will revert to default kernel state
    # The gpio instance should then be deleted.
    def release(self):
        with open(base+"/unexport","w") as f: f.write("%d\n" % self.line)
        # invalidate this instance
        del self.base
        del self.line

if __name__ == "__main__":

    # Demo for Raspberry Pi 3B

    gpio5=gpio(5, output=True)      # aka header pin 29
    gpio5.show()

    gpio6=gpio(6, output=True)      # aka header pin 31
    gpio6.show()

    gpio7=gpio(7, invert=True)      # aka header pin 26, note input floats high until grounded
    gpio7.show()

    try:

        # Sequence gpios 5 and 6 until gpio7 is grounded
        while not gpio7.get_input():
            for n in range(0,4):
                gpio5.set_output(n & 1)
                gpio6.set_output(n & 2)

        # Toggle gpio5 as fast as possible
        while True:
            gpio5.set_output(not gpio5.state)

    except:

        # Persistent GPIOs in the feature of this module.  But for this demo we
        # don't want them to persist.
        gpio5.release()
        gpio6.release()
        gpio7.release()

