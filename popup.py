"""Simple Menu Management
    :author: Paul Redhead

This module has classes for Menu and MenuItems so that simple menus can be built and displayed.
Additionally it may provide other 'widgets' e.g. numeric input.
"""
"""
       Copyright 2023, 2024 Paul Redhead

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

# standard python imports
from array import array

# micropython imports
from micropython import const

# /lib imports
from screen_util import Tile

# font created from courier new
import courier14

class NumberIn:
    """Number Entry
    
    This class handles simple number entry."""

    def __init__(self, label, max, min, value_action, increment = 1):
        """Initialise a Number Entry object
        
        The paramaters are saved.
        
        Args:
            self:
            label:  the label string
            max:    the maximum value
            min:    the minimum value (may be negative)
            value_action: function to be called on number entry complete (button press)
            increment: amount by which 1 click alters the number
            """
        self._label = label
        self._max = max
        self._min = min
        self._value = 0
        self._value_action = value_action
        self._inc = increment

    def build(self):
        """Build a number entry widget

        This builds a Tile to allow for a value to be entered.

        Args:
            self:
        """

        # determine dimenstions from label and limits
        h = (courier14.height() + 3) 
      
        w = len(self._label) * courier14.max_width()
        self._num_w = (max(len(str(self._max)), len(str(self._min))) + 1) * courier14.max_width()
        w = w + self._num_w + Menu.CURS_WW # add in cursor width
        self._height = h # save height
        self._width = w
        
        # create the tile for the labels etc 
        self._p_tile = Tile(w, h)
        self._p_tile.fill(0)
        self._p_tile.courier_text(self._label, Menu.CURS_WW, 2 , 0)
           
        # draw framing lines
        self._p_tile.hline(0, 0, w, 1)
        self._p_tile.hline(0, h - 1, w, 1)
        
        self._p_tile.vline(w - 1, 0, h, 1)
        self._p_tile.vline(0, 0, h, 1)

        self._p_tile.poly(3, 4, Menu.CURS_L, 2, True)
        self._show_value()
        self._p_tile.show(0, 0)

    def quad_decode(self, data):
        """Process quadrature decoder event.
        
        Update the number by incrementing or decrementing as indicated by the event.
        The value is constrained. The updated value is displayed on screen.
        
        Args:
            self:
            data: normally + or - 1 depending on direction of rotation.
        """
        self._value = self._value + (data * self._inc)
        
        # constrain the value to be within max and min
        self._value = max(min(self._value, self._max), self._min)
        self._show_value()
        self._p_tile.show(0, 0)
        

    def _show_value(self):
        value_str = str(self._value)
        self._p_tile.rect(self._width - self._num_w - 1, 1, self._num_w, courier14.height(), 0, True)
        self._p_tile.courier_text(value_str,self._width - (len(value_str) * courier14.max_width()) - 2, 2, 0)

    def button(self, data):
        """Take number input Button-Press action.

        If button pressed the defined action is taken. No action on button release.

        args:
            self:
            data: 0 if button pressed, else 1

        returns:
            boolean - true if button pressed else false

        
        """
        if data == 0:
            (self._value_action)(self._value)
            return True
        
        return False





class MenuItem:
    """The Menu Item Class
    
    This corresponds to a line on the menu and is used to build a menu.
    
    It holds the menu item label as displayed, the action method and the parameters 
    to be passed to the action method."""

    def __init__(self, label, action, params, single = True):
        """Menu Item constructor
        
        This builds a menu item - a single line on the menu.
        
        args:
            self:
            label: a textual label for menu display
            action: the action to be taken when the item is selected
            params: a tuple containing parameters for the action
            single: if true the menu system will be exited after this item completes
        """
        self._label = label
        self._action = action
        self._params = params
        self._single = single

    def get_label(self):
        return(self._label)
    
    def do_action(self):
        #print (self._action.__name__, self._params)
        (self._action)(*self._params)

    def is_single(self):
        return self._single

class PopUp:
    """Base class for popups
    
    This is the base class for popups (e.g. menus and simple forms)
    
    """

    def __init__(self, title, item_list = list()):
            self._title = title
            self._item_list = item_list
            self._cursor_pos = 0 # set to first menu item

    def button(self, data):
        raise NotImplementedError
    
    def build(self):
        raise NotImplementedError
    
    def quad_decode(self, data):
        raise NotImplementedError
    
    # may need to add display_cursor() and append()
    
class Menu(PopUp):
    """This class manages menu displays.

    The class provides for menus to be setup, built and displayed.
    Once display UI quad encoder and push button events are used to select 
    an entry and intiate actions.

    Menus may be built from static menu item lists or dynamically so menu items
    can have labels generated on the fly

    Attributes:
        CURS_WW:    Cursor window width
        CURS_R:     Polygon for right facing cursor
        CURS_L:     Polygon for left facing cursor

    """
    CURS_WW = const(12) #cursor window width

    CURS_R = array('h',[0 , 0,  4, 3,  0, 6]) #forward pointing cursor 
    CURS_L = array('h',[4 , 0,  0, 3,  4, 6]) #backward pointing cursor 

    def __init__(self, title, item_list = list()):
        """Menu Constructor
        
        This calls the base class (PopUp) constructor

        Args:
            self:
            title: Menu Title (string)
            item_list:  a simple list of menu items (default - an empty list)
        """
        super().__init__(title, item_list)


    def button(self, data):
        """Take Menu Button Press Action
        
        This can either be to exit the menu or act on one of the menu options
        
        Args:
            self:
            data: 0 - button pressed, 1 - button release
            
        Returns:
            action result Boolean:  True leave menu system, False stay in menu"""
        
        if data == 0:
            if self._cursor_pos >= 0:
                self._item_list[self._cursor_pos].do_action()
                return self._item_list[self._cursor_pos].is_single()
            else:
                # first item on menu is menu exit 
                return True
        # button release ignored so don't leave
        return False 
          


    def append(self, item):
        """Append Item to Menu.
        
        This appends a menu item to the menu, allowing menus with varying
        content to be built on the fly.
        
        Args:
            self:
            item:   the menu item to be added.
            """
        self._item_list.append(item)
        
    def build(self):
        """Build a menu
        
        This builds a menu based on current attributes.  The menu is boxed.  A tile is allocated to hold
        the item labels and a second tile is used for the cursor
        Both tiles are set up and displayed.
        """

        # determine menu dimenstions from the item list etc
        h = (courier14.height() + 1) * (len(self._item_list) + 1)
        w = max((courier14.max_width() * len(item.get_label()) for item in self._item_list))
        w = max(w, len(self._title) * courier14.max_width()) + courier14.max_width()
        self._height = h # save height 
        
        # create the tile for the labels etc 
        m_tile = Tile(w, h)
        m_tile.fill(0)
        # add title
        m_tile.courier_text(self._title, 0, 1, 0)
        r = courier14.height() + 1
        # add item labels
        for item in self._item_list:
            m_tile.courier_text(item.get_label(),0 , r , 0)
            r = r + courier14.height() + 1
        # draw framing lines
        m_tile.hline(0, 0, w, 1)
        m_tile.hline(0, h - 1, w, 1)
        m_tile.hline(0, courier14.height() + 1, w, 1)
        m_tile.vline(w - 1, 0, h, 1)
        # display label tile
        m_tile.show(Menu.CURS_WW, 0)
        # create tile for cursor - will be retained while menu is loaded
        self._c_tile = Tile(Menu.CURS_WW, self._height)
        self.show_cursor()

    def quad_decode(self, data):
        """Process quadrature decoder event.
        
        Move the cursor up or down the screen as appropriate. Down for CW, UP for CCW
        
        Args:
            self:
            data: normally + or - 1 depending on direction of rotation.
        """
        self._cursor_pos = self._cursor_pos + data
        if self._cursor_pos < -1:
            self._cursor_pos = len(self._item_list) - 1
        elif self._cursor_pos  >= len(self._item_list):
            self._cursor_pos = -1
        self.show_cursor()


    def show_cursor(self):
        """Show the Cursor
        
        Remove the old cursor and display the cursor in the new position.  If the cursor is
        on the to line, it's displayed left pointing.
        
        Args:
            self:
        """
        
        self._c_tile.fill(0)    # clear cursor (and everything else)
        self._c_tile.hline(0, 0, Menu.CURS_WW, 1)
        self._c_tile.hline(0, self._height - 1, Menu.CURS_WW, 1)
        self._c_tile.hline(0, courier14.height() + 1, Menu.CURS_WW, 1)
        self._c_tile.vline(0, 0, self._height, 1)

        if self._cursor_pos >= 0:
            self._c_tile.poly(3, (self._cursor_pos + 1) * (courier14.height() +1) + 2, Menu.CURS_R, 1, True)
        else:
            self._c_tile.poly(3, 3, Menu.CURS_L, 1, True)
        self._c_tile.show(0, 0)

        
        




