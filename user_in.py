"""User Input Module
    :author: Paul Redhead

 

User input is via a rotary encoder that incorporates a push button switch. Classes are provided to decode
the rotary encoder switch and accept push button input.


The rp2040 PIO peripherals are used debounce switch inputs.
It uses PIO state machines 1 & 2. 
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
from machine import Pin
import rp2

from device import Device
from micropython import const




@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, out_init = rp2.PIO.OUT_LOW)
def _debounce():
    """GPIO Debounce        

        Debounce a gpio.  This is based on the code at
        https://github.com/GitJer/Some_RPI-Pico_stuff/tree/main/Button-debouncer

        Explanation:

        - start with the assumption that the gpio is in a steady state. 
            If it is currently 1, then go to 'isone'# if it is currently 0, then go to 'iszero'

        - the branch of 'isone' works as follows:
            wait for a change to 0
            if that happens, set 31 into the x scratch register
            this is the amount of 'time' the debouncer will wait before switching over
            the actual amount of time is also dependent on the clock divisor
            the program keeps checking if the input changes back to 1, if so, start over at 'isone'
            if the input does not change back, complete the loop of counting down from 31
            if the x scratch register becomes 0, the signal has definitively switched to 0
            start from 'iszero'

        - the branch of 'iszero' works similarly, but note that a jmp pin statement always jumps on 1, not 0
        
         
        The state of the pin being monitored is 'pushed' into the FIFO buffer and should be read from the PIO state
        machine.
    """

  
    jmp  (pin, 'oneatfirst')   # executed only once: is the gpio currently 0 or 1?
    wrap_target()
    label('iszero')
    wait (1,  pin, 0)    # the gpio is 0, wait for it to become 1
    set  (x, 31)        # prepare to test the gpio for 31 * 2 clock cycles
    label('checkzero')
    # nop [31]      # possible location to add some pauses if longer debounce times are needed
                    # Note: also insert a pause right after 'checkone' below

    jmp  (pin, 'stillone') # check if the gpio is still 1
    
    jmp  ('iszero')      # if the gpio has returned to 0, start over
    label('stillone')
    jmp  (x_dec, 'checkzero')# the decrease the time to wait, or decide it has definitively become 1
    label('isone')

    #set  (y, 1)
    in_  (pins, 1)

    push ()
    irq( rel(0))
            
    label ('oneatfirst')
    wait (0, pin, 0)    # the gpio is 1, wait for it to become 0
    set  (x, 31)        # prepare to test the gpio for 31 * 2 clock cycles
    label('checkone')
    # nop [31]      # possible location to add some pauses if longer debounce times are needed
                    # Note: also insert a pause right after 'checkzero' above
    jmp  (pin, 'isone')   # if the gpio has returned to 1, start over
    jmp  (x_dec, 'checkone')# decrease the time to wait
    #set  (y, 0)
    in_  (pins, 1)

    push ()
    irq( rel(0))
    wrap ()

class QuadDecode(Device):
    """Quadrature Decode
    
    This class decodes quadrature device pin readings.  It's interrupt driven using pin inputs debounced
    by a PIO statemachine. Two state machines are used. Both run the _debounce program.
     
    The PIO state machine numbers are hardwired! 

    Attributes:
        PERIOD_MS: time (ms) at same level to indicate contact bouncing over
    """



    # class constants

    PERIOD_MS  = const(2)

    
   

    def __init__(self,name, pin_a, pin_b):
        """Construct the quadrature decoder

        Pins are allocated for the assigned numbers and configured as inputs with pull ups enabled.

        PIO state machines are allocated and loaded with the debounce code and linked to ISRs.
         
        Args:
            self:
            name:   the device name - string
            pin_a:  encoder A channel pin number 
            pin_b:  encoder B channel pin number
             """
        self._qa = Pin(pin_a, Pin.IN, pull = Pin.PULL_UP)
        self._qb = Pin(pin_b, Pin.IN, pull = Pin.PULL_UP)

        self._freq = int(1000/(QuadDecode.PERIOD_MS/62))

        self._sma = rp2.StateMachine(0, _debounce, freq= self._freq, in_base = self._qa, jmp_pin = self._qa)
        self._smb = rp2.StateMachine(1, _debounce, freq= self._freq, in_base = self._qb, jmp_pin = self._qb)

        # set the state machine ISRs
        self._sma.irq(self._qdec_irs_a)
        self._smb.irq(self._qdec_irs_b)

        # initialise decode state variables
        self._lrmem = 3
        self._lrsum = 0

        # create device entries too
        super().__init__(name, 'q')

        # Finally start the StateMachines
        self._sma.active(True)
        self._smb.active(True)


    def _qdec_irs_a(self, sm):
        if sm.get() == 0 and self._qb() == 0:
            # -1 for counter clockwise
            self.report_event(Device.UI_QUAD, -1)

    def _qdec_irs_b(self, sm):
        if sm.get() == 0 and self._qa() == 0:
            # 1 for clockwise
            self.report_event(Device.UI_QUAD, 1)

       
    

    


class Switch(Device):
    """Switch Input class
    
    This class takes an input from a switch. The switch output is assumed true if low. I.e the input is
    held high by the pull up if the switch is off.

    It's interrupt driven using an input pin debounced
    by a PIO statemachine running the _debounce program.

    Attributes:
        S_PERIOD_MS: time (ms) at same level to indicate contact bouncing over.

    """

    S_PERIOD_MS  = const(30)


    def __init__(self,name, pin_num):
        """Construct the switch object

        The pin is configured as an input with pull up enabled.

        A PIO state machine is allocated and loaded with the debounce code and linked to ISR the ISR.
        
        Args:
            self:
            name:   the device name - string
            pin_num:  switch pin number
            """
        self._pin = Pin(pin_num, Pin.IN, pull = Pin.PULL_UP)
        self._freq = int(1000/(Switch.S_PERIOD_MS/62))

        self._sm = rp2.StateMachine(3, _debounce, freq= self._freq, in_base = self._pin, jmp_pin = self._pin)

        # set the state machine ISRs
        self._sm.irq(self._switch_irs)





        # create device entries too
        super().__init__(name, 'u')

        self._sm.active(True)

    def _switch_irs(self, sm):
        self.report_event(Device.UI_SWITCH, sm.get())




if __name__ == '__main__':
    # create test sector object
    q = QuadDecode('QUI', 2, 3)
    s = Switch('SW1', 4)

    import time
    time.sleep_ms(2000)
    
    while True:
        time.sleep_ms(1)
        print(Device.get_event_report())


        






