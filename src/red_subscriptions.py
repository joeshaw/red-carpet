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
import rcd_util
import gobject, gtk
import red_pixbuf, red_component

class SubscriptionsComponent(red_component.Component):

    def name(self):
        return "Subscriptions"

    def pixbuf(self):
        return "subscribed"

    def construct(self):
        channels = rcd_util.get_all_channels()

        rows = len(channels) * 4
        cols = 3

        table = gtk.Table(rows, cols, 0)

        r = 0
        for c in channels:

            # a spacer
            table.attach(gtk.VBox(0, 0),
                         0, 3, r, r+1,
                         0, gtk.EXPAND | gtk.FILL,
                         0, 8)

            r = r + 1

            pixbuf = rcd_util.get_channel_icon(c["id"])
            img = gtk.Image()
            img.set_from_pixbuf(pixbuf)
            img.show()
            table.attach(img,
                         0, 1, r, r+2,
                         0, 0,
                         0, 0)

            label = gtk.Label("")
            label.set_alignment(0, 0)
            label.set_markup("<b>%s</b>" % c["name"])
            label.show()
            table.attach(label,
                         1, 2, r, r+1,
                         gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL,
                         0, 0)

            view = gtk.TextView()
            view.get_buffer().set_text(c["description"])
            view.set_wrap_mode(gtk.WRAP_WORD)
            table.attach(view,
                         1, 2, r+1, r+2,
                         gtk.FILL, gtk.FILL,
                         0, 0)

            b = gtk.Button("Foo!")
            b.show()
            table.attach(b,
                         2, 3, r, r+2,
                         gtk.FILL, gtk.FILL,
                         0, 0)


            r = r + 3

        table.show_all()

        return table

            

    def build(self):
        widget = self.construct()
        self.display("main", widget)
        


        
        
