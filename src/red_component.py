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

valid_widget_types = ["upper", "lower", "main"]

class Component(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)

        self.have_server = 0
        self.server_obj = None

        self.transaction = None

        self.widgets = {}
        self.did_build = 0
        self.visible_flag = 0

    def get(self, type):
        assert type in valid_widget_types
        return self.widgets.get(type)

    def display(self, type, widget):
        assert type in valid_widget_types
        if id(self.widgets.get(type)) != id(widget):
            self.widgets[type] = widget
            self.emit("display", type, widget)

    def visible(self, flag):
        if flag and not self.did_build:
            self.build()
            self.did_build = 1
        if self.visible_flag ^ flag:
            self.visible_flag = flag
            self.changed_visibility(flag)
            self.emit("visible", flag)

    def is_visible(self):
        return self.visible_flag

    def is_user_selectable(self):
        return 1

    def server(self):
        assert self.have_server
        return self.server_obj

    def set_server(self, server):
        assert not self.have_server
        self.server_obj = server
        self.have_server = 1

    def set_transaction(self, transaction):
        self.transaction = transaction

    def switch_to(self, component):
        self.emit("switch", component)

    def message(self, msg):
        self.emit("message", msg)

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
        pass

    def changed_visibility(self, flag):
        pass


gobject.type_register(Component)

gobject.signal_new("display",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, gtk.Widget.__gtype__))

gobject.signal_new("visible",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_BOOLEAN,))

gobject.signal_new("switch",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_OBJECT,))

gobject.signal_new("message",
                   Component,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, ))
