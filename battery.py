"""Battery Monitor Module
    :author: Paul Redhead

This module monitors the RP Pico supply voltage, the primary usage for this being
when the Pico is battery powered.

On the standard Pico GPIO29 is connected to Vsys
via a 3 to 1 voltage divider. I.e a maximum analogue reading corresponds to 9.9V 
supply voltage. GPIO29 is not exposed on the standard Pico board so is not used for
any other purpose.

"""
"""
        Copyright (C) 2024 Paul Redhead

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

from micropython import const
from machine import Pin, ADC, Timer


from device import Device


_ADC_MAX = const(65535) # maximum ADC reading
_V_MAX_MV = const(9900)        # Vsys in mV corresponding to _ADC_MAX
_FILTER_FACTOR = const(10)     # Simple Infinite Impulse Response Filter Factor


SAMPLE_PERIOD = const(10000)
""" Battery Voltage Sample Period

The period between successive battery voltage samples (ms).
"""

class BatteryMonitor(Device):
    """Battery Monitor
    
    There is a single instance of this class.  It monitors Vsys/3 as available on GPIO 29 on a standard
    Pico board.

    Readings are taken periodically. They are filtered using a simple Infinite Impulse Response
    digital filter according to the following formula.

    y[k] = w * x[k] + (1 - w) * y[k-1]

    - y[k] is the output of this iteration.
    - x[k] is the input to this iteration (the current reading).
    - w is a positive fractional weighting less than one.
    - y[k-1] is the output of the preceding iteration.

    
    The actual implementation employs an equivalent to this but adjusted to use integer arithmetic with
    no loss of precision. The value _FILTER_FACTOR in the actual implementation is given by 1/w. As
    _FILTER_FACTOR is an integer, w has to be constrained accordingly. It must be expressible as 1/n
    where n is an integer.

    """
    _battery = None

    @classmethod
    def get_instance(cls):
        """Return the singleton instance

        The singleton is created on the first call.
        
        args:
            cls:
            """
        if cls._battery == None:
            cls._battery = BatteryMonitor()
        return cls._battery
        
    def __init__(self):
        """Battery Monitor Constructor
        
        This sets up pin 29 for analogue (ADC) input. The IIR filter accumulator is initialised by summing
        a number of readings corresponding to the filter factor.
        
        The timer is initialised."""
        super().__init__('B1', 'b')
        self._adc = ADC(Pin(29))
        self._filter_acc = 0    # filter accumulator
        for _ in range(_FILTER_FACTOR): # set the accumulator based on the current value
            self._filter_acc += self._adc.read_u16()
        self._timer = Timer(mode = Timer.PERIODIC, period = SAMPLE_PERIOD, callback = self._next_sample)

    def _next_sample(self,_):
        """Next Reading Due Callback
        
        When the next sample is due the ADC is read. The Accumulator is multiplied by
        FILTER_FACTOR - 1/FILTER_FACTOR and then the current reading is added in. This gives
        a rolling sum.  The rolling average may be determined by dividing by the FILTER_FACTOR.

        Integer arithmetic is used. Results of division are rounded to nearest integer rather
        than rounded down.

        args:
            self:
            _: timer ID (ignored)
        """
        self._filter_acc = ((self._filter_acc * (_FILTER_FACTOR - 1) + (_FILTER_FACTOR//2))
            // _FILTER_FACTOR) + self._adc.read_u16()
        
        # convert the rolling sum to millivolts
        self._mv = ((self._filter_acc * _V_MAX_MV) + (_ADC_MAX * _FILTER_FACTOR // 2)) \
            // (_ADC_MAX * _FILTER_FACTOR)
        print(self._mv)

        