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
import red_pixbuf

from red_gettext import _

class Statusbar(gtk.HBox):
    def __init__(self):
        gobject.GObject.__init__(self)
        self.build()

    def build(self):
        self.tooltips = gtk.Tooltips()

        self.connection = gtk.Button()
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        self.connection.add(align)
        box = gtk.HBox(0, 2)
        align.add(box)

        image = red_pixbuf.get_widget("connect")
        box.pack_start(image, 0, 0)

        self.connection.show_all()
        self.pack_start(self.connection, 0, 0)
        self.connection.connect("clicked", lambda x:self.connect_clicked())

        self.message = gtk.Statusbar()
        self.message.show()
        self.pack_start(self.message, expand=1, fill=1)

    def set_connected(self, host):
        msg = _("Connected to %s" % host)
        self.tooltips.set_tip(self.connection, msg)
        self.pop(abs(hash(self))) # Pop off any old message
        self.push(abs(hash(self)), msg))

    def connect_clicked(self):
        self.emit("connect")

    ## Proxy GtkStatusbar's interface

    def push(self, context_id, text):
        self.message.push(context_id, text)
    def pop(self, context_id):
        self.message.pop(context_id)
    def remove(self, context_id, message_id):
        self.message.remove(context_id, message_id)

gobject.signal_new("connect",
                   Statusbar,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())
