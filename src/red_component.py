###
### Copyright (C) 2002-2003 Ximian, Inc.
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
from red_gettext import _

class Component(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)

        self.__widget = None
        self.__visible_flag = 0
        self.__busy_flag = 0
        self.__parent = None
        self.__current_pkg = None


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
    def message_push(self, msg, context_id=-1, transient=0):
        if transient:
            context_id = 0
        elif context_id < 0:
            context_id = hash(self)
        self.emit("message_push", msg, context_id)

    # Pop the component's previous message off of the status bar.
    def message_pop(self, context_id=-1):
        if context_id < 0:
            context_id = hash(self)
        self.emit("message_pop", context_id)

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

    def package_selected(self, pkg):
        self.__current_pkg = pkg
        self.emit("package_selected", pkg)

    def get_current_package(self):
        return self.__current_pkg

    # Proxy selected signals from package views
    def connect_view(self, view):
        def proxy_selected_cb(view, path, pkg, comp):
            comp.package_selected(pkg)
        view.connect("selected", proxy_selected_cb, self)

    # Proxy busy and message signals from arrays.

    def connect_array(self, array):
        def proxy_busy_cb(array, flag, comp):
            comp.busy(flag)
        array.connect("busy", proxy_busy_cb, self)

        def proxy_message_push_cb(array, msg, id, comp):
            comp.message_push(msg, id)
        array.connect("message_push", proxy_message_push_cb, self)

        def proxy_message_pop_cb(array, id, comp):
            comp.message_pop(id)
        array.connect("message_pop", proxy_message_pop_cb, self)

    ###
    ### Virtual functions
    ###

    def name(self):
        return "?Unknown?"

    def long_name(self):
        return self.name()

    def pixbuf(self):
        return None

    def stock(self):
        return None

    def access_key(self):
        return None

    def accelerator(self):
        return None

    def build(self):
        return None

    def changed_visibility(self, flag):
        pass

    def select_all_sensitive(self):
        return 0

    def select_all(self):
        pass

    def unselect_all(self):
        pass

    def activated(self):
        pass

    def deactivated(self):
        pass

    def show_in_shortcuts(self):
        return 0

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

gobject.signal_new("message_push",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, gobject.TYPE_UINT))

gobject.signal_new("message_pop",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_UINT, ))

gobject.signal_new("busy",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_BOOLEAN,))

gobject.signal_new("package_selected",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

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
        self.__pkgsel_id  = 0

    # A paranoid check: make sure that a component matches what the
    # ComponentListener thinks is the current component.
    def __check_component(self, comp):
        assert id(self.__current_component) == id(comp), "Component Mismatch!"

    # Ugh... fractured English.
    def get_component(self):
        return self.__current_component

    def set_component(self, comp):
        if id(self.__current_component) == id(comp):
            return

        if self.__current_component:
            self.__current_component.disconnect(self.__display_id)
            self.__current_component.disconnect(self.__switch_id)
            self.__current_component.disconnect(self.__push_id)
            self.__current_component.disconnect(self.__pop_id)
            self.__current_component.disconnect(self.__msgpush_id)
            self.__current_component.disconnect(self.__msgpop_id)
            self.__current_component.disconnect(self.__busy_id)
            self.__current_component.disconnect(self.__pkgsel_id)

        self.__clear_ids()

        self.__current_component = comp

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

        def msg_push_cb(comp, msg, context_id, listener):
            listener.__check_component(comp)
            listener.do_component_message_push(msg, context_id)

        def msg_pop_cb(comp, context_id, listener):
            listener.__check_component(comp)
            listener.do_component_message_pop(context_id)

        def busy_cb(comp, flag, listener):
            listener.__check_component(comp)
            listener.do_component_busy(flag)

        def pkgsel_cb(comp, pkg, listener):
            listener.__check_component(comp)
            listener.do_component_package_selected(pkg)

        if comp:
            self.__display_id = comp.connect("display",          display_cb,  self)
            self.__switch_id  = comp.connect("switch",           switch_cb,   self)
            self.__push_id    = comp.connect("push",             push_cb,     self)
            self.__pop_id     = comp.connect("pop",              pop_cb,      self)
            self.__msgpush_id = comp.connect("message_push",     msg_push_cb, self)
            self.__msgpop_id  = comp.connect("message_pop",      msg_pop_cb,  self)
            self.__busy_id    = comp.connect("busy",             busy_cb,     self)
            self.__pkgsel_id  = comp.connect("package_selected", pkgsel_cb,   self)

    def do_component_display(self, widget):
        pass

    def do_component_switch(self, new_comp):
        pass

    def do_component_push(self, new_comp):
        pass

    def do_component_pop(self, new_comp):
        pass

    def do_component_message_push(self, msg, context_id):
        pass

    def do_component_message_pop(self, context_id):
        pass

    def do_component_busy(self, flag):
        pass

    def do_component_package_selected(self, pkg):
        pass
