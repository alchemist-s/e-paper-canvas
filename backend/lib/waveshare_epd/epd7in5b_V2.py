# *****************************************************************************
# * | File        :	  epd7in5b_V2.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V4.2
# * | Date        :   2022-01-08
# # | Info        :   python demo
# -----------------------------------------------------------------------------
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


import logging
from . import epdconfig

# Display resolution
EPD_WIDTH = 800
EPD_HEIGHT = 480

logger = logging.getLogger(__name__)


class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.partFlag = 1

    # Hardware reset
    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(4)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data2(self, data):  # faster
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        logger.debug("e-Paper busy")
        self.send_command(0x71)
        busy = epdconfig.digital_read(self.busy_pin)
        while busy == 0:
            self.send_command(0x71)
            busy = epdconfig.digital_read(self.busy_pin)
        epdconfig.delay_ms(200)
        logger.debug("e-Paper busy release")

    def init(self):
        if epdconfig.module_init() != 0:
            return -1

        # EPD hardware init start
        self.reset()

        self.send_command(0x01)
        self.send_data(0x07)
        self.send_data(0x07)
        self.send_data(0x3F)
        self.send_data(0x3F)

        self.send_command(0x06)
        self.send_data(0x17)
        self.send_data(0x17)
        self.send_data(0x28)
        self.send_data(0x17)

        self.send_command(0x04)
        epdconfig.delay_ms(100)
        self.ReadBusy()

        self.send_command(0x00)
        self.send_data(0x0F)

        self.send_command(0x61)
        self.send_data(0x03)
        self.send_data(0x20)
        self.send_data(0x01)
        self.send_data(0xE0)

        self.send_command(0x15)
        self.send_data(0x00)

        self.send_command(0x50)
        self.send_data(0x11)
        self.send_data(0x07)

        self.send_command(0x60)
        self.send_data(0x22)

        return 0

    def init_Fast(self):
        if epdconfig.module_init() != 0:
            return -1

        # EPD hardware init start
        self.reset()

        self.send_command(0x00)
        self.send_data(0x0F)

        self.send_command(0x04)
        epdconfig.delay_ms(100)
        self.ReadBusy()

        self.send_command(0x06)
        self.send_data(0x27)
        self.send_data(0x27)
        self.send_data(0x18)
        self.send_data(0x17)

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x5A)

        self.send_command(0x50)
        self.send_data(0x11)
        self.send_data(0x07)

        return 0

    def init_part(self):
        if epdconfig.module_init() != 0:
            return -1
        # EPD hardware init start
        self.reset()

        self.send_command(0x00)
        self.send_data(0x1F)

        self.send_command(0x04)
        epdconfig.delay_ms(100)
        self.ReadBusy()

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x6E)

        self.send_command(0x50)
        self.send_data(0xA9)
        self.send_data(0x07)

        # EPD hardware init end
        return 0

    def getbuffer(self, image):
        img = image
        imwidth, imheight = img.size
        if imwidth == self.width and imheight == self.height:
            img = img.convert("1")
        elif imwidth == self.height and imheight == self.width:
            # image has correct dimensions, but needs to be rotated
            img = img.rotate(90, expand=True).convert("1")
        else:
            logger.warning(
                "Wrong image dimensions: must be "
                + str(self.width)
                + "x"
                + str(self.height)
            )
            # return a blank buffer
            return [0x00] * (int(self.width / 8) * self.height)

        buf = bytearray(img.tobytes("raw"))
        # The bytes need to be inverted, because in the PIL world 0=black and 1=white, but
        # in the e-paper world 0=white and 1=black.
        for i in range(len(buf)):
            buf[i] ^= 0xFF
        return buf

    def display(self, imageblack, imagered):
        self.send_command(0x10)
        # The black bytes need to be inverted back from what getbuffer did
        for i in range(len(imageblack)):
            imageblack[i] ^= 0xFF
        self.send_data2(imageblack)

        self.send_command(0x13)
        self.send_data2(imagered)

        self.send_command(0x12)
        epdconfig.delay_ms(100)
        self.ReadBusy()

    def display_Base_color(self, color):
        if self.width % 8 == 0:
            Width = self.width // 8
        else:
            Width = self.width // 8 + 1
        Height = self.height
        self.send_command(0x10)  # Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(color)

        self.send_command(0x13)  # Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(~color)

        self.send_command(0x12)
        epdconfig.delay_ms(100)
        self.ReadBusy()

    def display_Partial(self, Image, Xstart, Ystart, Xend, Yend):
        if (
            (Xstart % 8 + Xend % 8 == 8 & Xstart % 8 > Xend % 8) | Xstart % 8 + Xend % 8
            == 0 | (Xend - Xstart) % 8
            == 0
        ):
            Xstart = Xstart // 8 * 8
            Xend = Xend // 8 * 8
        else:
            Xstart = Xstart // 8 * 8
            if Xend % 8 == 0:
                Xend = Xend // 8 * 8
            else:
                Xend = Xend // 8 * 8 + 1

        Width = (Xend - Xstart) // 8
        Height = Yend - Ystart

        # self.send_command(0x50)
        # self.send_data(0xA9)
        # self.send_data(0x07)

        self.send_command(0x91)  # This command makes the display enter partial mode
        self.send_command(0x90)  # resolution setting
        self.send_data(Xstart // 256)
        self.send_data(Xstart % 256)  # x-start

        self.send_data((Xend - 1) // 256)
        self.send_data((Xend - 1) % 256)  # x-end

        self.send_data(Ystart // 256)  #
        self.send_data(Ystart % 256)  # y-start

        self.send_data((Yend - 1) // 256)
        self.send_data((Yend - 1) % 256)  # y-end
        self.send_data(0x01)

        if self.partFlag == 1:
            self.partFlag = 0
            self.send_command(0x10)
            for j in range(Height):
                for i in range(Width):
                    self.send_data(0xFF)

        self.send_command(0x13)  # Write Black and White image to RAM
        self.send_data2(Image)

        self.send_command(0x12)
        epdconfig.delay_ms(100)
        self.ReadBusy()

    def Clear(self):
        logger.info("Clearing display for real")
        buf = [0x00] * (int(self.width / 8) * self.height)
        buf2 = [0xFF] * (int(self.width / 8) * self.height)
        self.send_command(0x10)
        self.send_data2(buf2)

        self.send_command(0x13)
        self.send_data2(buf)

        self.send_command(0x12)
        epdconfig.delay_ms(100)
        self.ReadBusy()

    def sleep(self):
        self.send_command(0x02)  # POWER_OFF
        self.ReadBusy()

        self.send_command(0x07)  # DEEP_SLEEP
        self.send_data(0xA5)

        epdconfig.delay_ms(2000)
        epdconfig.module_exit()


### END OF FILE ###
