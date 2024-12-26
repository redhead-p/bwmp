"""OLED Display Module
    :author: Paul Redhead


This is the driver module for the 1.5" OLED Display.  It defines the OLED class and 
constants associated with the display. This is a singleton class.
"""
"""
       Copyright 2023 Paul Redhead

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from machine import Pin, SPI
import time
import framebuf
from micropython import const
#from micropython import schedule, opt_level




OLED_CS = const(13)
"""OLED chip select"""
OLED_DC = const(14)
"""OLED data - command"""
OLED_RS = const(12)
"""OLED reset"""

# other pins as default for SPI1






class OLED_1in5():
    """The OLED Display Driver

    The display is a 1.5" OLED on SPI 
    - CS - chip select
    - DC - data or command
    - RS - reset

    The driver uses SPI1 and additional pins. The screen is 4 bit Grey scale using SSD1327 controller.

    Attributes:
        OLED_WIDTH:  OLED width in pixels
        OLED_HEIGHT:  OLED height in pixels

    """
    
    OLED_WIDTH   = const(128)
   
    OLED_HEIGHT  = const(128)
    
    _spi = None

    _oled = None

    @classmethod
    def get_instance(cls):
        """ Instantiate oled driver if not yet done
        
        args:
            cls:
            """
        if cls._oled == None:
            cls._oled = OLED_1in5()
        return cls._oled

    def __init__(self):
        """OLED_1in5 constructor.

        This constructs the display driver. 
        Args:
            self:
        """

        #Initialize DC & RST pins
        self._dc = Pin(OLED_DC, Pin.OUT)
        self._rst = Pin(OLED_RS, Pin.OUT, value = 1)  # not reset
        self._cs  = Pin(OLED_CS, Pin.OUT, value = 1)  # not chip select
        #esp32 spi
        #self._spi = SPI(1, baudrate = 10_000_000, polarity=1, phase=1, sck=Pin(14),mosi=Pin(13),miso=None)
        #RP2040 spi
        if OLED_1in5._spi == None:
            OLED_1in5._spi = SPI(1, baudrate = 5_000_000, miso = None)
            OLED_1in5._oled = self
        else:
            # enforce screen driver as a singleton
            raise RuntimeError ('Only one display possible')
        
        #NRF52
        #self._spi = SPI(1,baudrate = 10_000_000)
        
        self._rst(0)    # assert reset
        time.sleep_ms(2) # requires 2ms
        self._rst(1)    # back to normal
        self._init_display()


    # IO commands - note use of arrays rather than bytewise operations

    def _write_cmd(self, cmd):
        self._dc(0)
        self._cs(0)
        self._spi.write(bytearray([cmd]))
        self._cs(1)

    def _write_data(self, buf):
        self._dc(1)
        self._cs(0)
        self._spi.write(bytearray([buf]))
        self._cs(1)

    ## @brief Initialise Display
    #
    # set the display registers up
    # @par self
    def _init_display(self):

        self._write_cmd(0xae)     #--turn off oled panel

        self._write_cmd(0x15)     #  set column address
        self._write_cmd(0x00)     #  start column   0
        self._write_cmd(0x7f)     #  end column   127

        self._write_cmd(0x75)     #   set row address
        self._write_cmd(0x00)     #  start row   0
        self._write_cmd(0x7f)     #  end row   127

        self._write_cmd(0x81)     # set contrast control
        self._write_cmd(0x80) 

        self._write_cmd(0xa0)     # segment remap
        self._write_cmd(0x51)     #51

        self._write_cmd(0xa1)     # start line
        self._write_cmd(0x00)     # (as reset)

        self._write_cmd(0xa2)     # display offset
        self._write_cmd(0x00) 	 # (as reset)

        self._write_cmd(0xa4)     # normal display
        self._write_cmd(0xa8)     # set multiplex ratio
        self._write_cmd(0x7f)	 # (as reset)

        self._write_cmd(0xb1)     # set phase leghth
        self._write_cmd(0xf1) 

        self._write_cmd(0xb3)     # set dclk
        self._write_cmd(0x00)     #80Hz:0xc1 90Hz:0xe1   100Hz:0x00   110Hz:0x30 120Hz:0x50   130Hz:0x70     01
 
        self._write_cmd(0xab)     # Enable internal Vdd regulator
        self._write_cmd(0x01)     # 

        self._write_cmd(0xb6)     # set phase leghth
        self._write_cmd(0x0f) 

#         self._write_cmd(0xbe) 	 # complex stuff to do with voltages!
        self._write_cmd(0x0f) 

        self._write_cmd(0xbc) 
        self._write_cmd(0x08) 

        self._write_cmd(0xd5) 
        self._write_cmd(0x62) 

        self._write_cmd(0xfd) 	# ensure unlocked
        self._write_cmd(0x12) 

        time.sleep_ms(100)


        self._write_cmd(0xAF);#--turn on oled panel
        
 
 
        

    def show(self,  buffer, x = 0, y = 0, w = OLED_WIDTH, h = OLED_HEIGHT):
        """Show the screen.

        The screen is written from the provided buffer.  This is a rectangular 
        area of pixrels either full or part screen.  The default arguments are for a full 
        screen.

        Args:
            self:
            buffer: buffer containing the screen information to be displayed
            x: x coordinate (column number) of area to be displayed
            y: y coordinate (row number) of area to be displayed
            w: width of area
            h: height of area
        """

        assert (x % 2) == 0, "disp area must start on byte boundary"

        self._write_cmd(0x15)    # set start column and end address
        self._write_cmd(x//2)
        self._write_cmd((x + w)//2 - 1)

        
        self._write_cmd(0x75)    # set start row and end address
        self._write_cmd(y)

        self._write_cmd(y + h - 1)
    
        self._dc(1)
        self._cs(0)
        self._spi.write(buffer)
        self._cs(1)

if __name__=='__main__':
    
    o = OLED_1in5()
    buffer = bytearray(100 *  15 // 2)  # 4 bit grey scale, two pixels per byte
    f = framebuf.FrameBuffer(buffer, 100,  15, framebuf.GS4_HMSB)

   
    x = time.ticks_us()
    f.fill(0)
    print(time.ticks_us() -  x)


    x = time.ticks_us()
    f.text('Hello World', 0, 0)



    print(time.ticks_us() -  x)
    x = time.ticks_us()
    o.show(buffer, 0, 10, 100,  15)
    print(time.ticks_us() -  x)


