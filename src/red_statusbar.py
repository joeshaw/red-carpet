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
        self.ctx_ids = {}
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
        self.pop(hash(self)) # Pop off any old message
        self.push(hash(self), msg)

    def connect_clicked(self):
        self.emit("connect")

    ## Proxy GtkStatusbar's interface

    def push(self, context_id, text):
        if not self.ctx_ids.has_key(context_id):
            ids = self.ctx_ids.values()
            if len(ids) < 1:
                self.ctx_ids[context_id] = 1
            else:
                self.ctx_ids[context_id] = max(ids) + 1

        self.message.push(self.ctx_ids[context_id], text)
    def pop(self, context_id):
        if self.ctx_ids.has_key(context_id):
            self.message.pop(self.ctx_ids[context_id])
            del self.ctx_ids[context_id]
    def remove(self, context_id, message_id):
        if self.ctx_ids.has_key(context_id):
            self.message.remove(self.ctx_ids[context_id], message_id)
            del self.ctx_ids[context_id]

gobject.signal_new("connect",
                   Statusbar,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())
