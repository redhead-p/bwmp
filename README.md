# Blackwater Mud Pie

## Introduction

---

This contains MicroPython classes, functions and data for a micro Model Railway controlled by a Raspberry Pi Pico.

This layout features Tollesbury Pier Station.  Lying on the north bank of the Blackwater Estuary,
this was at the southern end of the Kelvedon and Tollesbury Light Railway until the station's closure in 1921. The scale is 1:480

Conventional drives mechanisms are difficult to engineer in a locomotive whose overall length at this
scale is about 16mm and so the propulsion mechanism
here is a magnetic linear motor which is controlled by a Raspberry Pi Pico. This also provides a simple
user interface for human operations.

## Modules

---

- battery - This module monitors the RP Pico supply voltage, the primary usage for this being when the Pico is battery powered (N.B this module is not integrated with the main application yet.)
- courier14 - Courier14
- device - This provides the Device class, a base class for hardware device drivers and similar objects.
- layout - This is the layout module. It sets up data structures that describe the layout. It is specific to Blackwater Mud Pie.
- layout_util - This provides utility classes for layout management and access to layout data structures including transits and routes.
- linearstepper - This module provides for the driving of the linear motor using a TI DRV8833 to generate the waveforms. It specifies the LinearMotor class and provides look up tables that specify the PWM duty cycles as 16 bit values.
- main - This is the top-level module for the Blackwater Mud Pie layout control and automation application.
- oled1_5 - This is the driver module for the 1.5" OLED Display. It defines the OLED class and constants associated with the display. This is a singleton class.
- popup - This module has classes for Menu and MenuItems so that simple menus can be built and displayed. Additionally it may provide other 'widgets' e.g. numeric input.
- relay - This module provides a single class - Relay - which is used to control relays connected to specific pins.
- screen - This is the screen application module. It specifies the Screen class. This contains code and data that is specific to Blackwater Mud Pie.
- screen_util - This provides utility classes for use in screen display functions, e.g. tiles and menus. The basic access the display is via tiles.
- sector - This module contains code associated with the sector plate. The sector plate is servo powered.
- user_in - User input is via a rotary encoder that incorporates a push button switch. Classes are provided to decode the rotary encoder switch and accept push button input.
