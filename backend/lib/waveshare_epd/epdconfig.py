# /*****************************************************************************
# * | File        :	  epdconfig.py
# * | Author      :   Waveshare team
# * | Function    :   Hardware underlying interface
# * | Info        :
# *----------------
# * | This version:   V1.2
# * | Date        :   2022-10-29
# * | Info        :
# ******************************************************************************
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import os
import logging
import sys
import time
import subprocess

from ctypes import *

logger = logging.getLogger(__name__)


class RaspberryPi:
    # Pin definition
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18
    MOSI_PIN = 10
    SCLK_PIN = 11

    def __init__(self):
        import spidev
        import RPi.GPIO as GPIO

        self.SPI = spidev.SpiDev()
        self.GPIO = GPIO

        # Set up GPIO mode
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)

        # Set up pins
        self.GPIO.setup(self.RST_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.DC_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.CS_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.PWR_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.BUSY_PIN, self.GPIO.IN)

    def digital_write(self, pin, value):
        self.GPIO.output(pin, value)

    def digital_read(self, pin):
        return self.GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        self.SPI.writebytes2(data)

    def DEV_SPI_write(self, data):
        self.DEV_SPI.DEV_SPI_SendData(data)

    def DEV_SPI_nwrite(self, data):
        self.DEV_SPI.DEV_SPI_SendnData(data)

    def DEV_SPI_read(self):
        return self.DEV_SPI.DEV_SPI_ReadData()

    def module_init(self, cleanup=False):
        self.GPIO.output(self.PWR_PIN, 1)

        if cleanup:
            find_dirs = [
                os.path.dirname(os.path.realpath(__file__)),
                "/usr/local/lib",
                "/usr/lib",
            ]
            self.DEV_SPI = None
            for find_dir in find_dirs:
                val = int(os.popen("getconf LONG_BIT").read())
                logging.debug("System is %d bit" % val)
                if val == 64:
                    so_filename = os.path.join(find_dir, "DEV_Config_64.so")
                else:
                    so_filename = os.path.join(find_dir, "DEV_Config_32.so")
                if os.path.exists(so_filename):
                    self.DEV_SPI = CDLL(so_filename)
                    break
            if self.DEV_SPI is None:
                RuntimeError("Cannot find DEV_Config.so")

            self.DEV_SPI.DEV_Module_Init()

        else:
            # Always open SPI device - the previous check was causing issues
            # SPI device, bus = 0, device = 0
            self.SPI.open(0, 0)
            self.SPI.max_speed_hz = 4000000
            self.SPI.mode = 0b00
        return 0

    def module_exit(self, cleanup=False):
        logger.debug("spi end")
        self.SPI.close()

        self.GPIO.output(self.RST_PIN, 0)
        self.GPIO.output(self.DC_PIN, 0)
        self.GPIO.output(self.PWR_PIN, 0)
        logger.debug("close 5V, Module enters 0 power consumption ...")

        if cleanup:
            self.GPIO.output(self.RST_PIN, 0)
            self.GPIO.output(self.DC_PIN, 0)
            self.GPIO.output(self.PWR_PIN, 0)
            self.GPIO.output(self.BUSY_PIN, 0)


class JetsonNano:
    # Pin definition
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18

    def __init__(self):
        import ctypes

        find_dirs = [
            os.path.dirname(os.path.realpath(__file__)),
            "/usr/local/lib",
            "/usr/lib",
        ]
        self.SPI = None
        for find_dir in find_dirs:
            so_filename = os.path.join(find_dir, "sysfs_software_spi.so")
            if os.path.exists(so_filename):
                self.SPI = ctypes.cdll.LoadLibrary(so_filename)
                break
        if self.SPI is None:
            raise RuntimeError("Cannot find sysfs_software_spi.so")

        import Jetson.GPIO

        self.GPIO = Jetson.GPIO

    def digital_write(self, pin, value):
        self.GPIO.output(pin, value)

    def digital_read(self, pin):
        return self.GPIO.input(self.BUSY_PIN)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.SYSFS_software_spi_transfer(data[0])

    def spi_writebyte2(self, data):
        for i in range(len(data)):
            self.SPI.SYSFS_software_spi_transfer(data[i])

    def module_init(self):
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)
        self.GPIO.setup(self.RST_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.DC_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.CS_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.PWR_PIN, self.GPIO.OUT)
        self.GPIO.setup(self.BUSY_PIN, self.GPIO.IN)

        self.GPIO.output(self.PWR_PIN, 1)

        self.SPI.SYSFS_software_spi_begin()
        return 0

    def module_exit(self):
        logger.debug("spi end")
        self.SPI.SYSFS_software_spi_end()

        logger.debug("close 5V, Module enters 0 power consumption ...")
        self.GPIO.output(self.RST_PIN, 0)
        self.GPIO.output(self.DC_PIN, 0)
        self.GPIO.output(self.PWR_PIN, 0)

        self.GPIO.cleanup(
            [self.RST_PIN, self.DC_PIN, self.CS_PIN, self.BUSY_PIN, self.PWR_PIN]
        )


class SunriseX3:
    # Pin definition
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18
    Flag = 0

    def __init__(self):
        import spidev
        import Hobot.GPIO

        self.GPIO = Hobot.GPIO
        self.SPI = spidev.SpiDev()

    def digital_write(self, pin, value):
        self.GPIO.output(pin, value)

    def digital_read(self, pin):
        return self.GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        # for i in range(len(data)):
        #     self.SPI.writebytes([data[i]])
        self.SPI.xfer3(data)

    def module_init(self):
        if self.Flag == 0:
            self.Flag = 1
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.setwarnings(False)
            self.GPIO.setup(self.RST_PIN, self.GPIO.OUT)
            self.GPIO.setup(self.DC_PIN, self.GPIO.OUT)
            self.GPIO.setup(self.CS_PIN, self.GPIO.OUT)
            self.GPIO.setup(self.PWR_PIN, self.GPIO.OUT)
            self.GPIO.setup(self.BUSY_PIN, self.GPIO.IN)

            self.GPIO.output(self.PWR_PIN, 1)

            # SPI device, bus = 0, device = 0
            self.SPI.open(2, 0)
            self.SPI.max_speed_hz = 4000000
            self.SPI.mode = 0b00
            return 0
        else:
            return 0

    def module_exit(self):
        logger.debug("spi end")
        self.SPI.close()

        logger.debug("close 5V, Module enters 0 power consumption ...")
        self.Flag = 0
        self.GPIO.output(self.RST_PIN, 0)
        self.GPIO.output(self.DC_PIN, 0)
        self.GPIO.output(self.PWR_PIN, 0)

        self.GPIO.cleanup(
            [self.RST_PIN, self.DC_PIN, self.CS_PIN, self.BUSY_PIN], self.PWR_PIN
        )


# Platform detection - Python-based instead of shell commands
def detect_platform():
    """Detect the platform using Python instead of shell commands"""
    try:
        # Check for Raspberry Pi by reading /proc/cpuinfo directly
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            if "Raspberry" in cpuinfo:
                return "RaspberryPi"
    except (FileNotFoundError, PermissionError):
        pass

    # Check for Sunrise X3
    if os.path.exists("/sys/bus/platform/drivers/gpio-x3"):
        return "SunriseX3"

    # Default to JetsonNano
    return "JetsonNano"


platform_type = detect_platform()

if platform_type == "RaspberryPi":
    implementation = RaspberryPi()
elif platform_type == "SunriseX3":
    implementation = SunriseX3()
else:
    implementation = JetsonNano()

for func in [x for x in dir(implementation) if not x.startswith("_")]:
    setattr(sys.modules[__name__], func, getattr(implementation, func))

### END OF FILE ###
