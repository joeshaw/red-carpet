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

import string, gtk
import red_packagearray, red_packageview
import red_pendingops, red_searchbox
import red_component

from red_gettext import _

class InstalledComponent(red_component.Component):

    def name(self):
        return _("Installed Software")

    def menu_name(self):
        return _("I_nstalled Software")

    def pixbuf(self):
        return "installed"

    def accelerator(self):
        return "<Control>S"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        self.array = red_packagearray.PackagesFromQuery()
        self.connect_array(self.array)

        self.__sbox = red_searchbox.SearchBox(system_packages_only=1)

        def search_cb(sbox, query, filter):
            self.array.set_query(query,
                                 query_msg=_("Searching for matching packages..."),
                                 query_filter=filter)
        self.__sbox.connect("search", search_cb)
        gtk.idle_add(lambda sbox: search_cb(sbox,
                                            sbox.get_query(),
                                            sbox.get_filter), self.__sbox)

        view = red_packageview.PackageView(self.array)
        self.connect_view(view)
        self.view = view

        view.append_action_column()
        view.append_channel_column(optionally_show_channel_name=1)
        view.append_locked_column()
        view.append_name_column()
        view.append_version_column()

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.add(view)
        scrolled.show_all()

        self.__sbox.set_widget(scrolled)
        self.__sbox.show()

        self.__sbox.try_to_grab_focus()

        return self.__sbox

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

class AvailableComponent(red_component.Component):

    def name(self):
        return _("Available Software")

    def menu_name(self):
        return _("A_vailable Software")

    def pixbuf(self):
        return "status-not-installed"

    def accelerator(self):
        return "<Control>V"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        self.array = red_packagearray.PackagesFromQuery()
        self.connect_array(self.array)

        self.__sbox = red_searchbox.SearchBox(uninstalled_packages_only=1)

        def search_cb(sbox, query, filter):
            self.array.set_query(query,
                                 query_msg=_("Searching for matching packages..."),
                                 query_filter=filter)
        self.__sbox.connect("search", search_cb)
        gtk.idle_add(lambda sbox: search_cb(sbox,
                                            sbox.get_query(),
                                            sbox.get_filter), self.__sbox)

        view = red_packageview.PackageView(self.array)
        self.connect_view(view)
        self.view = view

        view.append_action_column()
        view.append_channel_column(optionally_show_channel_name=1)
        view.append_locked_column()
        view.append_name_column()
        view.append_version_column()

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.add(view)
        scrolled.show_all()

        self.__sbox.set_widget(scrolled)
        self.__sbox.show()

        self.__sbox.try_to_grab_focus()

        return self.__sbox

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
