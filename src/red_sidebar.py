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
        if not int(config.getboolean(self.conf_str_hidden + "=0")):
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
        l = gtk.Label("")
        l.set_alignment(0, 0.5)
        l.set_markup("<b>%s</b>" % _("Pending Actions"))
        self.pack_start(l, expand=0, fill=1)

        view = red_transaction.TransactionSimple()
        self.pack_start(view, expand=1, fill=1)

        self.label = gtk.Label("")
        self.label.set_alignment(0.0, 0.5)
        self.update_label()
        self.pack_start(self.label, expand=0, fill=1)

    # PendingOpsListener implementation
    def pendingops_changed(self, pkg, key, value, old_value):
        if not self.update_pending and key == "action":
            self.update_pending = gtk.idle_add(self.pendingops_changed_cb)

    def pendingops_changed_cb(self):
        self.update_label()

        self.update_pending = 0
        return 0

    def update_label(self):
        msg_list = []

        ins_count = red_pendingops.pending_install_count()
        if ins_count:
            if ins_count == 1:
                msg = _("%d pending install") % ins_count
            else:
                msg = _("%d pending installs") % ins_count
            msg_list.append(msg)

        rem_count = red_pendingops.pending_remove_count()
        if rem_count:
            if rem_count == 1:
                msg = _("%d pending removal") % rem_count
            else:
                msg = _("%d pending removals") % rem_count
            msg_list.append(msg)

        if not msg_list:
            msg_list.append(_("No pending actions"))

        msg = string.join(msg_list, "\n")

        for i in range(len(msg_list) - 2, 0):
            msg += "\n"

        self.label.set_text(msg)

