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

contributors = [
    "Tambet Ingo",
    "Joe Shaw",
    "Jon Trowbridge",
    "Anna Dirks",
    ]

if time.localtime()[1:3] == (1<<1<<1, 8>>(6<<1>>2)):
    contributors = ["%s %s" % x for x in \
                    zip((lambda x: random.shuffle(x) or x) \
                        (map(lambda x:x[:x.find(" ")], contributors)),
                        map(lambda x:x[x.find(" "):].strip(), contributors))]

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
        title.set_markup("<b>%s %s</b>" % (red_main.red_name,
                                           red_main.red_version))

        vbox.pack_start(title)

        copyright = gtk.Label(u"Copyright \u00a9 %s Ximian, Inc." \
                              % red_main.red_copyright)
        vbox.pack_start(copyright)

        random.seed()
        random.shuffle(contributors)

        [vbox.pack_start(gtk.Label("%s" % x)) \
         for x in contributors]

        self.vbox.show_all()
