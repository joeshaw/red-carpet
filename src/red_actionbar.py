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

import gtk
import red_pendingops

from red_gettext import _


class Actionbar(gtk.HBox, red_pendingops.PendingOpsListener):

    def __init__(self):
        gtk.HBox.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)

        self.update_pending = 0
        self.set_spacing(6)

        self.tooltips = gtk.Tooltips()
        self.items = []

    def add(self,
            text,
            tooltip,
            stock=None,
            pixbuf=None,
            pixbuf_name=None,
            sensitive_fn=None,
            callback=None):

        if pixbuf_name:
            assert not pixbuf
            pixbuf = red_pixbuf.get_pixbuf(pixbuf_name)

        if stock or pixbuf:
            image = gtk.Image()

            if stock:
                assert not pixbuf
                image.set_from_stock(stock, gtk.ICON_SIZE_MENU)

            if pixbuf:
                assert not stock
                image.set_from_pixbuf(pixbuf)
        else:
            image = None

        button = gtk.Button()
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        button.add(align)
        box = gtk.HBox(0, 2)
        if image:
            box.pack_start(image, 0, 0)
        label = gtk.Label("")
        label.set_text_with_mnemonic(text)
        box.pack_start(label, 0, 0)
        align.add(box)

        if tooltip:
            self.tooltips.set_tip(button, tooltip)

        gtk.Box.pack_start(self, button, expand=1, fill=1)
        button.set_sensitive(0)

        if callback:
            button.connect("clicked", callback)

        item = {"text":text,
                "tooltip":tooltip,
                "stock":stock,
                "pixbuf":pixbuf,
                "sensitive_fn":sensitive_fn,
                "callback":callback,
                "widget":button
                }

        self.items.append(item)

        return button

    def sensitize_actionbar_items(self):
        for i in self.items:
            s = 1
            if i["sensitive_fn"]:
                s = i["sensitive_fn"]()

            i["widget"].set_sensitive(s)

        self.update_pending = 0
        return 0

    def pendingops_changed(self, pkg, key, value, old_value):
        if key == "action" and not self.update_pending:
            self.update_pending = gtk.idle_add(self.sensitize_actionbar_items)
