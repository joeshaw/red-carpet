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

import sys
import math
import pango
import gtk

font_param = 0

def resize(label):
    global font_param
    font_size = 8 + 96 * math.fabs(math.cos(font_param))
    font = pango.FontDescription("Sans %g" % font_size)
    font_param = font_param + 0.1
    label.modify_font(font)
    return 1

def main(version):
    label = gtk.Label("")
    label.set_markup('Red Carpet <span color="red">2</span>')
    resize(label)
    win = gtk.Window()
    win.add(label)
    win.show_all()

    gtk.timeout_add(50, resize, label)

    win.connect("delete_event",
                lambda x,y:sys.exit(0))

    # Start the main loop
    gtk.main()
