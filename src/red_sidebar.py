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

import sys, string
import gobject, gtk
import rcd_util
import red_pixbuf

class SideBar(gtk.EventBox):

    def __init__(self):
        gtk.EventBox.__init__(self)

        self.color = self.get_colormap().alloc_color("gray50")
        self.text_color = self.get_colormap().alloc_color("white")
        
        style = self.get_style().copy()
        style.bg[0] = self.color
        self.set_style(style)

        self.vbox = gtk.VBox(0, 5)

        # We put our vbox in an hbox to get a little extra x-padding...
        # this nesting of hboxes and vboxes reminds me of TeX!
        hbox = gtk.HBox(0, 0)
        hbox.pack_start(self.vbox, 0, 0, 15)
        gtk.EventBox.add(self, hbox)

    def add(self,
            pixbuf=None,
            label="No Label",
            callback=None):

        icon = red_pixbuf.get_widget(pixbuf, width=48, height=48)

        my_vbox = gtk.VBox(0, 0)

        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.add(icon)
        style = button.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = self.color
        style.bg[gtk.STATE_PRELIGHT] = self.color
        button.set_style(style)
        my_vbox.pack_start(button, 0, 0, 0)

        lines = rcd_util.linebreak(label, 12)
        for line in lines:
            l = gtk.Label(line)
            style = l.get_style().copy()
            style.fg[gtk.STATE_NORMAL] = self.text_color
            l.set_style(style)
            my_vbox.pack_start(l, 0, 0, 0)

        if callback:
            button.connect("clicked",
                           lambda b: callback())
        else:
            warn = gtk.Label("")
            warn.set_markup("<small>(no callback)</small>")
            my_vbox.pack_start(warn, 0, 0, 0)

        eventbox = gtk.EventBox()
        style = eventbox.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = self.color
        style.bg[gtk.STATE_PRELIGHT] = self.color
        eventbox.set_style(style)

        def button_press_cb(eb, ev, button):
            if ev.button == 1:
                button.set_state(gtk.STATE_ACTIVE)
        eventbox.connect("button_press_event", button_press_cb, button)
        
        def button_release_cb(eb, ev, button):
            if ev.button == 1:
                button.clicked()
                button.set_state(gtk.STATE_NORMAL)
        eventbox.connect("button_release_event", button_release_cb, button)

        def enter_notify_cb(eb, ev, button):
            button.set_state(gtk.STATE_PRELIGHT)
        eventbox.connect("enter_notify_event", enter_notify_cb, button)

        def leave_notify_cb(eb, ev, button):
            button.leave()
        eventbox.connect("leave_notify_event", leave_notify_cb, button)
        
        eventbox.add(my_vbox)

        self.vbox.pack_start(eventbox, 0, 0, 10)

        eventbox.show_all()
        
           
        
        
