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

import string, gtk
import red_packagearray, red_packageview
import red_pendingops
import red_component
import red_depcomponent
import rcd_util, red_pixbuf
import red_emptypage

from red_gettext import _

class UpdatesComponent(red_component.Component):

    def name(self):
        return _("Updates")

    def menu_name(self):
        return _("_Updates")

    def pixbuf(self):
        return "updates"

    def accelerator(self):
        return "<Control>U"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        self.array = red_packagearray.UpdatedPackages()
        self.connect_array(self.array)

        self.__built = 0

        def updates_changed_cb(array, comp):
            if not self.__built:
                return
            if array.len() == 0:
                comp.__have_updates.hide()
                comp.__no_updates.show()
                self.unselect_all()
            else:
                comp.__have_updates.show()
                comp.__no_updates.hide()
        self.array.connect_after("changed", updates_changed_cb, self)

        page = gtk.VBox(0, 6)

        ### Update All button

        box = gtk.HButtonBox()
        box.set_layout(gtk.BUTTONBOX_START)
        page.pack_start(box, 0, 0)

        def sensitize_update_all(this, button):
            sensitive = 0
            if not this.array.len() == 0:
                sensitive = 1
            button.set_sensitive(sensitive)

        update_all = gtk.Button(_("_Update All"))
        self.array.connect_after("changed", lambda x,y,z: sensitize_update_all(y,z),
                                 self, update_all)
        update_all.connect("clicked", lambda x,y: y.update_all(), self)
        box.add(update_all)
        box.show_all()

        ### Main

        view = red_packageview.PackageView(self.array)
        self.connect_view(view)
        self.view = view

        view.append_action_column()
        col = view.append_importance_column()
        view.append_channel_column(optionally_show_channel_name=1)
        view.append_name_column()
        view.append_version_column(column_title=_("New Version"))
        view.append_current_version_column()

        view.sort_by(red_packagearray.COLUMN_IMPORTANCE)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.add(view)
        scrolled.show_all()
        scrolled.hide()

        self.__have_updates = scrolled

        msg1 = "<span size=\"large\"><b>%s</b></span>" \
               % _("The system is up-to-date.")
        msg2 = _("There are no software updates available in any subscribed catalogs.")
        msg = msg1+"\n"+string.join(rcd_util.linebreak(msg2, width=30), "\n")

        self.__no_updates = red_emptypage.EmptyPage(pixbuf_name="verify",
                                                    formatted_text=msg)

        self.__built = 1

        page.pack_start(self.__have_updates, expand=1, fill=1)
        page.pack_start(self.__no_updates, expand=1, fill=1)

        # Show a blank updates list by default until we get a changed
        # signal, even if we don't have any updates, to reduce flicker
        # at startup in the case where we do actually have updates.
        self.__have_updates.show()
        self.__no_updates.hide()

        return page

    def update_all(self):
        pkgs = self.array.get_all()
        install_packages = []
        for pkg in pkgs:
            if red_pendingops.can_perform_action_single(pkg, red_pendingops.TO_BE_INSTALLED):
                install_packages.append(pkg)

        if install_packages:
            dep_comp = red_depcomponent.DepComponent(install_packages, [])
            self.parent().componentbook.push_component(dep_comp)

    def changed_visibility(self, flag):
        if flag:
            self.array.thaw()
        else:
            self.array.freeze()

    def select_all_sensitive(self):
        return self.array.len() > 0

    def select_all(self):
        selection = self.view.get_selection()
        selection.select_all()

    def unselect_all(self):
        selection = self.view.get_selection()
        selection.unselect_all()
        # In some cases, the selection's changed signal doesn't get
        # emitted when we unselect_all on it.  I'm not sure why.
        self.packages_selected([])
