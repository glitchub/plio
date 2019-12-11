# Driver for MAX 6639 fan controller

# In normal operation:
#   reset() possibly with options
#   set_fan_ config() for each fan
#   set_pwm_mode() or set_rpm_mode() for each fan.

from i2c import i2c

class max6639():

    # registers, some may accept channel or fan index 1 or 2
    def TEMP(self ,n)       : return (0x00, 0x01)[n-1]
    STATUS                  = 2
    MASK                    = 3
    CONFIG                  = 4
    def XTEMP(self ,n)      : return (0x05, 0x06)[n-1]
    def ALERT(self ,n)      : return (0x08, 0x09)[n-1]
    def OLIMIT(self ,n)     : return (0x0A, 0x0B)[n-1]
    def TLIMIT(self ,n)     : return (0x0C, 0x0D)[n-1]
    def CONFIG1(self ,n)    : return (0x10, 0x14)[n-1]
    def CONFIG2A(self ,n)   : return (0x11, 0x15)[n-1]
    def CONFIG2B(self ,n)   : return (0x12, 0x16)[n-1]
    def CONFIG3(self ,n)    : return (0x13, 0x17)[n-1]
    def TACH(self ,n)       : return (0x20, 0x21)[n-1]
    def START_TACH(self ,n) : return (0x22, 0x23)[n-1]
    def PPR(self ,n)        : return (0x24, 0x25)[n-1]
    def DUTY(self ,n)       : return (0x26, 0x27)[n-1]
    def START_TEMP(self ,n) : return (0x28, 0x29)[n-1]
    ID                      = 0x3D
    MANUFACTURER            = 0x3E
    REVISION                = 0x3F

    def __init__(self, bus, addr=0x58):
        self.addr = addr
        self.i2c = i2c(bus, addr)
        self.cache = {}

    # update register with mask and value, and cache it
    def register(self, reg, mask, value):
        if reg not in self.cache: self.cache[reg] = self.i2c.io(reg,1)[0][0]
        v = (self.cache[reg] & ~mask) | value
        if v != self.cache[reg]:
            self.cache[reg] = v
            self.i2c.io([reg, v])

    # reset the device, possibly enable standby, smb timeout, chip temp for channel 2, and hi frequency PWM
    def reset(self, standby=False, smbto=False, local=False, pwmhi=False):
        self.i2c.io([0x04, 0x40]) # force reset bit
        r=0
        if standby:   r |= 0x80
        if not smbto: r |= 0x20
        if local:     r |= 0x10
        if pwmhi:     r |= 0x08
        self.i2c.io([0x04,r])
        self.cache = {}

    # Given fan index 1 or 2, set pwm frequency 0-3 (table 9), polarity, rate
    # of change 0-7 (table 5), spinup if fan should start at 100%.
    # Use this after reset, only if non-defaults are required.
    def set_fan_config(self, fan, freq=1, polarity=False, roc=0, spinup=True):
        assert 0 <= freq <= 3
        assert 0 <= roc <= 7
        self.register(self.CONFIG1(fan), 0x70, roc << 4)
        self.register(self.CONFIG2A(fan), 0x02, 0x02 if polarity else 0x00)
        self.register(self.CONFIG3(fan), 0x83, freq | (0x00 if spinup else 0x80))

    # Set fan 1 or 2 into pwm mode.
    # duty is the pwm duty cycle, 0 to 100%
    def set_pwm_mode(self, fan, duty):
        assert 0 <= duty <= 100
        self.register(self.CONFIG1(fan), 0x80, 0x80)    # set PWM mode
        width=int(round(duty*1.2))                      # convert percent to 120ths
        self.i2c.io([self.DUTY(fan), width])            # set PWM width, DO NOT CACHE

    # Set fan 1 or 2 into RPM mode.
    # rpm        = base RPM, 500 to 16000.
    # ppr        = fan tach pulses per revolution, 1 to 4. Default 2.
    # target     = temperature (of corresponding channel) to maintain, 1 to 255C. Default None, operate in manual mode.
    # continuous = If true, fan does not stop if temp falls below target. Default False.
    def set_rpm_mode(self, fan, rpm, ppr=2, target=None, continuous=False):
        assert 500 <= rpm <= 16000
        assert 1 <= ppr <= 4
        if target: assert 1 <= target <= 255

        # Set tach clock frequency 0 to 3 and maxrpm
        self.clock=0
        if rpm <= 1500: self.clock = 0                  # max 2000 rpm
        elif rpm <= 3000: self.clock = 1                # max 4000 rpm
        elif rpm < 6000: self.clock = 2                 # max 8000 rpm
        else: self.clock = 3                            # max 16000 rpm

        # enable rpm mode
        self.register(self.START_TACH(fan), 0xFF, (60000<<self.clock)/rpm)          # set start speed
        self.register(self.PPR(fan), 0xFF, ppr<<6 + 0x1E)                           # ppr and min tach
        if target:
            self.register(self.CONFIG1(fan), 0x8F, [8,4][fan-1] | self.clock)       # fan monitors temp1, fan2 monitors temp 2
            self.register(self.START_TEMP(fan), 0xFF, target)                       # set start temperature
            self.register(self.CONFIG2A(fan), 0x01, 0x01 if continuous else 0x00)   # maybe set continuous run flag
        else:
            self.register(self.CONFIG1(fan), 0x8F, self.clock)                      # run without monitor
            self.register(self.CONFIG2A(fan), 0x01, 0x01)                           # continuous

    # Return temp 0 to 255.875 degrees C from indexed channel 1 or 2, or return
    # -1 if diode fault.
    def get_temp(self, channel):
        l = self.i2c.io(self.XTEMP(channel),1)[0][0]    # read low first from reg 5 or 6
        if l & 1: return -1                             # diode fault?
        h = self.i2c.io(self.TEMP(channel),1)[0][0]     # read high from reg 0 or 1
        return h+(float(l>>5)/8)                        # return float

    # Returns current pwm percent and rpm for indexed fan
    # rpm only valid if fan in rpm mode
    def get_fan_speed(self, fan):
        pwm=int(round(self.i2c.io(self.DUTY(fan),1)[0][0]/1.2))
        tach = self.i2c.io(self.TACH(fan),1)[0][0]
        rpm = (60000 << self.clock)/tach if tach else 0
        return (pwm,rpm)

if __name__ == "__main__":
    import time

    chip = max6639(1, 0x58)

    # reset and use local temp as temp2, hi freq PWM
    chip.reset(local=True, pwmhi=True)

    print "Device ID = 0x%02X, manufacturer = 0x%02X, revision = 0x%02X" % tuple(chip.i2c.io(chip.ID,3)[0])

    # run fan 1 at 50% duty
    chip.set_pwm_mode(1, 50)

    # start fan 2 at 2000 RPM, follow chip temp
    chip.set_rpm_mode(2, 2000, target=25)

    while True:
        print "Temp = %fC, %fC" % (chip.get_temp(1), chip.get_temp(2))
        print "Fan 1 PWM = %d%%" % chip.get_fan_speed(1)[0]
        print "Fan 2 PWM = %d%%, RPM = %d" % chip.get_fan_speed(2)
        time.sleep(1)
