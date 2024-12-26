"""Main Module 
    :author: Paul Redhead


This is the top-level module for the Blackwater Mud Pie layout control and automation application.

It instantiates device driver objects for linear motor, sector plate and
track power relays.

It sets up the user interface. The Quadrature Decoder and Switch objects are instantiated.
The screen driver singleton object is instanticated on demand using <Class>.get_instance().
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

# micropython imports
from micropython import const

# application imports
from layout_util import TransitHelper, RouteTable
from layout import SECTOR_POSITION, SECTOR_DEFAULT, TRANSIT_TABLE, ROUTE_TABLE


# application lib imports
from user_in import QuadDecode, Switch
from sector import Sector
from linearstepper import LinearMotor
from relay import Relay
from device import Device
from screen import Screen


# hardware pin allocations

AIN1_PIN = const(16)
"""DRV8833 Winding A pin1"""

AIN2_PIN = const(17)
"""DRV8833 Winding A pin2"""
    
BIN1_PIN = const(18)
"""DRV8833 Winding B pin1"""

BIN2_PIN = const(19)
"""DRV8833 Winding B pin2"""

SLEEP_PIN = const(26)
"""DRV8833 Sleep"""

SECTOR_SERVO_PIN = const(15)
"""Sector Servo motor pin"""

RELAY1_PIN = const(20)
"""Relay 1"""
RELAY2_PIN = const(21)
"""Relay 2"""
RELAY3_PIN = const(22)
"""Relay 3"""


# instantiate device drivers

sector = Sector('S1', SECTOR_SERVO_PIN, SECTOR_POSITION, SECTOR_DEFAULT)
"""The Sector Plate

    This is driven by a servo.

    The servo pulse widths for the sector plate postitions are in layout.py
"""


lm = LinearMotor('L1', AIN1_PIN, AIN2_PIN, BIN1_PIN, BIN2_PIN, SLEEP_PIN)
"""The Linear Motor

===========  ====================
  Pin        DRV8833 Pin
===========  ====================
AIN1_PIN     Winding A pin1
AIN2_PIN     Winding A pin2
BIN1_PIN     Winding B pin1
BIN2_PIN     Winding B pin2
SLEEP_PIN    Sleep (low for true)
===========  ====================

"""

r1 = Relay('R1', RELAY1_PIN)
""" photovoltaic relay pair 1"""
r2 = Relay('R2', RELAY2_PIN)
""" photovoltaic relay pair 2"""
r3 = Relay('R3', RELAY3_PIN)
""" photovoltaic relay pair 3"""

q = QuadDecode('QUI', 2, 3)
""" Quadrature decoder on pins 2 & 3"""

u = Switch("SW1", 4)
""" User switch (quadrature press button) pin 4"""

# instantiate application objects




ts = TransitHelper('KTLR', TRANSIT_TABLE)
""" Transit Service

This service comprises a collection of transits.
"""

rt = RouteTable(ROUTE_TABLE)
""" Route Table lookup"""

s = Screen.get_instance()
""" User Interface Screen"""    


def main():
    """ Core 0 Main
    
    At the moment only core 0 is used.
    It monitors for events which are passed to
    
     - the transit controller for action
     - the screen so it can be updated.
    """

    ts.set_callback(s.transit_done)



    while True:
        report = Device.get_event_report()

        ts.process_event(report)

        s.show_event(report)


if __name__ == '__main__':
    main()
