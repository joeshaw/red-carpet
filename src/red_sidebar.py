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
import red_pixbuf

def linebreak(in_str, width):

    str = string.strip(in_str)

    if not str:
        return []

    if len(str) <= width:
        return [str]

    if width < len(str) and str[width] == " ":
        n = width
    else:
        n = string.rfind(str[0:width], " ")

    lines = []

    if n == -1:
        lines.append(str)
    else:
        lines.append(str[0:n])
        lines = lines + linebreak(str[n+1:], width)

    return lines

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

        icon = red_pixbuf.get_widget(pixbuf)

        my_vbox = gtk.VBox(0, 0)

        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.add(icon)
        style = button.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = self.color
        style.bg[gtk.STATE_PRELIGHT] = self.color
        button.set_style(style)
        my_vbox.pack_start(button, 0, 0, 0)

        lines = linebreak(label, 12)
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

        self.vbox.pack_start(my_vbox, 0, 0, 10)

        my_vbox.show_all()
        
           
        
        
