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

import gtk
import math, string

import red_transaction
import red_pixbuf
import red_pendingops
import red_settings

from red_gettext import _

class SideBar(gtk.VBox, red_pendingops.PendingOpsListener):

    conf_str_hidden = "UI/sidebar_hidden"

    def __init__(self):
        gtk.VBox.__init__(self, 0, 6)
        red_pendingops.PendingOpsListener.__init__(self)

        self.update_pending = 0

        self.set_border_width(6)

        self.build()

        config = red_settings.get_config()
        if not int(config.get(self.conf_str_hidden + "=0")):
            self.show_all()

    def change_visibility(self):
        config = red_settings.get_config()

        if self.get_property("visible"):
            config.set(self.conf_str_hidden, 1)
            self.hide()
        else:
            config.set(self.conf_str_hidden, 0)
            self.show_all()

        config.sync()

    def build(self):
        self.shortcut_bar = ShortcutBar()
        self.pack_start(self.shortcut_bar, 0, 0)

        label = gtk.Label("")
        label.set_markup("<b>%s</b>" % _("Pending Operations"))
        label.set_alignment(0, 0.5)
        self.pack_start(label, 0, 1)

        view = red_transaction.TransactionSimple()
        self.pack_start(view, 1, 1)

        self.label = gtk.Label("")
        self.label.set_alignment(0.0, 0.5)
        self.update_label()
        self.pack_start(self.label, expand=0, fill=1)

        bbox = gtk.HButtonBox()
        bbox.set_spacing(6)
        bbox.set_layout(gtk.BUTTONBOX_START)

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_BUTTON)

        ## Details Button
        self.details = gtk.Button()
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        self.details.add(align)
        box = gtk.HBox(0, 2)
        image = red_pixbuf.get_widget("pending-transactions",
                                      width=width, height=height)
        box.pack_start(image, 0, 0)
        box.pack_start(gtk.Label(_("Details")), 0, 0)
        align.add(box)
        bbox.add(self.details)
        self.details.set_sensitive(0)

        self.pack_start(bbox, 0, 1)

    def get_shortcut_bar(self):
        return self.shortcut_bar

    def get_details_button(self):
        return self.details

    # PendingOpsListener implementation
    def pendingops_changed(self, pkg, key, value, old_value):
        if not self.update_pending and key == "action":
            self.update_pending = gtk.idle_add(self.pendingops_changed_cb)

    def pendingops_changed_cb(self):
        self.update_label()
        if red_pendingops.pending_ops_exist():
            self.details.set_sensitive(1)
        else:
            self.details.set_sensitive(0)

        self.update_pending = 0
        return 0

    def update_label(self):
        msg_list = []

        ins_count = red_pendingops.pending_install_count()
        if ins_count:
            msg_list.append("%d pending install%s" %
                            (ins_count, (ins_count > 1 and "s") or ""))

        rem_count = red_pendingops.pending_remove_count()
        if rem_count:
            msg_list.append("%d pending removal%s" %
                            (rem_count, (rem_count > 1 and "s") or ""))

        if not msg_list:
            msg_list.append("No pending operations")

        msg = string.join(msg_list, "\n")

        for i in range(len(msg_list) - 2, 0):
            msg += "\n"

        self.label.set_text(msg)

class ShortcutBar(gtk.HBox):

    def __init__(self):
        gtk.HBox.__init__(self)
        self.components = []
        self.buttons = []
        self.constructed = 0

        def on_realize(x):
            x.construct()

        self.connect("realize", on_realize)

    def add(self, component, callback):
        self.components.append((component, callback))

    def active_changed(self, comp, w, button):
        for b, id in self.buttons:
            if not b:
                continue

            b.handler_block(id)
            if b != button:
                b.set_active(0)
            else:
                b.set_active(1)
            b.handler_unblock(id)

    def construct(self):
        if self.constructed:
            return
        self.constructed = 1

        if len(self.components) < 1:
            return

        rows = int(math.ceil(len(self.components) / 2.0))
        table = gtk.Table(rows, 2)
        table.set_col_spacings(6)
        table.set_row_spacings(6)

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_BUTTON)

        row = 0
        for comp, callback in self.components:
            if comp.show_in_shortcuts():
                button = gtk.ToggleButton()
                align = gtk.Alignment(0.5, 0.5, 0, 0)
                button.add(align)
                box = gtk.HBox(0, 2)

                image = None

                if comp.stock():
                    assert not comp.pixbuf()

                    stock_id = comp.stock()
                    
                    image = gtk.Image()
                    image.set_from_stock(stock_id, gtk.ICON_SIZE_BUTTON)
                
                if comp.pixbuf():
                    assert not comp.stock()
                    image = red_pixbuf.get_widget(comp.pixbuf(),
                                                  width=width, height=height)


                if image:
                    box.pack_start(image, 0, 0)

                box.pack_start(gtk.Label(comp.name()), 0, 0)
                align.add(box)

                y = int(row)
                if row > y:
                    x = 1
                else:
                    x = 0

                table.attach(button,
                             x, x+1, y, y+1,
                             gtk.FILL, 0, 0, 0)

                row += 0.5
                sid = button.connect("clicked", callback)
            else:
                button = None
                sid = 0

            comp.connect("display", self.active_changed, button)
            self.buttons.append((button, sid))

        self.pack_start(table)
        table.show_all()
