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
import rcd_util
import red_packagearray
import red_component, red_packageview
import red_pendingops
import red_searchbox
import red_emptypage

from red_gettext import _

class SearchComponent(red_component.Component):

    def __init__(self):
        red_component.Component.__init__(self)
        self.__sbox = None

    def name(self):
        return _("Search")

    def menu_name(self):
        return _("S_earch Packages")

    def stock(self):
        return gtk.STOCK_FIND

    def accelerator(self):
        return "<Control>f"

    def show_in_shortcuts(self):
        return 1

    def select_all_sensitive(self):
        return self.array and self.array.len() > 0

    def select_all(self):
        selection = self.view.get_selection()
        selection.select_all()

    def unselect_all(self):
        selection = self.view.get_selection()
        selection.unselect_all()
        # In some cases, the selection's changed signal doesn't get
        # emitted when we unselect_all on it.  I'm not sure why.
        self.packages_selected([])

    def build(self):

        self.array = red_packagearray.PackagesFromQuery()
        self.connect_array(self.array)

        self.__sbox = red_searchbox.SearchBox()

        def search_cb(sbox, query, filter):
            self.array.set_query(query,
                                 query_msg=_("Searching for matching packages..."),
                                 query_filter=filter)
        self.__sbox.connect("search", search_cb)

        self.__built = 0

        def search_finished_cb(array, comp):
            if not self.__built:
                return
            if array.len() == 0:
                comp.__have_results.hide()
                comp.__no_results.show()
                self.unselect_all()
            else:
                comp.__have_results.show()
                comp.__no_results.hide()

        self.array.connect_after("changed", search_finished_cb, self)

        view = red_packageview.PackageView(self.array)
        self.connect_view(view)
        self.view = view

        view.append_action_column()
        view.append_status_column()
        view.append_channel_column(optionally_show_channel_name=1)
        view.append_locked_column()
        view.append_name_column()
        view.append_version_column()

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.add(view)
        scrolled.show_all()

        self.__have_results = scrolled
        self.__no_results = red_emptypage.EmptyPage(text=_("No matching packages found."))

        self.__built = 1

        self.__sbox.set_widget(self.__have_results)
        self.__sbox.set_widget(self.__no_results)

        self.__have_results.show()
        self.__no_results.hide()

        self.__sbox.show()

        self.__sbox.try_to_grab_focus()

        return self.__sbox
 
    def activated(self):
        if self.__sbox:
            self.__sbox.try_to_grab_focus()
        red_component.Component.activated(self)
