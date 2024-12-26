"""Route Module
    :author: Paul Redhead



This is the layout module.  It sets up data structures that describe the layout. It is specific to 
Blackwater Mud Pie.

.. image:: diags/CakeTrack.pdf
    :width: 800px


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

from linearstepper import LinearMotor
from layout_util import Transit, Route



SECTOR_POSITION = {'M':1245, 'L':1520, 'C':1845}
"Sector Plate Positions look up giving servo pulse width in micro seconds."

SECTOR_DEFAULT = 'M'
"Sector Plate Default (Start of day) position."


ROUTE_TABLE = {"Main":Route((('S1', 'M'), ('R2', 0), ('R3', 0), ('R1', 1))),
            "MainX":Route((('S1', 'M'), ('R1', 0), ('R3', 0), ('R2', 1))),
            "RR":   Route((('S1', 'M'), ('R1', 0), ('R2', 0), ('R3', 1))),
            "Coach":Route((('S1', 'C'), ('R1', 0), ('R3', 0), ('R2', 1))),
            "CoachX":Route((('S1', 'C'), ('R2', 0), ('R3', 0), ('R1', 1))),
            "Loco": Route((('S1', 'L'), ('R1', 0), ('R2', 0), ('R3', 1))),
            "LocoX": Route((('S1', 'L'), ('R3', 0), ('R2', 0), ('R1', 1))),
            "_":  Route((('S1', 'M'), ('R1', 0), ('R2', 0), ('R3', 0)))}
"""The Route Table

Each route has a name (index to the dictionary) and a list of device commands required to put the route into 
effect.  Index '_' clears the route.

N.B relays to be set are at end of tuple list so that any set relays are cleared first
"""

    


TRANSIT_TABLE ={"MD":Transit("Main Down", "Main", False, True, LinearMotor.MEDIUM, 33, "R1", False),
                 "R1":Transit("Decouple Loco", "MainX", True, True, LinearMotor.SLOW, 10, "R2", False),
                 "R2":Transit("Run Round", "RR", True, True, LinearMotor.SLOW, -32, "R3", False),
                 "R3":Transit("Couple Loco", "MainX", True, True, LinearMotor.SLOW, 10, "MU", False),
                 "MU":Transit("Main Up", "Main", True, False, LinearMotor.MEDIUM, -30, "C1"),
                 "C1":Transit("Coaches -> CS", "Coach", False, False, LinearMotor.FAST, 9, "C2"),
                 "C2":Transit("Decouple Loco", "CoachX", False, False, LinearMotor.FAST, -2, "L1"),
                 "L1":Transit("Loco -> LS", "Loco", False, False, LinearMotor.FAST, 5, "C3"),
                 "C3":Transit("Coaches -> SP", "Coach", False, False, LinearMotor.MEDIUM, -10, "L2"),
#                 "L2":Transit("Couple Loco", "LocoX", False, False, LinearMotor.MEDIUM, 1, "L3"),
                 "L2":Transit("Loco -> SP", "Loco", False, False, LinearMotor.MEDIUM, -4, "M0"),
                 "M0":Transit("Park","Main",False,False,LinearMotor.SLOW,0, None)
                 }
"""Table of Transits

This dictionary sets up the details the transits using the Transit Class to do so.

:see: Transit for constructor parameters.
"""

