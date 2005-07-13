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

        self.__pending_messages = []
        self.__pending_handler  = 0

        img = red_pixbuf.get_widget("console")

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
        self.window.set_title(_("ZENworks Error Console"))
        self.window.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)

        self.window.vbox.add(box)

        self.window.connect("response", lambda d, x: d.hide())

    def write(self, msg):
        _original_stderr.write(msg)

        #ignore deprecation warnings, sigh
        if msg.find('DeprecationWarning') >= 0:
            return

        if msg[:11] == "Traceback (":
            msg = "\n" + msg

        self.__pending_messages.append(msg)

        def write_messages_cb(console):
            buf = console.textview.get_buffer()
            iter = buf.get_end_iter()
            for msg in console.__pending_messages:
                console.textview.get_buffer().insert(iter, msg)

            console.window.show_all()
            
            def scroll_down_cb(console):
                adj = console.scrolled.get_vadjustment()
                adj.set_value(adj.upper - adj.page_size)
                return 0
            gtk.idle_add(scroll_down_cb, console)

            console.__pending_messages = []
            console.__pending_handler  = 0
            return 0

        # We put the text into the console window in a timeout.  That
        # way we can be sure that it happens in the main thread and
        # that we don't have any gtk locking issues if another thread
        # writes to stderr.
        if self.__pending_handler == 0:
            self.__pending_handler = gtk.timeout_add(50,
                                                     write_messages_cb,
                                                     self)

    def writelines(self, lines):
        msg = string.join(lines, "\n")
        self.write(msg)

    def flush(self):
        pass

sys.stderr = Console()


