"""Linear Motor Module
    :author: Paul Redhead



This module provides for the driving of the linear motor using a TI DRV8833 to generate the 
waveforms.
It specifies the LinearMotor class and provides look up tables that specify the PWM duty cycles as 
16 bit values.

The linear stepper is like a 2 phase stepper motor. There are windings for each phase
which are controlled independently.  

The DRV8833 has two H bridges designated A & B.  Each H bridge has two connections designated 1 and 2.

The two phases overlap with effectively 90 degrees between the values. 
We use micro stepping.  
A full step corresponds to the complete transfer of power from one phase to the next.
Microstepping PWM factors are calculated in an external spreadsheet.
It has tables for full, half, quarter, eighth and sixteenth stepping modes.
Only the active table is included here.


The look up table converts the micro step value to PWM 16 bit duty cycle values for each of the 
four DRV8833 inputs.  Note that the DRV8833
inputs are low for true so the values here are inverted for brake/slow decay PWM modes.
Each 'revolution' comprises four 
steps and so a table for eighth microsteps has 32 sets of values in total.  Also only
one of each pair of inputs has PWM active at any time.  The other is set for the maximum
duty cycle.


"""
"""
        Copyright (C) 2023, 2024 Paul Redhead

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
from math import sqrt

# micropython imports
from machine import Pin, PWM, Timer
from micropython import const

# /lib imports
from device import Device



PWM_LU = ((19195, 65535, 19195, 65535),
(14876, 65535, 23960, 65535),
(11045, 65535, 29126, 65535),
(7738, 65535, 34642, 65535),
(4989, 65535, 40456, 65535),
(2822, 65535, 46511, 65535),
(1259, 65535, 52750, 65535),
(316, 65535, 59111, 65535),
(0, 65535, 65535, 65535),
(316, 65535, 65535, 59111),
(1259, 65535, 65535, 52750),
(2822, 65535, 65535, 46511),
(4989, 65535, 65535, 40456),
(7738, 65535, 65535, 34642),
(11045, 65535, 65535, 29126),
(14876, 65535, 65535, 23960),
(19195, 65535, 65535, 19195),
(23960, 65535, 65535, 14876),
(29126, 65535, 65535, 11045),
(34642, 65535, 65535, 7738),
(40456, 65535, 65535, 4989),
(46511, 65535, 65535, 2822),
(52750, 65535, 65535, 1259),
(59111, 65535, 65535, 316),
(65535, 65535, 65535, 0),
(65535, 59111, 65535, 316),
(65535, 52750, 65535, 1259),
(65535, 46511, 65535, 2822),
(65535, 40456, 65535, 4989),
(65535, 34642, 65535, 7738),
(65535, 29126, 65535, 11045),
(65535, 23960, 65535, 14876),
(65535, 19195, 65535, 19195),
(65535, 14876, 65535, 23960),
(65535, 11045, 65535, 29126),
(65535, 7738, 65535, 34642),
(65535, 4989, 65535, 40456),
(65535, 2822, 65535, 46511),
(65535, 1259, 65535, 52750),
(65535, 316, 65535, 59111),
(65535, 0, 65535, 65535),
(65535, 316, 59111, 65535),
(65535, 1259, 52750, 65535),
(65535, 2822, 46511, 65535),
(65535, 4989, 40456, 65535),
(65535, 7738, 34642, 65535),
(65535, 11045, 29126, 65535),
(65535, 14876, 23960, 65535),
(65535, 19195, 19195, 65535),
(65535, 23960, 14876, 65535),
(65535, 29126, 11045, 65535),
(65535, 34642, 7738, 65535),
(65535, 40456, 4989, 65535),
(65535, 46511, 2822, 65535),
(65535, 52750, 1259, 65535),
(65535, 59111, 316, 65535),
(65535, 65535, 0, 65535),
(59111, 65535, 316, 65535),
(52750, 65535, 1259, 65535),
(46511, 65535, 2822, 65535),
(40456, 65535, 4989, 65535),
(34642, 65535, 7738, 65535),
(29126, 65535, 11045, 65535),
(23960, 65535, 14876, 65535),)
"""
Stepper look up table.

A complete 'revolution' or cycle requires four steps so the number of rows is the number of microsteps * 4.
The table is generated externally using a spreadsheet. The numbers here are 65535 - x as the PWM outputs
low for true. I.e we specify the off value of the PWM duty cycle rather than the on value.
"""

class LinearMotor(Device):
    """Linear motor driver using a TI DRV8833.
   
    This class specifies the driver for the linear motor using the DVR8833. It inherits 
    from the general Device class.

    The motor driver is asynchonous and non blocking with periodic activities scheduled using
    a timer.  Methods return immediately and command execution completion is reported using
    the Device event reporting mechanism.

    Attributes:
        DOWN: direction Down (increasing mileposts - increasing step counts)
        UP:  direction Up (decreasing mileposts - decreasing step counts).
        STOP: motor stopped  
        SLOW:       about 4 scale m.p.h.
        MEDIUM:   about 10 scale m.p.h.
        FAST:  about 25 scale m.p.h.
        PWM_FREQ: PWM frequency in Hz
        BUSY:  motor busy (dir != STOP)

    
    """
    # class constants
    DOWN = const(1)         # direction Down (increasing mileposts)
    UP = const(-1)          # direction UP (decreasing mileposts)
    STOP = const(0)         # stopped
    SLOW = const(0)         # about 4 scale mph
    MEDIUM = const(1)       # about 10 scale mph
    FAST = const(2)         # about 25 scale mph
    BUSY = const(1)         # motor busy (dir != STOP)


    PWM_FREQ = const(250)

    
    _accel_rate = 4 # micro steps per second per second
    _decel_rate = 6 # micro steps per secoed per second

    _usteps_per_step = len(PWM_LU)//4  # number of microsteps per step

    # speeds in micro steps per second - integers
    _uspeeds = (5 *  _usteps_per_step // 2, 6 *  _usteps_per_step, 31 *  _usteps_per_step // 2)

    def __init__(self, name, a1_pin, a2_pin, b1_pin, b2_pin, sleep_pin):
        """Linear Motor Constructor
        
        This sets up the four PWM pins. The base device is set up with the name and type.
        
        Args:
            self:
            name:   Device name - string
            a1_pin: pin number for winding a output 1
            a2_pin: pin number for winding a output 2
            b1_pin: pin number for winding b output 1
            b2_pin: pin number for winding b output 2
            """
        self._dir = LinearMotor.STOP
        self._ustep = 0 # microstep counter - held modulo number of microsteps in step look up table
        
        self._windings = [PWM(Pin(a1_pin)), PWM(Pin(a2_pin)),
                            PWM(Pin(b1_pin)), PWM(Pin(b2_pin))]
        
        for pwm in self._windings:
            pwm.freq(LinearMotor.PWM_FREQ)

        self._set_windings()
        self._sleep = Pin(sleep_pin, Pin.OUT, value = 1 ) # 0 for sleep, 1 for awake
        self._step_timer = Timer()  
        super().__init__(name,'l') #construct device with type l

        
    def _set_windings(self):
        winding = iter(self._windings)
        for duty in  PWM_LU[self._ustep]:
            next(winding).duty_u16(duty)
  

    def _micro_step(self):
        self._ustep += self._dir
        try:
            self._set_windings() 
        except IndexError:
            self._ustep %= len(PWM_LU)
            self._set_windings()  


    def get_dir_speed(self):
        """Get the direction and speed
        
        Expose the directions and speed in a tuple.
        

        Args:
            self:

        Returns:
            direction (up, down or stop) & speed
        """
        return self._dir, self._speed
    
    def get_state(self):
        """Get State
        
        This overrides the get_state in the base class
        
        Returns:
            BUSY if motor running otherwise STOP"""
        return LinearMotor.STOP if self._dir == LinearMotor.STOP else LinearMotor.BUSY
    

    def _set_next_step(self):
        """ work out the time to the next step in ms and initialise the timer"""

        # time to next step if no accel or braking
        nxt_period = round(1000/LinearMotor._uspeeds[self._speed])

        if self._brake: 
            # work out if we need to be braking
            #
            # have we already worked out the brake time for this step
            t0 = sqrt(2 * self._us_togo / LinearMotor._decel_rate) if self._brake_time == None else self._brake_time
            # and the time for the next step
            t1 = sqrt(2 * (self._us_togo - 1) / LinearMotor._decel_rate)
            
            self._brake_time = t1 # save for next iteration
            braking = (t0 - t1) > nxt_period  # set flag if braking
            nxt_period = max(nxt_period, round((t0 - t1) * 1000)) # take the longer time for the next step
        else:
            braking = False

        # only process acceleration if not braking
        if (not braking) and self._accel:
            t1 = sqrt(2 * (self._us_start - self._us_togo + 1) / LinearMotor._accel_rate)  # calculate time for next micro step
            nxt_period = max(nxt_period, round((t1 - self._accel_time) * 1000)) # take the longer time for the next step
            self._accel_time =  t1   # save time for next iteraion
        self._step_timer.init(mode = Timer.ONE_SHOT,
                               period = nxt_period,
                               callback = self._us_cb)
 
    def _us_cb(self, _):
        """
        Step timer callback.
        The next step is due.
        """
        self._micro_step()
        self._us_togo -=  1
        if self._us_togo > 0:
            self._set_next_step()
        else:
            self._dir = LinearMotor.STOP
            self.report_event(Device.ACTION_DONE,self._dir)


    def move(self, cycle_count, accel = True, brake = True, speed = MEDIUM):
        """Move
        
        Move stock on the linear motor by a number of cycles. A cycle is a complete iteration through
        the PWM lookup table  and so the output is returned to the initial 
        phasing. It represents four steps and we always move in 4 step cycles.
        Each move is a multiple of 6mm. The speed may be specified.
        Braking may be applied at the end of move and acceleration at the beginning.
        
        Args:
            self:
            cycle_count: number of four step cycles to move. +ve for 'Down' moves, -ve for 'Up' moves.
            accel: boolean - acceleration at start is applied if true
            brake: boolean - braking is applied at end of move if true
            speed: one of SLOW, MEDIUM or FAST
        """
        
        assert ((speed in (LinearMotor.SLOW, LinearMotor.MEDIUM, LinearMotor.FAST)), f'Invalid Speed Option')
        if cycle_count == 0:
            # nothing to do 
            self.report_event(Device.ACTION_DONE, LinearMotor.STOP)
            return

        self._speed = speed
        self._accel = accel
        self._brake = brake

        if (cycle_count > 0):
            # cycle count +ve so going Down (increasing mileposts)
            self._dir = LinearMotor.DOWN
        else:
            # cycle count -ve so going Up (decreasing mileposts)
            self._dir = LinearMotor.UP

        self.report_event(Device.ACTION_INIT, (self._dir, self._speed))

        # calculate number of micro steps to go
        self._us_togo = abs(cycle_count) * LinearMotor._usteps_per_step * 4
        self._us_start = self._us_togo
        self._brake_time = None # time to decelerate - None - will be computed if needed.
        self._accel_time = 0    # time under acceleration so  far

        self._set_next_step()   # set timer to expire when next (first) step due


if __name__=='__main__':

    lm = LinearMotor('L1', 16, 17, 18, 19, 26)

