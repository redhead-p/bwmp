"""Screen Module
    :author: Paul Redhead

 
This is the screen application module.  It specifies the Screen class. This contains code and data that
is specific to Blackwater Mud Pie.

Generally it provides application specific access to the display. It knows about application objects and events etc.
and how they are managed on screen.

It specifies menus, menu items and other popups.
"""
"""       Copyright 2023, 2024  Paul Redhead

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



# lib imports
from layout_util import TransitHelper, Route, RouteTable
from screen_util import Tile, Section
from device import Device
from popup import MenuItem, Menu, NumberIn
from linearstepper import LinearMotor


LAYOUT_SECTION = {
    'SecM':Section(3,37,    array('h', [0,  5, 25, 5, 25, 0,  0,  0])),
    'SecL':Section(1,26,    array('h', [3, 15, 25, 3, 23, 0, 0, 11])),
    'SecC':Section(1,18,    array('h', [4, 23, 19, 3, 15, 0, 0, 20])),
    'Loco':Section(27,25,   array('h', [0, 5,  15, 5, 15, 0,  0,  0, -1, 1])),
    'Coach':Section(21,15,  array('h', [0, 5, 25, 5, 25, 0,-3, 0, -5, 2])),
    'Link':Section(29,37,   array('h', [0, 5, 20, 5, 20, 0, 0, 0])),
    'StnU':Section(49,37,   array('h', [0, 5, 15, 5, 15, 0, 0, 0])),
    'StnM':Section(65,37,   array('h', [0, 5, 29, 5, 29, 0, 0, 0])),
    'StnD':Section(95,37,   array('h', [0, 5, 15, 5, 15, 0, 0, 0])),
    'Ends':Section(110,37,  array('h', [0, 5, 15, 5, 15, 0, 0, 0])),
    'RunRnd':Section(49,37, array('h', [0, 5, 15, 15, 46, 15, 62, 5,62, 0,
                                        60, 0, 46, 10, 15, 10, 2, 0, 0, 0]))
           }
"""Layout Track section shapes

For each track section this specifies the display position on the framebuffer and
the x, y coordinates of the points used for the framebuf poly function.

In the co-ordinate list for a section there is alway a 0 x and a 0 y.  Each section's
display position is its top left corner.

The overall image is 126 pixels wide and 52 high.
"""


class Screen():
    """This class provides the screen application.
    
    It deals with the application events that
    require display on the screen or other actions (e.g. UI menu/data)

    It's a singleton.

    The screen is divided into base areas (Tiles).
    The contents of these areas are updated in line with events received. User interactions
    are conducted using modal pop-ups (e.g. menus etc). When a pop-up is displayed writing base tiles to the 
    screen is deferred until the pop-up is closed. If no pop-up is displayed base tiles are written to the 
    screen following the Tile being updated. On screen base tiles are refreshed when a pop-up is closed.
    """

    _scrn = None # this will be set to the singleton object on instantiation

    _TRANSIT_SERVICE = 'KTLR'
    _RESTART_TRANSIT = "MD"


    


    @classmethod
    def get_instance(cls):
        """Return the singleton instance

        The singleton is created on the first call.
        
        args:
            cls:
            """
        if cls._scrn is None:
            cls._scrn = Screen()
        return cls._scrn
        

    def __init__(self):
        """Screen Initialiser
        
        This displays the start up splash.
        
        It sets up the tile to hold the layout but it's not displayed at this time.
        """
        if (Screen._scrn) != None and (Screen._scrn is not self):
            raise RuntimeError ('Only one Screen object possible')
        
        self._menu_list = [MenuItem('Transits',self._transit_menu,(), False),
                   MenuItem('Routes', self._route_menu, (), False),
                   MenuItem('Motor', self._get_motor_steps, (), False)]      
        """Start Menu Item List

        This holds the start menu. It comprises as list of menu items."""

        # temporay splash tile
        t = Tile(128, 64)
        t.fill(0)
        t.courier_text('   Blackwater',0,0,1)
        t.courier_text('     Mud Pie',0,16,1)
        t.show(0, 0)

        self._pop_up = None # no menu or pop_up loaded at start

        self._layout_disp = Tile(128, 64)
        for k in LAYOUT_SECTION.keys():
            LAYOUT_SECTION[k].draw(self._layout_disp,1)
        self._layout_disp.show(0,64)

        self._action_disp = Tile(128, 32)
        self._action_disp.fill(0)

        # list of tiles to be refreshed after pop up / menu display &  x, y coords
        self._refresh_list = [(self._layout_disp,0 ,64),(self._action_disp, 0 ,0)]

        # temp clear tile
        t2 = Tile(128, 64)
        t2.fill(0)
        self._refresh_list.append((t2, 0, 0))

        # the transit service (manages a collection of transits)
        self._transit_service = TransitHelper.get_service(Screen._TRANSIT_SERVICE)
        self._route_table = RouteTable.get_instance()


    def show_event(self, report):
        """Show an event report
        
        This updates the screen with the event.  Other application actions on events are 
        dealt with elsewhere.

        Args:
            self:
            report: a tuple containing the reference to the source object, the unique event code see: display
                and additional information - format and content event specific
        """
    
        (source, event, data) = report

        # call the handler for this event type
        try:
            # call the handler associated with the source object type of the event
            (REPORT_DECODE[source.get_type()])(self,source, event, data)
        except KeyError:
            # pop up event message 
            t = Tile(128, 20)
            t.fill(0)
            t.courier_text(f'Event {source.get_name()} {event} {data}',0,1)
            t.show(0,0)

    def transit_done(self):
        """Transit Completed
        
        If the next transit is set build the transit menu
        
        args:
            self:
        """
        
        if self._transit_service.get_current_transit() is not None:
            self._transit_menu()

                           

    def _sector_event(self, sector, event, data):
        if event == Device.ACTION_INIT:
            # remove current dispays
            for value in SECTOR_SECTIONS.values():
                value.draw(self._layout_disp, 0)
        elif event == Device.ACTION_DONE:
            SECTOR_SECTIONS[sector.value()].draw(self._layout_disp,15)
        if self._pop_up is None:
            self._layout_disp.show(0, 64)

    def _relay_event(self, source, event, data):
        name = source.get_name()
        if event == Device.ACTION_DONE:
            # see if relay set
            if data == 1:
                for x in RELAY_SECTION_NAMES[name]:
                    LAYOUT_SECTION[x].draw(self._layout_disp,15)
            if self._pop_up is None:
                self._layout_disp.show(0, 64)
        elif event == Device.ACTION_INIT:
            for x in RELAY_SECTION_NAMES[name]:
                LAYOUT_SECTION[x].draw(self._layout_disp,1)
        

    def _motor_event(self, _, event, data):
        if event == Device.ACTION_INIT:
            dir, speed = data
            transit = self._transit_service.get_current_transit()
            self._action_disp.fill(0)
            if transit is not None:
                name = transit.get_name()
            else:
                name = '<no transit>'
            self._action_disp.courier_text(name, 0 ,0 ,1)
            self._action_disp.courier_text('Up' if dir == LinearMotor.UP else 'Dn', 0, 16, 1)
            self._action_disp.courier_text(('Slow','Medium','Fast')[speed], 32, 16, 1)
        elif event == Device.ACTION_DONE:
            self._action_disp.fill(0)
            self._action_disp.courier_text('Stopped', 0, 16, 1)
        else:
            self._action_disp.courier_text('Error', 0, 0, 4)
        if self._pop_up is None:
            self._action_disp.show(0, 0)



    def _button_event(self, _, event, data):
        # events are either button pressed (data = 0) or released (data = 1)
        # at the moment we only deal with pressed here but if a menu is loaded it gets both
        
        if self._pop_up is None:
            if data == 0:
                if Device.by_name('L1').get_state() == LinearMotor.STOP:

                    # create start menu
                    self._pop_up = Menu('Start', self._menu_list)
                    # and display it
                    self._pop_up.build()
 
        else:
            # pass the button event on to the menu
            if self._pop_up.button(data):
                # menu exited so let the gc at it and refresh the main tiles
                self._pop_up = None
                for item in self._refresh_list:
                    tile, x , y = item
                    tile.show(x, y)

    def _route_menu(self):
        current_name = self._route_table.get_current_route_name()
       
        items = [MenuItem(name + '*' if current_name == name else name,
                  self._route_table.set_route_by_name,(name if current_name != name else '_',))
                   for name in self._route_table.get_names() if name != '_']
       
        self._pop_up = Menu('Routes',items)
        self._pop_up.build()

    def _transit_menu(self):

        transit = self._transit_service.get_current_transit()  # this may return None


        if transit is None:
            transit = self._transit_service.set_transit(Screen._RESTART_TRANSIT) # set main down as first Move
        
        items = [MenuItem(transit.get_name(),transit.run, (), True),
                 MenuItem("Restart",self._transit_service.set_transit,((Screen._RESTART_TRANSIT,)))]
        self._pop_up = Menu("Transits",items)
        self._pop_up.build()
        
        
    def _get_motor_steps(self):

        lm = Device.by_name('L1')
        self._pop_up = NumberIn('Cycles', 100, -100, lm.move)
        self._pop_up.build()


    def _q_decode_event(self, name, event, data):
        try:
            self._pop_up.quad_decode(data)
        except:
            pass
            #print(Exception)
        

        

REPORT_DECODE = {'s':Screen._sector_event,
                'r':Screen._relay_event,
                'l':Screen._motor_event,
                'u':Screen._button_event,
                'q':Screen._q_decode_event}
"""Report Decode

This dictionary associates the report type with the screens bound method that handles that report."""




SECTOR_SECTIONS = { 'M': LAYOUT_SECTION['SecM'],
                    'L' : LAYOUT_SECTION['SecL'],
                    'C' : LAYOUT_SECTION['SecC']}
"""Sector Sections

This dictionary links the sector table position with the layout section to be displayed."""



RELAY_SECTION_NAMES = {'R1':('Link', 
                        'StnU',
                        'StnM',
                        'StnD',
                        'Ends'),
                  'R2':('Link',
                        'Coach',
                        'StnU',
                        'StnD',
                        'Ends'),
                  'R3':('Link',
                        'Loco',
                        'RunRnd',
                        'Ends')}
"""Relay Section Names

This dictionary associates relays with the track sections that are energised when the relay is on."""
    
    

if __name__ == '__main__':
    from user_in import QuadDecode, Switch
    # create OLED and logical screen
    _s = Screen.get_instance()
    # test menu
    _q = QuadDecode('QUI', 2, 3)
    """ Quadrature decoder """

    _u = Switch("SW1", 4)


    while True:
        _s.show_event(Device.get_event_report())


