###
### Copyright (C) 2003 Ximian, Inc.
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

import string, sys, gtk
import red_pixbuf, red_main
from red_gettext import _

_original_stderr = sys.stderr

class Console:

    def __init__(self):

        img = red_pixbuf.get_widget("progress-config")

        box = gtk.HBox(0, 0)
        box.pack_start(img, expand=0, fill=0, padding=3)

        box.pack_start(gtk.VSeparator(), expand=0, fill=1, padding=3)
        
        self.textview = gtk.TextView()
        self.textview.set_editable(0)
        self.textview.set_cursor_visible(0)
        self.textview.set_size_request(300, 200)

        self.scrolled = gtk.ScrolledWindow()
        self.scrolled.add(self.textview)
        self.scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        box.pack_start(self.scrolled, expand=1, fill=1)

        self.window = gtk.Dialog()
        self.window.set_title(_("Red Carpet Error Console"))
        self.window.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)

        self.window.vbox.add(box)

        self.window.connect("response", lambda d, x: d.hide())

    def write(self, msg):
        _original_stderr.write(msg)
        
        if msg[:11] == "Traceback (":
            msg = "\n" + msg
            
        buf = self.textview.get_buffer()
        iter = buf.get_end_iter()
        self.textview.get_buffer().insert(iter, msg)
        self.window.show_all()

        def scroll_down_cb():
            adj = self.scrolled.get_vadjustment()
            adj.set_value(adj.upper - adj.page_size)
            return 0
        gtk.idle_add(scroll_down_cb)

    def writelines(self, lines):
        msg = string.join(lines, "\n")
        self.write(msg)

    def flush(self):
        pass

sys.stderr = Console()


