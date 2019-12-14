# Driver for TI TMP100/101 temperature sensor

from i2c import i2c


class tmp101():

    # four registers
    TEMP    = 0
    CONFIG  = 1
    LOW     = 2
    HIGH    = 3

    def __init__(self, bus, addr=0x49):
        self.addr = addr
        self.i2c=i2c(bus, addr)

    # convert hi/low registers to -128.0 to +127.9375 C
    @staticmethod
    def __hl2c(hl):
        c = hl[0] + ((hl[1] >> 4) * 0.0625)
        if c >= 128: c = -(256-c)
        return c

    # convert -128 to +127.9375C to hi/low registers
    @staticmethod
    def __c2hl(c):
        assert -128 <= c < 128
        if c < 0: c = 256+c
        c = int(c/.0625)
        return [c >> 4, (c & 15) << 4]

    # return temp as centigrade (float)
    def get_temperature(self):
        self.i2c.io(self.TEMP)                                  # set pointer register = 0
        return self.__hl2c(self.i2c.io(None,2)[0])              # return 2 bytes as centigrade

    # return configuration byte (and alert status)
    def get_config(self):
        self.i2c.io(self.CONFIG)                                # set register pointer
        return self.i2c.io(None,1)[0][0]                        # return one byte

    # set masked configuration bits
    def set_config(self, mask, value):
        o = self.get_config()                                   # get current
        n = (o & ~mask) | (value & mask)                        # alter as required
        if (n != o):                                            # if actually changed
            self.i2c.io([self.CONFIG, n])                       # update register

    # get high or low alert temp in centigrade (float)
    def get_alert(self, reg):
        assert reg == self.HIGH or reg == self.LOW
        self.i2c.io(reg)                                        # set register pointer
        return self.__hl2c(self.i2c.io(None,2)[0])              # return two bytes as centigrade

    # set high or low low alert temp in centigrade (float)
    def set_alert(self, reg, centigrade):
        assert reg == self.HIGH or reg == self.LOW
        self.i2c.io([reg]+self.__c2hl(centigrade))              # update register with two bytes

    # get alert status, or trigger oneshot in shutdown
    def get_osalert(self)       : return bool(self.get_config() & 0x80)
    def set_osalert(self,n)     : (self.set_config(0x80, 0x80 if n else 0))

    # set temperature resolution, affects the conversion time
    def get_resolution(self)    : return (self.get_config() >> 5) & 3
    def set_resolution(self, n) : self.set_config(0x60, n << 5)

    # get number of siccessive faults before alert (aka debounce)
    def get_faults(self)        : return (self.get_config() >> 3) & 3
    def set_faults(self, n)     : self.set_config(0x18, n << 3)

    def get_polarity(self)      : return bool(self.get_config() & 0x04)
    def set_polarity(self, n)   : self.set_config(0x04, 0x04 if n else 0)

    def get_mode(self)          : return bool(self.get_config() & 0x02)
    def set_mode(self, n)       : self.set_config(0x02, 0x02 if n else 0)

    def get_shutdown(self)      : return bool(self.get_config() & 0x01)
    def set_shutdown(self, n)   : self.set_config(0x01, 0x01 if n else 0)

if __name__ == "__main__":

    from time import sleep

    # address 0x49 on bus 1
    t = tmp101(1, 0x49)

    # reset config to normal thermostat mode
    t.set_config(0xFF,0)

    # output high on alert
    t.set_polarity(True)

    # .0625 degree resolution == 320mS conversion time
    t.set_resolution(3)

    # 4 faults before alert
    t.set_faults(2)

    # un-alert below 27C
    t.set_alert(t.LOW, 27)

    # alert above 28.5C
    t.set_alert(t.HIGH, 28.5)

    print "Alert set at %gC, resets at %gC" % (t.get_alert(t.HIGH), t.get_alert(t.LOW))

    while True:
        if t.get_osalert(): print "ALERT!",
        print "Temperature = %gC" % t.get_temperature()
        sleep(1)

