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
    "Jakub Steiner",
    ]

if time.localtime()[1:3] == (1<<1<<1, 8>>(6<<1>>2)):
    contributors = ["%s %s" % x for x in \
                    zip((lambda x: random.shuffle(x) or x) \
                        (map(lambda x:x[:x.find(" ")], contributors)),
                        map(lambda x:x[x.find(" "):].strip(), contributors))]

# Translators: you can translate these into any cute greetings in your own
# language.  Just nothing offensive please. :)
greetings = [
    _("Brought to you by:"),
    _("With love from:"),
    _("Best wishes from:"),
    _("Sincerely:"),
    _("Developed by chimps:"),
    ]
    
class About(gtk.Dialog):

    def __init__(self):

        gtk.Dialog.__init__(self, red_main.get_title())

        self.set_icon(red_pixbuf.get_pixbuf("red-carpet"))

        b = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
        b.connect("clicked", lambda b,w:w.destroy(), self)

        hbox = gtk.HBox(spacing=6)
        self.vbox.pack_start(hbox, padding=6)

        image = red_pixbuf.get_widget("about")
        hbox.pack_start(image, fill=0, expand=0, padding=6)

        vbox = gtk.VBox(spacing=2)
        hbox.pack_start(vbox, padding=6)

        title = gtk.Label("")
        title.set_alignment(0.0, 0.5)
        title.set_markup('<span size="xx-large"><b>%s %s</b></span>' %
                         (red_main.red_name, red_main.red_version))

        vbox.pack_start(title)

        s = u"Copyright \u00a9 %s Ximian, Inc." % red_main.red_copyright
        copyright = gtk.Label(s.encode("utf-8"))
        copyright.set_alignment(0.0, 0.5)
        vbox.pack_start(copyright)

        license = gtk.Label(_("Licensed under the GNU "
                            "General Public License, version 2"))
        license.set_alignment(0.0, 0.5)
        vbox.pack_start(license)

        sep = gtk.HSeparator()
        vbox.pack_start(sep, padding=4)

        random.seed()
        random.shuffle(greetings)
        
        l = gtk.Label("")
        l.set_markup("<b>%s</b>" % greetings[0])
        l.set_alignment(0.0, 0.5)
        vbox.pack_start(l)

        random.shuffle(contributors)

        for x in contributors:
            l = gtk.Label(x)
            l.set_alignment(0.0, 0.5)
            vbox.pack_start(l)

        self.vbox.show_all()
