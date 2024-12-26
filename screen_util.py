"""Screen Utility Module
    :author: Paul Redhead




This provides utility classes for use in screen display functions, e.g. tiles and menus.  The basic access
the display is via tiles.
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


# micropython imports
import framebuf

# lib imports
from oled1_5 import OLED_1in5



## font created from courier new
import courier14


class Section:
    """This class describes a track section for screen display purposes and application purposes.

    Track section are displayed on the screen within a layout tile
    as vector polyons using the
    Framebuffer.poly() method.

    Each track section has an x, y position within the tile and a list of coordinates
    describing the shape.
    """

    def __init__(self, x, y, coords):
        """Construct the object based on supplied parameters

        Args:
            self:
            x:  x coordinate for display
            y:  y coordinate for display
            coords: list of poly point coordinates relative to x,y
            """
        self._x = x
        self._y = y
        self._coords = coords

    def draw(self, tile, c):
        """ Draw the track section
        
        Create an image of the track section within the supplied tile.

        Args:
            self:
            tile:  the tile to draw on - the Tile class is based on frambuf.Frambuffer
            c:  colour
        """
        tile.poly(self._x, self._y, self._coords, c)    


class Tile(framebuf.FrameBuffer):
    """This Class describes a Tile
    
    A Tile is an rectangular area to be displayed on the screen.  It is built on the standard
    FramBuffer but adds a methods to display the tile on the screen and print text using a simple courier font
    (larger than standard Framebuffer text).  It provides the primary display access.
    """

    _palette =   [framebuf.FrameBuffer(bytearray(b'\x08'), 2, 1, framebuf.GS4_HMSB),
                framebuf.FrameBuffer(bytearray(b'\x0F'), 2, 1, framebuf.GS4_HMSB),
                framebuf.FrameBuffer(bytearray(b'\xc0'), 2, 1, framebuf.GS4_HMSB)]
    """
    Blit Palettes
    
    These palettes are to be used in blit command for converting B&W to greyscale
    for use with the courier font.

     - 0 - mid power white on black
     - 1 - full power white on black
     - 2 - black on white
    """

    _disp = None

    def __init__(self, w, h):
        """Initialise the Tile
        
        This is the standard initialiser and will be called automatically when the object is
        instantiated.  It initialises the framebuffer too.

        The first Tile to be instantiated will get the reference to the physical display object
        singleton.

        Args:
            self:
            w:  tile width in pixels
            h:  tile heigth in pixels
        """
        assert (w <= OLED_1in5.OLED_WIDTH) and (h <= OLED_1in5.OLED_HEIGHT) and ((w % 2) == 0), "Invalid Dimensions"
        self._width = w
        self._height = h
        self._buffer = bytearray(w * h // 2)
        """4 bit grey scale, two pixels per byte"""
        super().__init__(self._buffer, w, h, framebuf.GS4_HMSB)

        # The first Tile will get the OLED object reference which will be instantiated if necessary
        if Tile._disp == None:
            Tile._disp = OLED_1in5.get_instance()

    def show(self, x , y):
        """Send tile to screen

        This displays the tile on the screen provided when the Tile 
        was created.
        
        Args:
            self:
            x:  x coordinate for display
            y:  y coordinate for display
            """
        Tile._disp.show(self._buffer, x, y, self._width, self._height)



    def courier_text(self,s, x, y, c = 0):
        """Courier Font Writer 
        
        Output simple text using courier14 font.  Same params as Frambuffer.text()
        
        Courier font created using Peter Hinch's utility


        Args:
            self:
            s:  text string to be rendered
            x: start x
            y:  start y
            c: palette to be used (default 0)
            """
        for ch in s:
            cb, h, w = courier14.get_ch(ch)
            char_fb = framebuf.FrameBuffer(bytearray(cb), w, h, framebuf.MONO_HLSB)
            
            self.blit(char_fb, x, y, -1, Tile._palette[c])

            x = x + w
            if x >= self._width:
                # line full - do a simple wrap
                x = 0
                y = y + h
                if y >= self._height:
                    y = 0    


