###
### Copyright 2003 Ximian, Inc.
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

import sys
import gobject, gtk
import random

import red_main
import red_pixbuf

contributors = [
    "Tambet Ingo",
    "Joe Shaw",
    "Jon Trowbridge",
    ]

def randomize(a, b):
    return random.choice([-1, 0, 1])

class About(gtk.Dialog):

    def __init__(self):

        gtk.Dialog.__init__(self)

        b = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
        b.connect("clicked", lambda b,w:w.destroy(), self)

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox)

        image = red_pixbuf.get_widget("about-monkey", width=100, height=100)
        hbox.pack_start(image)

        vbox = gtk.VBox()
        hbox.pack_start(vbox)

        title = gtk.Label("")
        title.set_markup("<b>%s</b>" % red_main.red_name)

        vbox.pack_start(title)

        contributors.sort(randomize)

        [vbox.pack_start(gtk.Label("%s" % x)) \
         for x in contributors]

        l = gtk.Label("")
        l.set_markup("<small>(this is really ugly and someone should fix it)</small>")
        vbox.pack_start(l)

        self.vbox.show_all()
