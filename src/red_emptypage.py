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

import string
import gtk
import rcd_util
import red_pixbuf

class EmptyPage(gtk.EventBox):

    def __init__(self,
                 image=None,
                 pixbuf=None,
                 pixbuf_name=None,
                 text=None,
                 formatted_text=None):

        gtk.EventBox.__init__(self)

        if pixbuf_name:
            assert not pixbuf and not image
            image = red_pixbuf.get_widget(pixbuf_name)

        if pixbuf:
            assert not pixbuf_name and not image
            image = gtk.Image()
            image.set_from_pixbuf(pixbuf)

        if text:
            assert not formatted_text
            formatted_text = "<span size=\"large\"><b>%s</b></span>" % text
            formatted_text = string.join(rcd_util.linebreak(
                formatted_text, width=70),
                                         "\n")

        box = gtk.HBox(0, 0)
        box.pack_start(gtk.Label(""), expand=1, fill=1)

        if image:
            box.pack_start(image, expand=0, fill=1, padding=4)

        label = gtk.Label("")
        if formatted_text:
            label.set_markup(formatted_text)
        box.pack_start(label, expand=0, fill=1, padding=4)

        box.pack_start(gtk.Label(""), expand=1, fill=1)

        frame = gtk.Frame(None)
        frame.add(box)

        self.add(frame)

        style = self.get_style().copy()
        color = self.get_colormap().alloc_color("white")
        style.bg[gtk.STATE_NORMAL] = color
        self.set_style(style)

        self.show_all()
        self.hide()
