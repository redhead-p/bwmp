"""Sector Plate Module.
    :author: Paul Redhead

This module contains code associated with the sector plate. The sector plate is servo powered.
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
from machine import Timer, Pin, PWM
import time
from device import Device
from micropython import const


class Sector(Device):
    """This class controls the sector table device.

    The sector plate rotates around an axis at one end and is aligned with one of 
    three tracks to allow stock to transfer on or off the plate track.  It inherits 
    from the Device class to allow it to raise events and be identified.

    A GPIO pin is configured as a PWM generator to control the servo that moves the 
    sector plate.

    Attributes:
        MAIN:       Main - set to main line
        LOCO:   Loco - set to loco siding
        COACH:  Coach - set to coach siding
        SETTLE: Number of steps settling at end of movement
        TIMER_PERIOD:  timer period in ms (20ms)
        TRAVEL_PERIOD: Time taken to move
        LONG_THRESHOLD: allow double time if pulse width count change > this
    
    """
    
    # static constants
    # sector state (would be enum but enum not available in MicroPython)


    SETTLE = const(5)       # Number of steps settling at end of movement


    TIMER_PERIOD = const(20) # timer period in ms (20ms)
    TRAVEL_PERIOD = const(2000) # 2  seconds
    LONG_THRESHOLD = const(500) # allow double time if pw count change > this
    

    
    _sectorList = []
    """List of sector objects.

    Initially empty but added to as sector plates are instantiated.
    """
   

    _timer = Timer()
    """one timer for all sector plate objects
    """

    @staticmethod
    def _timeStep(_):
        """Call each point instance in turn to update the pulse width.

        This is called once every 20ms

        Args:
            _: required for a timer callback but not used here
        
        """
        for sector in Sector._sectorList:
            sector._nextPW()





    def __init__(self, name, pin, plate_pw, default_pos = 'M'):
        """Sector Plate Constructor

        This initiates the PWM driver on the assigned pin and 
        adds the sector plate to the Class static list.

        The parent device is set up with the device name and type ('s')

        Args:
            self:
            name:   The Sector plate name used throughout the application 
                to identify it.
            pin:    GPIO pin to be used to control the servo
            plate_pw: a dictionary containing servo pulse widths in ms for each position
            default_pos:    the key for the default position
        
        """
        self._pwmOut = PWM(Pin(pin)) # create PWM driver
        self._pwmOut.freq(50)        # 50Hz for servo
        time.sleep_ms(10)
        self._pwmOut.duty_ns(0)      # de energise servo
        self._plate_pw = plate_pw
        self._lastPW = plate_pw[default_pos] * 1000     # assume in main as normal position (nano seconds)
        self._state = Device.UNKNOWN       # unknown until a move is initiated
        self._targetCmd = default_pos # needs to be same as state initially
        self._value = default_pos

        if len(Sector._sectorList) == 0:
            # start timer if first one
            Sector._timer.init(period = Sector.TIMER_PERIOD, mode = Timer.PERIODIC, callback = Sector._timeStep)
        Sector._sectorList.append(self) # add this instance to the list
        # create device entry too
        super().__init__(name, 's')


    def _set_state(self, newState):
        """ Update the Sector plate state & publish completion event """
        #print("State", newState, self._state)
        self._state = newState
        if newState == Device.INDETERMINATE:
            self.report_event(Device.ACTION_INIT, newState)
        else:
            self.report_event(Device.ACTION_DONE, newState)
        

        # will do more later

    def get_state(self):
        """Get the state
        
        returns:
            the sector state """
        return self._state

    def value(self, cmd  = None):
        """Get the device value
        
        This this supersedes the method in the base class. Note if a sector move is currently in
        progess it will be quietly superseded by this one.
        
        args:
            self:
            cmd: the value associated with the command to be executed"""
        if cmd == None:
            return(self._value)
        
       
        #print ('Cmd',  cmd)
        try:
            self._targetPW = self._plate_pw[cmd] * 1000 # pulse width in nano secs
        except KeyError:
            #print('command not recognised: ', cmd)
            self.report_event(Device.ACTION_ERROR, cmd)
            return self._state
        if (self._state == Device.UNKNOWN) or (self._targetCmd != cmd):
            #move needed
            self._targetCmd = cmd
            #print(abs(self._targetPW - self._lastPW))
            if abs(self._targetPW - self._lastPW) > (Sector.LONG_THRESHOLD * 1000):
                travel_period = Sector.TRAVEL_PERIOD * 2
            else:
                travel_period = Sector.TRAVEL_PERIOD
            #print(travel_period)

            self._steps = Sector.SETTLE + travel_period // Sector.TIMER_PERIOD #number of steps to complete the move

            #print(self._steps, self._lastPW)
            self._pwmOut.duty_ns(self._lastPW)                
            self._set_state(Device.INDETERMINATE) # this publishes the state too
        else:
            pass



    def _nextPW(self):
        """
        It's time to change the pulse width
        """
        if (self._state != Device.INDETERMINATE):
            return      # nothing to do
        
        if (self._steps >= 0):
            #move still in progress - should not need to check step count!
            if (self._steps > Sector.SETTLE):
                self._lastPW = self._lastPW + ((self._targetPW - self._lastPW) // (self._steps - Sector.SETTLE))
                self._pwmOut.duty_ns(self._lastPW)
            


            elif (self._steps == Sector.SETTLE):
                    # allow to settle at target passwidth
                    self._pwmOut.duty_ns(self._targetPW)
            
            # must be settling!
                
                
            elif (self._steps == 0):
                # move complete
                    self._lastPW = self._targetPW
                    self._value = self._targetCmd
                    self._set_state(Device.SET) #update state & publish
                    self._pwmOut.duty_ns(0)       #stop pwm generation
            self._steps -= 1
        
        
   
        
if __name__ == '__main__':
    # create test sector object
    s = Sector('L1', 15, {'M':1240, 'L':1520, 'C':1845})
        


