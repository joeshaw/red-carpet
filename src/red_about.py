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

import time, gtk,random

import red_main
import red_pixbuf
from red_gettext import _

class About(gtk.Dialog):

    def __init__(self):

        gtk.Dialog.__init__(self, red_main.get_title())

        b = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
        b.connect("clicked", lambda b,w:w.destroy(), self)

        hbox = gtk.HBox(spacing=6)
        self.vbox.pack_start(hbox, padding=6)

        vbox = gtk.VBox(spacing=2)
        hbox.pack_start(vbox, padding=6)

        title = gtk.Label("")
        title.set_alignment(0.0, 0.5)
        title.set_markup('<span size="xx-large"><b>%s</b></span>' %
                         red_main.red_name)

        vbox.pack_start(title)

        copyright = gtk.Label(red_main.red_copyright.encode("utf-8"))
        copyright.set_alignment(0.0, 0.5)
        vbox.pack_start(copyright)

        license = gtk.Label(_("Licensed under the GNU "
                            "General Public License, version 2"))
        license.set_alignment(0.0, 0.5)
        vbox.pack_start(license)

        self.vbox.show_all()
