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

import gobject, gtk
import red_extra
import rcd_util
import red_component
import red_users

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

        actions = [("All",        None),
                   ("Installations", "install"),
                   ("Removals",      "remove"),
                   ("Upgrades",      "upgrade")]
        self.action_opt = HistoryOption(actions)
        self.container.pack_start(self.action_opt, 0, 0, 0)
        self.action_opt.connect("selected", lambda x, y:self.updated())

        self.container.pack_start(gtk.Label("User:"), 0, 0, 0)

        self.user_opt = red_users.UsersOption(allow_all=1)
        self.container.pack_start(self.user_opt, 0, 0, 0)
        self.user_opt.connect("selected", lambda x, y:self.updated())

        self.container.pack_start(gtk.Label("Timeframe (days):"), 0, 0, 0)

        self.days_spin = gtk.SpinButton()
        self.days_spin.set_increments(1, 7)
        self.days_spin.set_range(1, 360)
        self.days_spin.set_numeric(1)
        self.days_spin.set_value(30)
        self.container.pack_start(self.days_spin, 0, 0, 0)
        self.days_spin.connect("value-changed", lambda x:self.updated())

    def container_get(self):
        return self.container

    def updated(self):
        self.query_reset()
        user = self.user_opt.get_selected_user()
        if user and user.name_get() != "All":
            self.query.append(["user", "contains", user.name_get()])
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

    def accelerator(self):
        return "<Control>h"

    def pixbuf(self):
        return "history"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        page = gtk.VBox(0, 6)

        label = gtk.Label("")
        label.set_alignment(0, 0.5)
        label.set_markup("<b>" + self.long_name() + "</b>")
        page.pack_start(label, 0, 0)

        hbox = gtk.HBox(0, 6)
        page.pack_start(hbox, 0, 0)

        search_bar = HistorySearchBar(self.server)
        container = search_bar.container_get()
        hbox.pack_start(container, 0, 0)
        hbox.show_all()

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
        self.view.set_rules_hint(1)

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

            col.set_resizable(1)

            if sortable:
                col.set_sort_column_id(id)
            self.view.append_column(col)

        self.view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_OUT)
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

        self.__worker = None
        self.__worker_handler_id = 0

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

    def get_worker(self):
        return self.__worker

    def update(self, filter, query):
        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_is = 0
            self.__worker.cancel()

        if not query:
            return

        def get_history_cb(worker, this):
            if not worker.is_cancelled():
                try:
                    entries = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    rcd_util.dialog_from_fault(f)
                    return

                if entries:
                    rows_first = 25
                    rows_later = 15

                    this.add_rows(entries[:rows_first])
                    entries = entries[rows_first:]

                    while entries:
                        gtk.idle_add(this.add_rows, entries[:rows_later])
                        entries = entries[rows_later:]

        self.clear()

        server = rcd_util.get_server_proxy()
        self.__worker = server.rcd.log.query_log(query)
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         get_history_cb,
                                                         self)

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
        self.view = red_extra.ListView()
        self.view.set_model(self.model)
        self.view.set_rules_hint(1)

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

        def got_results_cb(worker, this):
            rows = 0
            if not worker.is_cancelled():
                try:
                    entries = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    rcd_util.dialog_from_fault(f)
                    return
                rows = len(entries)
            if not rows:
                this.add_note("There is no record of this package ever being installed or removed.")

        worker = self.model.get_worker()
        worker.connect("ready", got_results_cb, self)

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(self.view)

    def add_note(self, msg):
        cell = gtk.CellRendererText()
        cell.set_property("text", msg)
        self.view.add_spanner(0, 0, -1, cell)

        iter = self.model.append()
