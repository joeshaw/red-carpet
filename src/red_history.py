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

import gobject, gtk
import rcd_util
import red_packagearray
import red_channeloption, red_sectionoption
import red_component, red_packageview, red_packagebrowser
import red_pendingops

class ActionOption(gtk.OptionMenu):

    def __init__(self):
        gobject.GObject.__init__(self)
        self.item_num_list = []
        self.current_selection = -1

        self.build()

    def build(self):
        content = [("All",       -1),
                   ("Installed",  0),
                   ("Removed",    1),
                   ("Upgraded",   2)]

        self.current_selection = -1
        self.item_num_list = []

        menu = gtk.Menu()
        for name, id in content:
            item = gtk.MenuItem()
            item.add(gtk.Label(name))
            item.show_all()

            self.item_num_list.append(id)

            def activate_cb(item, id, this):
                if this.current_selection != id:
                    this.emit("selected", id)
                    this.current_selection = id

            item.connect("activate", activate_cb, id, self)

            menu.append(item)

        menu.show()
        self.set_menu(menu)

    def get_action_num(self):
        return self.item_num_list[self.get_history()]

gobject.type_register(ActionOption)
gobject.signal_new("selected",
                   ActionOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT, ))


class UserOption(gtk.OptionMenu):

    def __init__(self, array=None):
        gobject.GObject.__init__(self)
        self.item_num_list = []
        self.current_selection = -1
        self.array = array

        self.build()

    def build(self):
        content = [("All Users", -1)]

        if self.array:
            i = 0
            for user in self.array:
                content.append((user, i))
                i += 1

            content.sort(lambda a, b: cmp(a[0], b[0]))

        self.current_selection = -1
        self.item_num_list = []

        menu = gtk.Menu()
        for name, id in content:
            item = gtk.MenuItem()
            item.add(gtk.Label(name))
            item.show_all()

            self.item_num_list.append(id)

            def activate_cb(item, id, this):
                if this.current_selection != id:
                    this.emit("selected", id)
                    this.current_selection = id

            item.connect("activate", activate_cb, id, self)

            menu.append(item)

        menu.show()
        self.set_menu(menu)

    def get_action_num(self):
        return self.item_num_list[self.get_history()]

gobject.type_register(UserOption)
gobject.signal_new("selected",
                   UserOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT, ))



class HistorySearchBar(gtk.HBox):
    def __init__(self, server):
        gtk.HBox.__init__(self)

        self.server = server
        self.build()

    def build(self):
        self.set_spacing(5)

        self.pack_start(gtk.Label("Browse"), 0, 0, 0)

        self.action_opt = ActionOption()
        self.pack_start(self.action_opt, 0, 0, 0)

        self.pack_start(gtk.Label("packages by"), 0, 0, 0)

        users = map(lambda x:x[0], self.server.rcd.users.get_all())
        self.user_opt = UserOption(users)
        self.pack_start(self.user_opt, 0, 0, 0)

        self.pack_start(gtk.Label("in last"), 0, 0, 0)

        spin = gtk.SpinButton()
        spin.set_increments(1, 7)
        spin.set_range(0, 360)
        spin.set_numeric(1)
        spin.set_value(30)
        self.pack_start(spin, 0, 0, 0)

        self.pack_start(gtk.Label("days"), 0, 0, 0)

class HistoryComponent(red_component.Component):

    def __init__(self):
        red_component.Component.__init__(self)

        self.server = rcd_util.get_server()

    def name(self):
        return "History"

    def long_name(self):
        return "Browse Packages History"

    def pixbuf(self):
        return "featured"

    def build(self):
        page = gtk.VBox(0,0)

        search_bar = HistorySearchBar(self.server)
        search_bar.show()
        page.pack_start(search_bar, 0, 0, 4)

##        view = HistoryView()
##        page.pack_start(view, 0, 0, 4)

        page.show_all()
        return page


