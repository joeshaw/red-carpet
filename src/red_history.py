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
import time
import gobject, gtk
import red_extra
import rcd_util
import red_component
import red_users
import red_emptypage
import red_listmodel
import red_thrashingtreeview
import ximian_xmlrpclib

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


PKG_INITIAL = "initial"
PKG_FINAL   = "final"

def pkg_name(item):
    if item.has_key(PKG_FINAL):
        return item[PKG_FINAL]["name"]
    if item.has_key(PKG_INITIAL):
        return item[PKG_INITIAL]["name"]
    return ""

def pkg_version(item, flag):
    if item.has_key(flag):
        return item[flag]["version"]
    return ""

def pkg_time(item):
    return time.strftime("%Y-%m-%d", time.localtime(item["timestamp"]))

def pkg_type(item):
    s = item.get("type")
    if s == "pkg":
        return _("Package");
    if s == "bundle":
        return _("Bundle");
    return s or _("Unknown")

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

def sort_by_type(a, b):
    return cmp(a.get("type"), b.get("type"))

COLUMN_ITEM        = 0
COLUMN_ACTION      = 1
COLUMN_USER        = 2
COLUMN_TYPE        = 3
COLUMN_NAME        = 4
COLUMN_PKG_INITIAL = 5
COLUMN_PKG_FINAL   = 6
COLUMN_TIME        = 7

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

    (COLUMN_TYPE,
     lambda x:pkg_type(x),
     sort_by_type,
     gobject.TYPE_STRING),

    (COLUMN_NAME,
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
     lambda x:pkg_time(x),
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

        cols = [(_("Time"),        COLUMN_TIME),
                (_("Action"),      COLUMN_ACTION),
                (_("User"),        COLUMN_USER),
                (_("Type"),        COLUMN_TYPE),
                (_("Name"),        COLUMN_NAME),
                (_("Old Version"), COLUMN_PKG_INITIAL),
                (_("New Version"), COLUMN_PKG_FINAL),
                ]

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
        self.set_shadow_type(gtk.SHADOW_IN)
        self.add(view)


class HistoryComponent(red_component.Component):

    def __init__(self):
        red_component.Component.__init__(self)
        self.filter = None

    def name(self):
        return _("History")

    def menu_name(self):
        return _("_History")

    def accelerator(self):
        return "<Control>h"

    def pixbuf(self):
        return "history"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        page = gtk.VBox(0, 6)

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

        self.__built = 0

        def search_finished_cb(model, comp):
            if not self.__built:
                return
            if model.len() == 0:
                comp.__have_results.hide()
                comp.__no_results.show()
            else:
                comp.__have_results.show()
                comp.__no_results.hide()

        model.connect_after("changed", search_finished_cb, self)

        view = HistoryView(model)

        self.__have_results = view
        self.__no_results = red_emptypage.EmptyPage(text=_("No results found."))
        self.__built = 1

        page.add(self.__have_results)
        page.add(self.__no_results)

        self.__have_results.show()
        self.__no_results.hide()

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
        red_component.Component.activated(self)

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

        cols = [(_("Time"),        COLUMN_TIME),
                (_("Action"),      COLUMN_ACTION),
                (_("User"),        COLUMN_USER),
                (_("Old Version"), COLUMN_PKG_INITIAL),
                (_("New Version"), COLUMN_PKG_FINAL)]

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
        self.set_shadow_type(gtk.SHADOW_IN)
        self.add(view)
        self.view = view
