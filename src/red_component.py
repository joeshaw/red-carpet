###
### Copyright 2002 Ximian, Inc.
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License, version 2,
### as published by the Free Software Foundation.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
###

import gobject, gtk

class Component(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)

        self.transaction = None

        self.__widget = None
        self.__visible_flag = 0
        self.__busy_flag = 0
        self.__parent = None


    # Forces the component to emit a 'display' signal
    # for the current widget (and causes the build method
    # to be executed if no widget has been displayed yet).
    def pull_widget(self):
        if self.__widget is None:
            self.__widget = self.build()
        self.emit("display", self.__widget)

    # Change the component's visibility flag.  This doesn't
    # actually make the component visible or invisible: instead,
    # it tells the component whether or not it is currently being
    # viewed.  If a component is hidden, we often want to do things
    # like "freeze" views so that they don't respond to rcd changes.
    def visible(self, flag):
        if self.__visible_flag ^ flag:
            self.__visible_flag = flag
            if self.__widget is not None:
                self.changed_visibility(flag)

    def is_visible(self):
        return self.__visible_flag

    def parent(self):
        return self.__parent

    def set_parent(self, p):
        self.__parent = p

    def set_transaction(self, transaction):
        self.transaction = transaction

    # Ask the window embedding this component to switch to another
    # component.
    def switch_to(self, component):
        self.emit("switch", component)

    # Ask the window embedding this component to push the current
    # component (i.e. ourselves) onto the component stack and to switch
    # to another component.
    def push(self, component):
        self.emit("push", component)

    # Ask the window embedding this component to pop a component off of
    # the stack and switch to it.  If the stack is empty, this is a no-op.
    def pop(self):
        self.emit("pop")

    # Send a status message to the window embedding this component.  The
    # window is expected to do something reasonable with the message, like
    # displaying it in a status bar.
    def message(self, msg):
        self.emit("message", msg)

    # Signal our 'busy state' to the window embedding this component.
    # When we tell the window we are busy (i.e. set the busy flag to
    # 1), it should give some user feedback (i.e. throbbing a throbber
    # or pulsing a progress bar) until we transmit a busy flag of 0.
    def busy(self, flag):
        if self.__busy_flag ^ flag:
            self.__busy_flag = flag
            self.emit("busy", flag)

    def is_busy(self):
        return self.__busy_flag

    # Pass a widget up to the window embedding this component.  This widget
    # becomes the "view" on the component, replacing any previous widget.
    def display(self, widget):
        if id(self.__widget) != id(widget):
            self.__widget = widget
            self.emit("display", widget)

    ###
    ### Virtual functions
    ###

    def name(self):
        return "?Unknown?"

    def long_name(self):
        return self.name()

    def pixbuf(self):
        return None

    def build(self):
        return None

    def changed_visibility(self, flag):
        pass

    ###
    ### Hints for setting up component navigation
    ###

    def is_user_selectable(self):
        return 1



gobject.type_register(Component)

gobject.signal_new("display",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gtk.Widget.__gtype__,))

gobject.signal_new("switch",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_OBJECT,))

gobject.signal_new("push",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_OBJECT,))

gobject.signal_new("pop",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())

gobject.signal_new("message",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,))

gobject.signal_new("busy",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_BOOLEAN,))



###
### A convenience class that handles all of the signal connecting and
### disconnecting required to monitor a component.
###

class ComponentListener:

    def __init__(self):
        self.__current_component = None
        self.__clear_ids()

    def __clear_ids(self):
        self.__display_id = 0
        self.__switch_id  = 0
        self.__push_id    = 0
        self.__pop_id     = 0
        self.__message_id = 0
        self.__busy_id    = 0

    # A paranoid check: make sure that a component matches what the
    # ComponentListener thinks is the current component.
    def __check_component(self, comp):
        assert id(self.__current_component) == id(comp), "Component Mismatch!"

    # Ugh... fractured English.
    def get_component(self):
        return self.__current_component

    def set_component(self, component):
        if id(self.__current_component) == id(component):
            return

        if self.__current_component:
            self.__current_component.disconnect(self.__display_id)
            self.__current_component.disconnect(self.__switch_id)
            self.__current_component.disconnect(self.__push_id)
            self.__current_component.disconnect(self.__pop_id)
            self.__current_component.disconnect(self.__message_id)
            self.__current_component.disconnect(self.__busy_id)

        self.__clear_ids()

        self.__current_component = component

        def display_cb(comp, widget, listener):
            listener.__check_component(comp)
            listener.do_component_display(widget)

        def switch_cb(comp, new_comp, listener):
            listener.__check_component(comp)
            listener.do_component_switch(new_comp)

        def push_cb(comp, new_comp, listener):
            listener.__check_component(comp)
            listener.do_component_push(new_comp)

        def pop_cb(comp, listener):
            listener.__check_component(comp)
            listener.do_component_pop()

        def message_cb(comp, msg, listener):
            listener.__check_component(comp)
            listener.do_component_message(msg)

        def busy_cb(comp, flag, listener):
            listener.__check_component(comp)
            listener.do_component_busy(flag)

        if component:
            self.__display_id = component.connect("display", display_cb, self)
            self.__switch_id  = component.connect("switch",  switch_cb,  self)
            self.__push_id    = component.connect("push",    push_cb,    self)
            self.__pop_id     = component.connect("pop",     pop_cb,     self)
            self.__message_id = component.connect("message", message_cb, self)
            self.__busy_id    = component.connect("busy",    busy_cb,    self)

    def do_component_display(self, widget):
        pass

    def do_component_switch(self, new_comp):
        pass

    def do_component_push(self, new_comp):
        pass

    def do_component_pop(self, new_comp):
        pass

    def do_component_message(self, msg):
        pass

    def do_component_busy(self, flag):
        pass

        
