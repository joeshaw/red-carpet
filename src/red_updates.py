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
import red_packagearray, red_packageview
import red_pendingops
import red_component
import rcd_util

from red_gettext import _

class SummaryComponent(red_component.Component):

    def name(self):
        return _("Summary")

    def long_name(self):
        return _("Update Summary")

    def pixbuf(self):
        return "summary"

    def access_key(self):
        return "s"

    def accelerator(self):
        return "<Control>s"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        self.array = red_packagearray.UpdatedPackages()
        self.connect_array(self.array)

        page = gtk.VBox(0, 6)

        hbox = gtk.HBox(0, 6)

        label = gtk.Label("")
        label.set_alignment(0, 0.5)
        label.set_markup("<b>" + self.long_name() + "</b>")
        hbox.pack_start(label)

        hbox.show_all()
        page.pack_start(hbox, 0, 0)

        ### Main

        view = red_packageview.PackageView()
        self.connect_view(view)

        view.append_action_column()
        col = view.append_importance_column()
        view.append_channel_column(show_channel_name=0)
        view.append_name_column()
        view.append_version_column(column_title=_("New Version"))
        view.append_current_version_column()

        view.set_model(self.array)
        view.sort_by(col)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_OUT)
        scrolled.add(view)
        scrolled.show_all()

        page.pack_start(scrolled, expand=1, fill=1)

        return page


    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()

    def select_all_sensitive(self):
        return rcd_util.check_server_permission("upgrade") \
               and self.array.len() > 0

    def select_all(self):
        for pkg in self.array.get_all():
            red_pendingops.set_action(pkg, red_pendingops.TO_BE_INSTALLED)

    def unselect_all(self):
        for pkg in self.array.get_all():
            red_pendingops.set_action(pkg, red_pendingops.NO_ACTION)
