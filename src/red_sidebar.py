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

import gtk
import math

import red_transaction
import red_pixbuf
import red_pendingops

class SideBar(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self, 0, 6)
        self.set_border_width(6)

        self.build()

    def change_visibility(self):
        if self.get_property("visible"):
            self.hide()
        else:
            self.show()

    def build(self):
        self.shortcut_bar = ShortcutBar()
        self.pack_start(self.shortcut_bar, 0, 0)

        label = gtk.Label("")
        label.set_markup("<b>Pending Transactions</b>")
        label.set_alignment(0, 0.5)
        self.pack_start(label, 0, 1)

        view = red_transaction.TransactionSimple()
        self.pack_start(view, 1, 1)

        transaction_bar = red_transaction.TransactionBar()
        self.pack_start(transaction_bar, expand=0, fill=1)

        bbox = gtk.HButtonBox()
        bbox.set_spacing(6)

        ## Run button
        self.run = RunButton()
        bbox.add(self.run)

        ## Details Button
        self.details = gtk.Button()
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        self.details.add(align)
        box = gtk.HBox(0, 2)
        image = red_pixbuf.get_widget("pending-transactions",
                                      width=24, height=24)
        box.pack_start(image, 0, 0)
        box.pack_start(gtk.Label("Details"), 0, 0)
        align.add(box)
        bbox.add(self.details)

        self.pack_start(bbox, 0, 1)

    def get_shortcut_bar(self):
        return self.shortcut_bar

    def get_run_button(self):
        return self.run

    def sensitize_run_button(self, en):
        self.run.set_sensitive(en)

    def get_details_button(self):
        return self.details


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

        row = 0
        for comp, callback in self.components:
            if comp.show_in_shortcuts():
                button = gtk.ToggleButton()
                align = gtk.Alignment(0.5, 0.5, 0, 0)
                button.add(align)
                box = gtk.HBox(0, 2)

                if comp.pixbuf():
                    image = red_pixbuf.get_widget(comp.pixbuf(),
                                                  width=24, height=24)
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


class RunButton(gtk.Button,
                red_pendingops.PendingOpsListener):

    def __init__(self):
        gtk.Button.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)

        align = gtk.Alignment(0.5, 0.5, 0, 0)
        self.add(align)
        box = gtk.HBox(0, 2)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        box.pack_start(image, 0, 0)
        box.pack_start(gtk.Label("Run"), 0, 0)
        align.add(box)

    def pendingops_changed(self, pkg, key, value, old_value):
        if key == "action":
            if red_pendingops.pending_install_count() + \
               red_pendingops.pending_remove_count() < 1:
                self.set_sensitive(0)
            else:
                self.set_sensitive(1)
