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

from red_gettext import _

class SearchComponent(red_component.Component):

    def __init__(self):
        red_component.Component.__init__(self)
        self.__sbox = None

    def name(self):
        return _("Search")

    def long_name(self):
        return _("Search Packages")

    def stock(self):
        return gtk.STOCK_FIND

    def access_key(self):
        return "e"

    def accelerator(self):
        return "<Control>f"

    def show_in_shortcuts(self):
        return 1

    def select_all_sensitive(self):
        return self.array and self.array.len() > 0

    def select_all(self):
        for pkg in self.array.get_all():
            red_pendingops.set_action(pkg, red_pendingops.TO_BE_INSTALLED)

    def unselect_all(self):
        for pkg in self.array.get_all():
            red_pendingops.set_action(pkg, red_pendingops.NO_ACTION)

    def build(self):

        self.array = red_packagearray.PackagesFromQuery()
        self.connect_array(self.array)

        self.__sbox = red_searchbox.SearchBox(_("Search"))

        def search_cb(sbox, query, filter):
            self.array.set_query(query,
                                 query_msg=_("Searching for matching packages..."),
                                 query_filter=filter)
        self.__sbox.connect("search", search_cb)


        view = red_packageview.PackageView()
        self.connect_view(view)

        view.append_action_column()
        view.append_status_column()
        view.append_channel_column()
        view.append_locked_column()
        view.append_name_column()
        view.append_version_column()
        view.set_model(self.array)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_OUT)
        scrolled.add(view)
        scrolled.show_all()

        self.__sbox.set_widget(scrolled)
        self.__sbox.show()

        self.__sbox.try_to_grab_focus()

        return self.__sbox
 
    def activated(self):
        if self.__sbox:
            self.__sbox.try_to_grab_focus()
