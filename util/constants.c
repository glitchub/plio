// Print various constants that are generated at compile-time.
// Not required for normal use.
#include <stdio.h>
#include <linux/gpio.h>
#include <linux/spi/spidev.h>

#define show(s) printf("%-40s= 0x%08X\n", #s, s)

int main(void)
{
    show(GPIO_GET_CHIPINFO_IOCTL);
    show(GPIO_GET_LINEINFO_IOCTL);
    show(GPIO_GET_LINEHANDLE_IOCTL);
    show(GPIO_GET_LINEEVENT_IOCTL);
    show(GPIOHANDLE_GET_LINE_VALUES_IOCTL);
    show(GPIOHANDLE_SET_LINE_VALUES_IOCTL);
    show(SPI_IOC_MESSAGE(0));
    show(SPI_IOC_MESSAGE(1));
    show(SPI_IOC_MESSAGE(2));
    show(SPI_IOC_MESSAGE(16));
    show(SPI_IOC_RD_MODE);
    show(SPI_IOC_WR_MODE);
    show(SPI_IOC_RD_LSB_FIRST);
    show(SPI_IOC_WR_LSB_FIRST);
    show(SPI_IOC_RD_BITS_PER_WORD);
    show(SPI_IOC_WR_BITS_PER_WORD);
    show(SPI_IOC_RD_MAX_SPEED_HZ);
    show(SPI_IOC_WR_MAX_SPEED_HZ);
    show(SPI_IOC_RD_MODE32);
    show(SPI_IOC_WR_MODE32);
}
