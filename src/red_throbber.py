###
### Copyright 2002, 2003 Ximian, Inc.
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

_throbber_pixbufs = ["throb-1",
                     "throb-2",
                     "throb-3",
                     "throb-4",
                     "throb-5",
                     "throb-6",
                     "throb-7",
                     "throb-8",
                     "throb-9",
                     "throb-10"]

for i in range(len(_throbber_pixbufs)):
    _throbber_pixbufs[i] = red_pixbuf.get_pixbuf(_throbber_pixbufs[i])
                    
class Throbber(gtk.EventBox):

    def __init__(self):
        gtk.EventBox.__init__(self)
        self.__timeout = 0
        self.__interval = 100
        self.__throb_count = 0
        self.__frame = 0

        self.__width = 48
        self.__height = 48
        self.set_size_request(self.__width, self.__height)

        bg_color = self.get_colormap().alloc_color("white")
        style = self.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = bg_color
        self.set_style(style)

        self.__img = gtk.Image()
        self.add(self.__img)
        self.__img.show()
        self.__draw()

    def start(self):
        self.__throb_count += 1
        if self.__timeout == 0:
            def throb_cb(throbber):
                if self.__throb_count == 0:
                    self.__timeout = 0
                    self.__frame = 0
                    self.__draw()
                    return 0
                self.__throb()
                return 1
            self.__timeout = gtk.timeout_add(self.__interval, throb_cb, self)

    def stop(self):
        if self.__throb_count > 0:
            self.__throb_count -= 1

    def is_throbbing(self):
        return self.__throb_count > 0

    def __draw(self):
        pixbuf = _throbber_pixbufs[self.__frame]
        self.__img.set_from_pixbuf(pixbuf)

    def __throb(self):

        self.__frame += 1
        if self.__frame >= len(_throbber_pixbufs):
            self.__frame = 0
        self.__draw()


