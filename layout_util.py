"""Screen Utility Module
    :author: Paul Redhead



This provides utility classes for layout management and access to layout data structures including 
transits and routes.


"""
"""
        Copyright 2024 Paul Redhead

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
from device import Device
#from transit import Transit

class RouteTable:
    """The Route Table
     
     This is a singleton class to provide access to the route table.
    """
    _route_table = None

    @classmethod
    def get_instance(cls):
        return cls._route_table

    def __init__(self, route_dict):
        if RouteTable._route_table is None:
            RouteTable._route_table = self
        else:
            # enforce route table as a singleton
            raise RuntimeError ('Only one route table possible')
        self._route_lu = route_dict

        self._current_route_name = None



    def set_route_by_name(self, name):
        """Set Route by Name
        
        The set route function is set for the named route
        
        Args:
            self:
            name: the name of the route as a string as used as the key in the route dictionary.
            """
        self._route_lu[name].set_route()
        self._current_route_name = name if name != '_' else None

    def get_route_by_name(self, name):
        """Get Route by Name
        
        Get the route object for the named route

        This will throw an exception if the route doesn't exist. To be handled
        (or not) by the calling code.
        
        Args:
            self:
            name: the name of the route as a string as used as the key in the route dictionary.

        Returns:
            The route object
            """
        return self._route_lu[name]


    
    def get_current_route_name(self):
        """Get name of current route
        
        Args:
            self:
            
        Returns:
            the current route name (string)
        """
        return self._current_route_name
    
    
    def get_names(self):
        """Get Route Names
        
        This returns the route names which are held
        as dictionary keys
        
        Returns:
            List of route names(strings)
            """
        return self._route_lu.keys() 
    
class Route:
    """The Route Class
    
    This class defines layout routes.  A route needs to be activated to permit movement.
    This is done by activting one of the relays that controls which track segments are powered up and the
    setting the sector plated in a specific position.
    
    Methods are provided to initiate setting a route and confirming that a route has been set and to return 
    the linear motor associated with the route.  At the moment there is only one so this can be hard coded.
    
    Class methods allow a route to be set by name. """


    def __init__(self,device_commands):
        """Initialise the route
        
        This saves the device commands that need to be issued to set the route up.
        These are sector table and relay setting commands.
        
        Args:
            device_commands: A list of device commands.  Each command is a tuple specifying the device name and
                containing an embeded tuple to be passed as parameters to the device's value() method.
            """      
        self._device_commands = device_commands


    def get_motor(self):
        """Get Linear Motor
        
        Get the linear motor associated with this route. There's only one at the moment.

        Args:
            self:

        returns:
            reference to the linear motor object.
        """
        return  Device.by_name("L1") # the single linear motor


    def set_route(self):
        """Set a route

        The commands required to set the route are issued. Note if a previous set_route 
        hasn't been completed it will be quietly superseded by this one.
        
        Args:
            self:
        """
        for (device_name, params) in self._device_commands:
                Device.by_name(device_name).value(params)
            
    def is_route_set(self):   
        """Check the route is set

        This assumes that the parameters issued to the command equate to the state
        read from the device when the route is set.

        Args:
            self:

        Returns:
            True if route set else False
        """
        for (device_name, params) in self._device_commands:
            if Device.by_name(device_name).value() != params:
                  return False
        return True
    


class TransitHelper:
    """Transist Helper
    
    The transit helper manages a collection of transits that manage a series of operations.
    
    
    
    """
    _service_table = {} # a dictionary to index services by name

    @classmethod
    def get_service(cls, name):
        return cls._service_table[name]

    def __init__(self, name, transit_dict, transit_end_cb = None):
        """Construct the transit service object

        Args:
            self:
            name: the transit service name
            transit_dict:   a dictionary of the associated transits indexed by transit name
            transit_end_cb: callback for when a transit ends.
        
        """
        self._service_table[name] = self # add this service to the list
        self._transit = transit_dict
        self._current_transit = None
        self._transit_end_cb = transit_end_cb
        """call back to be called when current transit completes"""

    def set_callback(self, cb):
        """Set the callback
        
        This sets the call back for when the transit ends.
        
        args:
            self:
            cb: the callback reference 
        """
        self._transit_end_cb = cb

    def set_transit(self, transit_name):
        """Set Current Transit
        
        This selects a transit from the transit table and makes it the current transit. The current 
        transit is returned.
        
        Args:
            self:
            transit_name: the name of the transit to be made current - string
            
        Returns:
            the selected transit or if not valid None
        """
    
        try:
            self._current_transit = self._transit[transit_name]
            self._next_transit_name = self._current_transit.get_next_transit()
            return self._current_transit
        except KeyError:
            self._next_transit_name = None
            self._current_transit = None
            return None
    
     
    def get_current_transit(self):
        return self._current_transit
        
    
      
    def process_event(self, report):
        """Process the event report
        
        Take actions depending on the event.  The actions taken depend on whether there is an current
        transit, and its current state. The state
        specific handler is called.

        Args:
            self:
            report: a tuple containing the reference to the source object, the unique event code see: display
                and additional information - format and content event specific.
        """
        try:
            self._current_transit_state = self._current_transit._event_handler(report)
            if self._current_transit_state == Transit.CHAINING:
                self.set_transit(self._next_transit_name) # update the current transit
                self._current_transit.run()
            elif self._current_transit_state == Transit.DONE:
                self.set_transit(self._next_transit_name) # update the current transit but don't run
                try:
                    self._transit_end_cb() # and invoke callback instead
                except AttributeError:
                    print ("no callback")
            
        except AttributeError:
            pass

class Transit:
    """Train Transit

    The transit combines a route with the instructions for the linear motor. A route may be shared
    by more than one transit.

    A Class function sets the current route.

    Once the transit has been initiated, events from the event system are used to monitor progress
    and initiate subsequent actions as required.

    When the transit is complete control passes to the next transit if specified. It may be started
    automatically.
    """

    # event processer return values

    IDLE = const(0)
    ROUTE = const(1)
    RUNNING = const(2)
    CHAINING = const(3)
    DONE = const(4)



    def __init__(self, name, route_name, accel, decel, speed, steps, next_transit, chain = True):
        """Construct the transit object

        Args:
            self:
            name:   display name for transit - string
            route_name: route to be used - string
            accel:  True - accelerate to speed, False - start at given speed
            decel:  True - brake to halt, False - just stop
            speed:  slow, medium or fast - Linearstepper constants
            steps:  number of 6mm steps (not conventional stepper motor steps)
            next_transit:  index name of next transit
            chain:  True - automatically chain to next transit, False - set next transit but don't execute
        
        """
        self._name = name
        self._move_params = (steps, accel, decel, speed)
        self._next_transit = next_transit
        self._chain = chain
        self._route_name = route_name
        self._event_handler = self._handle_idle_event
        self._route = None


    def run(self):
        """Run the transit
        
        This initiates the actions as specified.  The first action is 
        to activate the route associated with transit.

        Subsequent actions will be initiated by events so we set the event handler
        accordingly.

        args:
            self
        
        """
        try:
            # this will fail the first time
            self._route.set_route()
        except AttributeError:
            self._route = RouteTable.get_instance().get_route_by_name(self._route_name)
            self._route.set_route()
        self._event_handler = self._handle_route_event

    def get_name(self):
        return self._name
    
    def get_next_transit(self):
        return self._next_transit

    def _handle_idle_event(self, _):
        """Nothing to do
        except possibly raise a runtime exception
    
        """
        return Transit.IDLE

    def _handle_route_event(self, _):
        """Handle event while waiting for route to be set.
        
        There's no specific event for route set up complete so we need to ask the 
        route if it's set."""
        #source, event, data = report
        if not self._route.is_route_set():
            return Transit.ROUTE
        # route has been set up
        # we can start the transit
        self._route.get_motor().move(*self._move_params)
        self._event_handler = self._handle_motor_event
        return Transit.RUNNING

    def _handle_motor_event(self, report):
        """ if the action is complete then we're done"""
        source, event, _ = report
        if source is not self._route.get_motor():
            return Transit.RUNNING # not our motor - ignore
        if event == Device.ACTION_DONE:
            self._event_handler = self._handle_idle_event
            if self._chain:
                return Transit.CHAINING
            else:
                return Transit.DONE
        return Transit.RUNNING
