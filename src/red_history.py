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

model = None


class HistoryFilter(gobject.GObject):
    def __init__(self):
        gobject.GObject.__init__(self)
        self.query = []
        self.cutoff_time = 60 * 60 * 24 * 30

    def query_reset(self):
        self.query = []

    def set_days(self, days):
        if days:
            self.cutoff_time = 60 * 60 * 24 * days

    def updated(self):
        self.query.append(["cutoff_time", "<=", str(self.cutoff_time)])
        self.emit("updated", self.query)

gobject.type_register(HistoryFilter)
gobject.signal_new("updated",
                   HistoryFilter,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))


class HistoryOption(gtk.OptionMenu):

    def __init__(self, array=None):
        gobject.GObject.__init__(self)
        self.item_num_list = []
        self.current_selection = -1
        self.array = array

        self.build()

    def build(self):
        self.current_selection = -1
        self.item_num_list = []

        menu = gtk.Menu()
        i = 0
        for label, name in self.array:
            item = gtk.MenuItem()
            item.add(gtk.Label(label))
            item.show_all()

            self.item_num_list.append(i)

            def activate_cb(item, id, this):
                if this.current_selection != id:
                    this.emit("selected", id)
                    this.current_selection = id

            item.connect("activate", activate_cb, i, self)

            menu.append(item)
            i += 1

        menu.show()
        self.set_menu(menu)

    def get_active_item(self):
        id = self.item_num_list[self.get_history()]
        if self.array[id][1]:
            return self.array[id][1]

gobject.type_register(HistoryOption)
gobject.signal_new("selected",
                   HistoryOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT, ))


class HistorySearchBar(HistoryFilter):
    def __init__(self, server):
        HistoryFilter.__init__(self)
        self.server = server
        self.build()

    def build(self):
        self.container = gtk.HBox(0, 5)
        self.container.pack_start(gtk.Label("Browse"), 0, 0, 0)

        actions = [("All",        None),
                   ("Installs",   "install"),
                   ("Removals",   "remove"),
                   ("Upgrades",   "upgrade")]
        self.action_opt = HistoryOption(actions)
        self.container.pack_start(self.action_opt, 0, 0, 0)
        self.action_opt.connect("selected", lambda x, y:self.updated())

        self.container.pack_start(gtk.Label("packages by"), 0, 0, 0)

        def get_users(server):
            users = map(lambda x:x[0], server.rcd.users.get_all())
            ret = []
            for u in users:
                ret.append((u, u))
            ret.sort(lambda a, b: cmp(a[0], b[0]))
            ret.insert(0, ("All Users", None))
            return ret

        users = get_users(self.server)
        self.user_opt = HistoryOption(users)
        self.container.pack_start(self.user_opt, 0, 0, 0)
        self.user_opt.connect("selected", lambda x, y:self.updated())

        self.container.pack_start(gtk.Label("in last"), 0, 0, 0)

        self.days_spin = gtk.SpinButton()
        self.days_spin.set_increments(1, 7)
        self.days_spin.set_range(1, 360)
        self.days_spin.set_numeric(1)
        self.days_spin.set_value(30)
        self.container.pack_start(self.days_spin, 0, 0, 0)
        self.days_spin.connect("value-changed", lambda x:self.updated())

        self.container.pack_start(gtk.Label("days"), 0, 0, 0)

    def container_get(self):
        return self.container

    def updated(self):
        self.query_reset()
        user = self.user_opt.get_active_item()
        if user:
            self.query.append(["user", "contains", user])
        action = self.action_opt.get_active_item()
        if action:
            self.query.append(["action", "contains", action])

        days = self.days_spin.get_value()
        if days < 1:
            days = 30
        self.set_days(days)

        HistoryFilter.updated(self)


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
        container = search_bar.container_get()
        container.show()
        page.pack_start(container, 0, 0, 4)

        view = HistoryView(search_bar)
        page.add(view)

        page.show_all()
        return page


class HistoryView(gtk.ScrolledWindow):

    def __init__(self, search_bar):
        gtk.ScrolledWindow.__init__(self)

        global model
        if not model:
            model = HistoryModel(search_bar)

        self.model = model
        self.build()

    def build(self):
        self.view = gtk.TreeView(self.model)

        cols = [("Action",      COLUMN_ACTION,  1),
                ("User",        COLUMN_USER,    1),
                ("Package",     COLUMN_PACKAGE, 1),
                ("Old Version", COLUMN_VER_OLD, 0),
                ("New Version", COLUMN_VER_NEW, 0),
                ("Time",        COLUMN_TIME,    1)]

        for label, id, sortable in cols:
            col = gtk.TreeViewColumn(label,
                                     gtk.CellRendererText(),
                                     text=id)
            if sortable:
                col.set_sort_column_id(id)
            self.view.append_column(col)

        self.view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(self.view)

COLUMN_ROW =     0
COLUMN_ACTION =  1
COLUMN_USER =    2
COLUMN_TIME =    3
COLUMN_PACKAGE = 4
COLUMN_VER_OLD = 5
COLUMN_VER_NEW = 6
COLUMN_LAST =    7

class HistoryModel(gtk.ListStore):

    def __init__(self, filter):
        gtk.ListStore.__init__(self,
                               gobject.TYPE_PYOBJECT,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)
        self.server = rcd_util.get_server()
        self.filter = filter
        filter.connect("updated", self.update)

        def sort_cb(model, a, b):
            aa = model.get_value(a, COLUMN_ROW)["timestamp"]
            bb = model.get_value(b, COLUMN_ROW)["timestamp"]
            if aa < bb:
                return -1
            if aa > bb:
                return 1
            return 0
            
        self.set_sort_func(COLUMN_TIME, sort_cb)
        # Get some result now
        filter.updated()

    def add_rows(self, entries):
        for entry in entries:
            pkg_name = ""
            pkg_initial_ver = ""
            if entry.has_key("pkg_initial"):
                pkg = entry["pkg_initial"]
                pkg_name = pkg["name"]
                pkg_initial_ver = pkg["version"] + "-" + pkg["release"]

            pkg_final_ver = ""
            if entry.has_key("pkg_final"):
                pkg = entry["pkg_final"]
                pkg_name = pkg["name"]
                pkg_final_ver = pkg["version"] + "-" + pkg["release"]
            
            iter = self.append()
            self.set(iter,
                     COLUMN_ROW,     entry,
                     COLUMN_ACTION,  entry["action"],
                     COLUMN_USER,    entry["user"],
                     COLUMN_TIME,    entry["time_str"],
                     COLUMN_PACKAGE, pkg_name,
                     COLUMN_VER_OLD, pkg_initial_ver,
                     COLUMN_VER_NEW, pkg_final_ver)

    def update(self, filter, query):
        if not query:
            return

        rows_first = 25
        rows_later = 15

        self.clear()
        entries = self.server.rcd.log.query_log(query)
        if not entries:
            return

        self.add_rows(entries[:rows_first])
        entries = entries[rows_first:]

        while entries:
            gtk.idle_add(self.add_rows, entries[:rows_later])
            entries = entries[rows_later:]


class PackageHistoryFilter(HistoryFilter):
    def __init__(self, pkg_name):
        HistoryFilter.__init__(self)
        self.pkg_name = pkg_name
        self.set_days(365 * 10) # 10 years

    def updated(self):
        self.query_reset()
        self.query.append(["name", "is", self.pkg_name])
        HistoryFilter.updated(self)


class PackageHistory(gtk.ScrolledWindow):

    def __init__(self, pkg_name):
        gtk.ScrolledWindow.__init__(self)

        filter = PackageHistoryFilter(pkg_name)
        pkg_model = HistoryModel(filter)

        self.model = pkg_model
        self.pkg_name = pkg_name
        self.build()

    def build(self):
        self.view = gtk.TreeView(self.model)

        cols = [("Action",      COLUMN_ACTION),
                ("User",        COLUMN_USER),
                ("Old Version", COLUMN_VER_OLD),
                ("New Version", COLUMN_VER_NEW),
                ("Time",        COLUMN_TIME)]

        for label, id in cols:
            col = gtk.TreeViewColumn(label,
                                     gtk.CellRendererText(),
                                     text=id)
            self.view.append_column(col)

        self.view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(self.view)
