""" Driver for TI temperature sensor TMP100/101 """

from i2c import i2c

# convert hi/low registers to -128.0 to +127.9375 C
def r2c(h, l):
    c = h + (l * .00390625)
    if c >= 128: c = -(c-128)
    return c

# convert -128 to +127.9375C to hi/low registers
def c2r(c):
    assert -128 <= c < 128
    c = int(c/.00390625)
    return c / 256, c & 255

class tmp101():
    def __init__(self, bus, addr=0x49):
        self.addr = addr
        self.i2c=i2c(bus, addr)

    def get_temperature(self):                  # return temp in centigrade (float)
        self.i2c.io(0)                          # set pointer register = 0
        h,l=self.i2c.io(None,2)[0]              # read h and l
        return r2c(h,l)                         # return degrees C

    def get_config(self):                       # return configuration byte
        self.i2c.io(1)                          # set pointer register = 1
        return self.i2c.io(None,1)[0][0]        # return config byte

    def set_config(self, config):               # set configuration byte
        self.i2c.io((1,config))                 # write to register 1

    def get_alert_low(self):                    # get low alert temp in centigrade (float)
        self.i2c.io(2)                          # set register pointer = 2
        h,l = self.i2c.io(None,2)[0]            # read h and l
        return r2c(h,l)                         # return degrees C

    def set_alert_low(self, centigrade):        # set low alert temp in centigrade (float)
        h,l = c2r(centigrade)                   # convert to h, l
        self.i2c.io((2,h,l))                    # write to register 2

    def get_alert_high(self):                   # get high alert temp in centigrade (float)
        self.i2c.io(3)                          # set pointer register = 3
        h,l = self.i2c.io(None,2)[0]            # read h and l
        return r2c(h,l)                         # return degrees C

    def set_alert_high(self, centigrade):       # set high alert temp in centigrade (float)
        h,l = c2r(centigrade)                   # convert to h, l
        self.i2c.io((3,h,l))                    # write tio register 3

    # get and set various config flags
    def get_alert(self)         : return bool(self.get_config() & 0x80)
    def set_alert(self,n)       : self.set_config(self.get_config() | (0x80 if n else 0))
    def get_resolution(self)    : return (self.get_config() >> 5) & 3
    def set_resolution(self, n) : self.set_config((self.get_config() & 0x95) | (n << 5))
    def get_faults(self)        : return (self.get_config() >> 3) & 3
    def set_faults(self, n)     : self.set_config((self.get_config() & 0xE7) | ((n & 3) << 3))
    def get_polarity(self)      : return bool(self.get_config() & 4)
    def set_polarity(self, n)   : self.set_config((self.get_config() & 0xFB) | (4 if n else 0))
    def get_mode(self)          : return bool(self.get_config() & 2)
    def set_mode(self, n)       : self.set_config((self.get_config() & 0xFD) | (2 if n else 0))
    def get_shutdown(self)      : return bool(self.get_config() & 1)
    def set_shutdown(self, n)   : self.set_config((self.get_config() & 0xFE) | (1 if n else 0))

if __name__ == "__main__":

    from time import sleep

    # address 0x49 on bus 1
    t = tmp101(1, 0x49)

    # normal mode
    t.set_mode(0)

    # output high on alert
    t.set_polarity(True)

    # un-alert below 27C
    t.set_alert_low(27)

    # alert above 29C
    t.set_alert_high(29)

    print "Alert set at", t.get_alert_high(),", resets at", t.get_alert_low()

    while True:
        if t.get_alert(): print "ALERT!",
        print "Temperature =", t.get_temperature()
        sleep(1)

