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

import string
import gobject, gtk
import red_extra
import rcd_util
import red_component
import red_users

import red_listmodel
import red_thrashingtreeview

from red_gettext import _


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
    def __init__(self):
        HistoryFilter.__init__(self)
        self.build()

    def build(self):
        self.container = gtk.HBox(0, 5)

        actions = [(_("All"),        None),
                   (_("Installations"), "install"),
                   (_("Removals"),      "remove"),
                   (_("Upgrades"),      "upgrade")]
        self.action_opt = HistoryOption(actions)
        self.container.pack_start(self.action_opt, 0, 0, 0)
        self.action_opt.connect("selected", lambda x, y:self.updated())

        self.container.pack_start(gtk.Label(_("User:")), 0, 0, 0)

        self.user_opt = red_users.UsersOption(allow_all=1)
        self.container.pack_start(self.user_opt, 0, 0, 0)
        self.user_opt.connect("selected", lambda x, y:self.updated())

        self.container.pack_start(gtk.Label(_("Timeframe (days):")), 0, 0, 0)

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
        if user and not user.is_any_user():
            self.query.append(["user", "contains", user.name_get()])
        action = self.action_opt.get_active_item()
        if action:
            self.query.append(["action", "contains", action])

        days = self.days_spin.get_value()
        if days < 1:
            days = 30
        self.set_days(days)

        HistoryFilter.updated(self)


PKG_INITIAL = "pkg_initial"
PKG_FINAL   = "pkg_final"

def pkg_name(item):
    if item.has_key(PKG_FINAL):
        return item[PKG_FINAL]["name"]
    if item.has_key(PKG_INITIAL):
        return item[PKG_INITIAL]["name"]
    return ""

def pkg_version(item, flag):
    if item.has_key(flag):
        return item[flag]["version"] + "-" + item[flag]["release"]
    return ""

###
### Sort functions
###

def sort_by_pkg(a, b):
    return cmp(string.lower(pkg_name(a)), string.lower(pkg_name(b)))

def sort_by_time(a, b):
    xa = a.get("timestamp")
    if xa:
        xa = int(xa)
    xb = b.get("timestamp")
    if xb:
        xb = int(xb)
    ## We want opposite order.
    return cmp(xb, xa)

def sort_by_user(a, b):
    return cmp(a.get("user"), b.get("user"))

def sort_by_action(a, b):
    return cmp(a.get("action"), b.get("action"))

COLUMN_ITEM        = 0
COLUMN_ACTION      = 1
COLUMN_USER        = 2
COLUMN_PKG         = 3
COLUMN_PKG_INITIAL = 4
COLUMN_PKG_FINAL   = 5
COLUMN_TIME        = 6

COLUMNS = (
    (COLUMN_ITEM,
     lambda x:x,
     None,
     gobject.TYPE_PYOBJECT),

    (COLUMN_ACTION,
     lambda x:x["action"],
     sort_by_action,
     gobject.TYPE_STRING),

    (COLUMN_USER,
     lambda x:x["user"],
     sort_by_user,
     gobject.TYPE_STRING),

    (COLUMN_PKG,
     lambda x:pkg_name(x),
     sort_by_pkg,
     gobject.TYPE_STRING),

    (COLUMN_PKG_INITIAL,
     lambda x:pkg_version(x, PKG_INITIAL),
     None,
     gobject.TYPE_STRING),

    (COLUMN_PKG_FINAL,
     lambda x:pkg_version(x, PKG_FINAL),
     None,
     gobject.TYPE_STRING),

    (COLUMN_TIME,
     lambda x:x["time_str"],
     sort_by_time,
     gobject.TYPE_STRING),
    )

class HistoryModel(red_listmodel.ListModel):

    def __init__(self):
        red_listmodel.ListModel.__init__(self)

        self.__worker = None
        self.__worker_handler_id = 0

        self.add_columns(COLUMNS)

        self.set_history([])

    def set_history(self, history):
        def set_history_cb(this, h):
            this.__history = h
        self.changed(set_history_cb, history)

    def refresh(self, query):
        if not query:
            return

        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_is = 0
            self.__worker.cancel()

        def get_history_cb(worker, this):
            this.busy(0)
            this.message_pop()
            if not worker.is_cancelled():
                try:
                    history = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    rcd_util.dialog_from_fault(f)
                    return
                this.set_history(history)

        self.busy(1)
        self.message_push(_("Searching..."))
        server = rcd_util.get_server_proxy()
        self.__worker = server.rcd.log.query_log(query)
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         get_history_cb,
                                                         self)

    def get_all(self):
        return self.__history


class HistoryView(gtk.ScrolledWindow):

    def __init__(self, model):
        gtk.ScrolledWindow.__init__(self)
        self.build(model)

    def build(self, model):
        view = red_thrashingtreeview.TreeView(model)
        view.set_rules_hint(1)
        self.view = view

        cols = [(_("Action"),      COLUMN_ACTION),
                (_("User"),        COLUMN_USER),
                (_("Package"),     COLUMN_PKG),
                (_("Old Version"), COLUMN_PKG_INITIAL),
                (_("New Version"), COLUMN_PKG_FINAL),
                (_("Time"),        COLUMN_TIME)]

        for title, id in cols:
            col = gtk.TreeViewColumn(title,
                                     gtk.CellRendererText(),
                                     text=id)

            col.set_resizable(1)
            view.add_column(col,
                            title=title,
                            initially_visible=1,
                            sort_id=id)

        view.sort_by(COLUMN_TIME)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_OUT)
        self.add(view)


class HistoryComponent(red_component.Component):

    def __init__(self):
        red_component.Component.__init__(self)
        self.filter = None

    def name(self):
        return _("History")

    def access_key(self):
        return "h"

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

        search_bar = HistorySearchBar()
        container = search_bar.container_get()
        hbox.pack_start(container, 0, 0)
        hbox.show_all()

        model = HistoryModel()
        self.connect_array(model)
        search_bar.connect("updated", lambda x,q,m:m.refresh(q), model)
        self.filter = search_bar

        view = HistoryView(model)
        page.add(view)

        page.show_all()
        return page

    def activated(self):
        parent = self.parent()
        try:
            update = parent.history_changed
        except AttributeError:
            pass
        else:
            if update and self.filter:
                parent.history_changed = None
                self.filter.updated()

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
        model = HistoryModel()
        filter.connect("updated", lambda x,q,m:m.refresh(q), model)

        self.pkg_name = pkg_name
        self.build(model)
        filter.updated()

    def build(self, model):
        view = red_thrashingtreeview.TreeView(model)
        view.set_rules_hint(1)

        cols = [(_("Action"),      COLUMN_ACTION),
                (_("User"),        COLUMN_USER),
                (_("Old Version"), COLUMN_PKG_INITIAL),
                (_("New Version"), COLUMN_PKG_FINAL),
                (_("Time"),        COLUMN_TIME)]

        for label, id in cols:
            col = gtk.TreeViewColumn(label,
                                     gtk.CellRendererText(),
                                     text=id)
            view.add_column(col,
                            title=label,
                            initially_visible=1,
                            sort_id=id)

        view.sort_by(COLUMN_TIME)
        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(view)
        self.view = view

##     def add_note(self, msg):
##         cell = gtk.CellRendererText()
##         cell.set_property("text", msg)
##         self.view.add_spanner(0, 0, -1, cell)

##         iter = self.model.append()
