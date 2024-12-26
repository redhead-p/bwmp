"""Relay Control Module
    :author: Paul Redhead

    
This module provides a single class - Relay - which is used to control relays connected to specific
pins.

Given that there are two-phase supplies to the track the relays are paired with one 
pin energising two relays. The distribution of power to the track as currently designed means that only
one pair of relays may be set at any time.  However to allow for a more generalised solution this constraint
is not enforced.

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
from machine import Pin, Timer
from device import Device
from micropython import const

class Relay(Device):
    """Control a relay.

    This class is a simple wrapper for a pin
    that provides relay & application specific additions.
    It allows a relay to be named and report its state.

    The photovoltaic relays used can take up to 5mS to turn on and 
    0.5 mS to turn off.  We allow 10ms.
    
    It inherits from Device. Ideally we would inherit from Pin too 
    but MicroPython doesn't
    support inheritance from multiple classes.
    """

    RELAY_TIME = const(10)
    """ The time allowed for the relay to change(ms)
    
    The new relay state will be reported after this delay.
    """

    _relay_list = [] # list of known relays

    @classmethod
    def get_relay_list(cls):
        """Get Relay List
        
        This exposes the list of relay objects.

        Args:
            cls:

        Returns:
            The list of relay objects that have been instantiated.
        """
        return cls._relay_list

    def __init__(self, name, pin_no):
        """Relay Constructor
        
        Constuct a relay object.

        Args:
            self:
            name: character string used for indexing
            pin_no: GPIO pin number
        """
        self._relay_pin = Pin(pin_no, Pin.OUT, value = 0)
        super().__init__(name, 'r')
        Relay._relay_list.append(self)
        self._timer = Timer()
        self._state = 2 # unknown/indeterminate
    
    def value(self, v = None):
        """Set or get the relay value.

        Set the relay.
        
        The name value is used for consistency with Pin and Sector
        
        Args:
            self:
            v:  the relay value to be set,
                1 for on,
                0 for off,
                None/omitted to read the current setting
        """
        # get the current value
        cv = self._relay_pin.value()
        if v == None:
            return(cv)
        if v != cv:
            # only report action initiated if action is needed
            self.report_event(Device.ACTION_INIT,cv)
            self._relay_pin.value(v)
            self._timer.init(mode = Timer.ONE_SHOT, period = 10, callback = self._timer_done)
            self._state = Device.INDETERMINATE # indeterminate
            return(cv)
        # no action required
        self._state = cv
        self.report_event(Device.ACTION_DONE,v)
        return v

    def _timer_done(self, _):
        self._timer.deinit()
        self._state = self._relay_pin.value()
        self.report_event(Device.ACTION_DONE,self._state)

    def get_state(self):
        """Get the relay's state

        Args:
            self:

        returns:
            The relay's state 0 or 1 as set by the pin or 2 if settling.
        """

        return self._state


    
        
        


