"""Device Module
    :author: Paul Redhead

This provides the Device class, a base class for hardware device drivers and
similar objects.

The RP2040 has two cores (0 and 1).  When running MicroPython by default core 0 is used
and core 1 is idle.  The RP2040 port of MicroPython uses the _thread module to run code
in core 1 and enable communications between the cores.  At the moment there's only a single thread running on Core 0.

This module provides a queue for passing events.  Multiple
sources may write to the queue.  There may be only 1 reader.  The reader runs in the main loop.  Sources are 
typically event driven.
"""
"""
        Copyright (C) 2023, 2034 Paul Redhead


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
# stardard python imports
from collections import deque

# micropython imports
from machine import Pin, mem32, WDT
import time
from micropython import const


MAX_Q_LEN = const(16)
"""The capacity of the event queue."""





class ThreadQError(RuntimeError):
    """Thread Queue Error
    
    Raised to indicate adding to the queue failed due to queue full."""
    pass





class Device():
    """Device Base Class
    
    This class acts as a base for hardware devices and similar. In particular those devices which need to raise 
    events for display on the screen or initiate actions as part of automation.  Events are queued.  Although 
    many devices may raise events there is only one reader.  Typically the device class is a abstract class.  I.e not
    instantiated independently.
    
    Attributes:
        ACTION_DONE: Assigned action completed
        ACTION_ERROR: Error encountered during action
        ACTION_INIT: Assigned action initiated
        UI_QUAD: User input from Quadrature Encoder
        UI_SWITCH: User input from switch/press button
        UNKNOWN: State unavalable (e.g start of day / action in progress)
        """
    # class variables

    ACTION_DONE = const(0)
    """Assigned action completed"""
    ACTION_ERROR = const(-1)
    """ Error encountered"""
    ACTION_INIT = const(1)
    """Action initiated (further event expected)"""
    UI_QUAD = const(2)
    """ User input from quadrature encoder"""
    UI_SWITCH = const(3)
    """ User input from press button"""

    # device states 0 & 1 are allocated for hardware devices with binary states e.g. points & relays etc
    UNSET = const(0)
    """State unset / off / false"""
    SET = const(1)
    """State Set / on / true or action complete if > 2 operables states"""
    UNKNOWN = const(2)
    """State unavalable (e.g start of day"""
    INDETERMINATE = const(3)
    """State indeterminate (e.g. action in progress)"""
    
    
    # _fido = WDT()  # enable a watch dog timer just in case



    _queue = deque((), MAX_Q_LEN, 1)

    


    
    ## empty device table
    # will be added to by devices when instantiated.
    _device_table = {}

    @classmethod 
    def by_name(cls, name):
        """Find a device object by name
        
        Args:
            cls:
            name: the name of the device
            
        Returns:
            refererence to the object
            
        Raises:
            IndexError if not found"""
        return cls._device_table[name]
    
    @classmethod
    def get_items(cls):
        """Get items from the device table.

        The device table holds a list of the device objects keyed by their name.
        
        returns:
            a list of items - name and device object pairs"""
        return cls._device_table.items()
    
    @classmethod
    def get_keys(cls):
        """Get device names (keys) from the device table.

        The device table holds a list of the device objects keyed by their name.
        
        returns:
            a list of device names"""
        return cls._device_table.keys()
    
    @classmethod
    def get_event_report(cls):
        """ get the event report at top of queue
        
        This is synchronous. It will wait forever if queue empty.

        Args:
            cls:

        Returns:
            an event tuple comprising:
            -   self: the object reporting the event
            -   event: one of ACTION_DONE, ACTION_ERROR, ACTION_INIT or as defined for device
            -   data: depends on source object and event

        """
       
        try:
            # see if anything there
            source, event, data = cls._queue.popleft()
            return(source, event, data)
            
        except IndexError:
            # queue empty

            while len(cls._queue) == 0:
#                cls._fido.feed()
                time.sleep_ms(0)

            # queue no longer empty
            try:
                source, event, data = cls._queue.popleft()

            except IndexError:
                raise ThreadQError('Q index')

            return(source, event, data)


    def __init__(self, name, type):
        """Initialise Device

        This initialises the device.  Usally invoked by super().__init__() from the child.

        Save the name (should be unique but not formally tested) & type.  Type is a single character. Could
        used __class__ but that would be more complex.

        Args:
            self:
            name: string containing the device name
            type: character specifying the type of device (i.e. class of child)
        
        """
        
        self._name = name
        self._type = type
        Device._device_table[name] = (self)

    def get_name(self):
        """Get the device name
        
        args:
            self:
            
        returns:
            the device name as a string"""
        return self._name
    
    def get_type(self):
        """Get the device type
        
        args:
            self:
            
        returns:
            the device type as a single character string"""
        return self._type
    
    def value(self, v = None):
        """Get or Set the device value
        
        This must be superseded by a bound method in an inheriting class. Otherwise
        a 'not implemented' error will be raised when called.
        
        args:
            self:
            v: the value to be writen if supplied
        
        raises:
            NotImplementedError: if not overridden"""
        
        raise NotImplementedError
    
    def get_state(self):
        """Get the device state
        
        This must be superseded by a bound method in an inheriting class. Otherwise
        a 'not implemented' error will be raised when called.
        
        args:
            self:
        
        raises:
            NotImplementedError: if not overridden"""
        
        raise NotImplementedError


    def report_event(self, event, data):
        """ Add event report to the queue

        The event report is added to the queue.

        :raise ThreadQError:  The queue is full

        args:
            self:
            event:  event code - system specific
            data:   event data to qualify code - device dependent  
            """
        try:
            Device._queue.append((self, event, data))
        except IndexError:
            raise ThreadQError('Q full')    