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

import string, gobject, gtk
import rcd_util
import red_main
import red_listmodel, red_thrashingtreeview
import ximian_xmlrpclib

from red_gettext import _

model = None

class PrefsViewPage(gtk.HBox):

    def __init__(self, parent_view, prefs):
        gtk.HBox.__init__(self, spacing=6)

        self.view = parent_view
        self.prefs = prefs

        self.handled_prefs = []

        self.queued_sets = []
        self.queued_id = 0

        self.build()

    def apply_prefs(self):
        server = rcd_util.get_server()
        
        for n in self.queued_sets:
            server.rcd.prefs.set_pref(n, self.prefs[n]["value"])

        self.queued_sets = []
        self.queued_id = 0
        return 0

    def enqueue(self, name):
        if not name in self.queued_sets:
            self.queued_sets.append(name)
            if not self.queued_id:
                self.queued_id = gtk.idle_add(self.apply_prefs)

    def create_entry(self, name):
        def entry_changed_cb(e, p, n):
            p.prefs[n]["value"] = e.get_text()
            self.enqueue(n)
            
        entry = gtk.Entry()
        entry.set_text(self.prefs[name]["value"])
        entry.set_activates_default(1)
        entry.connect("changed", entry_changed_cb, self, name)

        self.handled_prefs.append(name)

        return entry

    def create_checkbox(self, name, label):
        def checkbox_toggled_cb(cb, p, n):
            p.prefs[n]["value"] = ximian_xmlrpclib.Boolean(cb.get_active())
            self.enqueue(n)

        cb = gtk.CheckButton(label)
        cb.set_active((self.prefs[name]["value"] and 1) or 0)
        cb.connect("toggled", checkbox_toggled_cb, self, name)

        self.handled_prefs.append(name)

        return cb

    def create_spinbutton(self, name, range,
                          from_daemon_func=None,
                          to_daemon_func=None):
        def spinbutton_value_changed_cb(sb, p, n, cfunc):
            value = sb.get_value_as_int()

            if cfunc:
                value = cfunc(value)

            p.prefs[n]["value"] = value
            self.enqueue(n)

        min, max = range

        value = self.prefs[name]["value"]

        if from_daemon_func:
            value = from_daemon_func(value)

        adj = gtk.Adjustment(value=value,
                             lower=min, upper=max,
                             step_incr=1, page_incr=5)
                             
        spin = gtk.SpinButton(adjustment=adj, digits=0)
        spin.set_update_policy(gtk.UPDATE_IF_VALID)
        spin.connect("value-changed", spinbutton_value_changed_cb,
                     self, name, to_daemon_func)

        self.handled_prefs.append(name)

        return spin
        

class PrefsViewPage_General(PrefsViewPage):

    def __init__(self, parent_view, prefs):
        PrefsViewPage.__init__(self, parent_view, prefs)

    def build(self):
        vbox = gtk.VBox(spacing=6)
        self.pack_start(vbox, padding=6)
        
        # Server frame
        frame = gtk.Frame(_("Server"))
        vbox.pack_start(frame, expand=0)

        table = gtk.Table(rows=2, columns=2)
        table.set_row_spacings(5)
        frame.add(table)

        label = gtk.Label(_("Server URL:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 0, 1, xoptions=gtk.FILL, xpadding=3)

        self.url_entry = self.create_entry("host")
        table.attach(self.url_entry, 1, 2, 0, 1, xpadding=3)

        self.premium_check = self.create_checkbox("enable-premium",
                                                  _("Enable Premium Services "
                                                    "(Red Carpet Express or "
                                                    "Enterprise"))
        table.attach(self.premium_check, 0, 2, 1, 2,
                     xoptions=gtk.FILL, xpadding=3)

        # Packages frame
        frame = gtk.Frame(_("Packages"))
        vbox.pack_start(frame, expand=0)

        table = gtk.Table(rows=2, columns=2)
        table.set_row_spacings(5)
        frame.add(table)

        self.signed_check = self.create_checkbox("require-signatures",
                                                 _("Require packages to be "
                                                   "cryptographically signed"))
        table.attach(self.signed_check, 0, 2, 0, 1,
                     xoptions=gtk.FILL, xpadding=3)

        label = gtk.Label(_("Maximum number of packages to download at once:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 1, 2, xoptions=gtk.FILL, xpadding=3)

        self.max_download_spin = self.create_spinbutton("max-downloads",
                                                        (0, 20))
        table.attach(self.max_download_spin, 1, 2, 1, 2,
                     xoptions=gtk.FILL, xpadding=3)
        
        # Proxy frame
        frame = gtk.Frame(_("Proxy"))
        vbox.pack_start(frame, expand=0)

        table = gtk.Table(rows=4, columns=2)
        table.set_row_spacings(5)
        frame.add(table)

        self.use_proxy_check = gtk.CheckButton(_("Use a proxy"))
        table.attach(self.use_proxy_check, 0, 2, 0, 1,
                     xoptions=gtk.FILL, xpadding=3)

        label = gtk.Label(_("Proxy URL:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 1, 2, xoptions=gtk.FILL, xpadding=3)

        self.proxy_url_entry = self.create_entry("proxy-url")
        table.attach(self.proxy_url_entry, 1, 2, 1, 2, xpadding=3)

        label = gtk.Label(_("Username:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 2, 3, xoptions=gtk.FILL, xpadding=3) 

        self.proxy_username_entry = self.create_entry("proxy-username")
        table.attach(self.proxy_username_entry, 1, 2, 2, 3, xpadding=3)

        label = gtk.Label(_("Password:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 3, 4, xoptions=gtk.FILL, xpadding=3)

        self.proxy_password_entry = self.create_entry("proxy-password")
        self.proxy_password_entry.set_visibility(0)
        table.attach(self.proxy_password_entry, 1, 2, 3, 4, xpadding=3)

        # Have to wait for the above widgets to be created.
        def use_proxy_toggled_cb(cb, p):
            sensitive = cb.get_active()

            p.proxy_url_entry.set_sensitive(sensitive)
            p.proxy_username_entry.set_sensitive(sensitive)
            p.proxy_password_entry.set_sensitive(sensitive)

            if not sensitive:
                p.prefs["proxy-url"]["value"] = ""
                p.prefs["proxy-username"]["value"] = ""
                p.prefs["proxy-password"]["value"] = ""
            else:
                p.prefs["proxy-url"]["value"] = p.proxy_url_entry.get_text()
                p.prefs["proxy-username"]["value"] = p.proxy_username_entry.get_text()
                p.prefs["proxy-password"]["value"] = p.proxy_password_entry.get_text()

            p.enqueue("proxy-url")
            p.enqueue("proxy-username")
            p.enqueue("proxy-password")
                
        self.use_proxy_check.connect("toggled", use_proxy_toggled_cb, self)
        self.use_proxy_check.set_active((self.prefs["proxy-url"]["value"] and 1) or 0)
        self.use_proxy_check.toggled()

class PrefsViewPage_Cache(PrefsViewPage):

    def __init__(self, parent_view, prefs):
        PrefsViewPage.__init__(self, parent_view, prefs)

    def build(self):
        vbox = gtk.VBox(spacing=6)
        self.pack_start(vbox, padding=6)

        table = gtk.Table(rows=2, columns=2)
        table.set_row_spacings(5)
        vbox.pack_start(table, expand=0, fill=1)

        self.enable_cache_check = self.create_checkbox("cache-cleanup-enabled",
                                                       _("Cache downloaded "
                                                         "packages and "
                                                         "metadata"))
        table.attach(self.enable_cache_check, 0, 2, 0, 1,
                     xoptions=gtk.FILL, xpadding=3)

        label = gtk.Label(_("Location of cached data:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 1, 2, xoptions=gtk.FILL, xpadding=3)

        self.cache_dir_entry = self.create_entry("cache-directory")
        table.attach(self.cache_dir_entry, 1, 2, 1, 2, xpadding=3)

        # Expiration frame
        frame = gtk.Frame(_("Expiration"))
        vbox.pack_start(frame, expand=0)

        # lame shim
        hbox = gtk.HBox()
        frame.add(hbox)

        exp_vbox = gtk.VBox(spacing=5)
        hbox.pack_start(exp_vbox, padding=3)

        self.cache_enabled_check = self.create_checkbox("cache-enabled",
                                                        _("Enable cache "
                                                          "expiration"))
        exp_vbox.pack_start(self.cache_enabled_check, expand=0, fill=1)

        hbox = gtk.HBox(spacing=6)
        exp_vbox.pack_start(hbox)
        
        label = gtk.Label(_("Maximum cache size (MB):"))
        label.set_alignment(0.0, 0.5)
        hbox.pack_start(label, expand=0, fill=1)

        self.cache_size_spin = self.create_spinbutton("cache-max-size-in-mb",
                                                      (0, 100000))
        hbox.pack_start(self.cache_size_spin, expand=0, fill=1)

        hbox = gtk.HBox(spacing=6)
        exp_vbox.pack_start(hbox)

        label = gtk.Label(_("Days a package may remain in cache before deletion:"))
        label.set_alignment(0.0, 0.5)
        hbox.pack_start(label, expand=0, fill=1)

        self.cache_age_spin = self.create_spinbutton("cache-max-age-in-days",
                                                     (0, 1460))
        hbox.pack_start(self.cache_age_spin, expand=0, fill=1)

        # Have to do this after the other widgets are created
        def cache_enabled_toggled_cb(cb, p):
            sensitive = cb.get_active()

            p.cache_size_spin.set_sensitive(sensitive)
            p.cache_age_spin.set_sensitive(sensitive)
                
        self.cache_enabled_check.connect("toggled", cache_enabled_toggled_cb,
                                         self)
        self.cache_enabled_check.toggled()

class PrefsViewPage_Daemon(PrefsViewPage):

    def __init__(self, parent_view, prefs):
        PrefsViewPage.__init__(self, parent_view, prefs)

    def build(self):
        vbox = gtk.VBox(spacing=6)
        self.pack_start(vbox, padding=6)

        # Logging frame
        frame = gtk.Frame(_("Logging"))
        vbox.pack_start(frame, expand=0)

        table = gtk.Table(rows=2, columns=2)
        table.set_row_spacings(5)
        frame.add(table)

        label = gtk.Label(_("Level at which to log to /var/log/rcd/rcd-messages:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 0, 1, xoptions=gtk.FILL, xpadding=3)

        self.debug_level_spin = self.create_spinbutton("debug-level",
                                                        (0, 6))
        table.attach(self.debug_level_spin, 1, 2, 0, 1,
                     xoptions=gtk.FILL, xpadding=3)

        label = gtk.Label(_("Level at which to log to syslog:"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 1, 2, xoptions=gtk.FILL, xpadding=3)

        self.syslog_level_spin = self.create_spinbutton("syslog-level",
                                                        (0, 6))
        table.attach(self.syslog_level_spin, 1, 2, 1, 2,
                     xoptions=gtk.FILL, xpadding=3)


        table = gtk.Table(rows=2, columns=2)
        table.set_row_spacings(5)
        vbox.pack_start(table, expand=0)

        label = gtk.Label(_("Server data refresh interval (hours):"))
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 0, 1, xoptions=gtk.FILL, xpadding=3)

        def hours_to_seconds(hours):
            return hours * 60 * 60

        def seconds_to_hours(seconds):
            return seconds / (60*60)

        self.refresh_spin = self.create_spinbutton("heartbeat-interval",
                                                   (1, 72),
                                                   seconds_to_hours,
                                                   hours_to_seconds)
        table.attach(self.refresh_spin, 1, 2, 0, 1,
                     xoptions=gtk.FILL, xpadding=3)

class PrefsViewPage_Advanced(PrefsViewPage):
    def __init__(self, parent_view, prefs):
        PrefsViewPage.__init__(self, parent_view, prefs)

    def build(self):
        unique_prefs = [self.prefs[x] for x in self.prefs
                        if not x in self.view.all_handled_prefs()]
        
        model = PrefsModel(unique_prefs, None)
        view = red_thrashingtreeview.TreeView(model)
        view.set_sensitive(rcd_util.check_server_permission("superuser"))

        col = gtk.TreeViewColumn(_("Description"),
                                 gtk.CellRendererText(),
                                 text=COLUMN_DESCRIPTION)
        view.append_column(col)

        r = CellRendererPref()

        def activated_cb(r, pref, page):
            opp = ximian_xmlrpclib.Boolean(not pref["value"])

            page.prefs[pref["name"]]["value"] = opp
            page.enqueue(pref["name"])

        r.connect("activated", activated_cb, self)

        def editing_done_cb(r, pref, value, page):
            try:
                v = int(value)
            except ValueError:
                v = value

            # Don't set the pref if we didn't change anything.
            if v == pref.get("value"):
                return

            page.prefs[pref["name"]]["value"] = v
            page.enqueue(pref["name"])

        r.connect("editing_done", editing_done_cb, self)

        col = gtk.TreeViewColumn(_("Value"), r, value=COLUMN_VALUE)
        view.append_column(col)

        self.pack_start(view)

class PrefsView(gtk.Notebook):

    def __init__(self):
        gtk.Notebook.__init__(self)

        self.set_show_tabs(0)
        label = gtk.Label(_("Loading preferences..."))
        label.show()
        self.append_page(label, gtk.Label(""))

        self.pages = []
        
        self.server = rcd_util.get_server_proxy()
        self.get_prefs()

    def all_handled_prefs(self):
        handled_prefs = []

        for p in self.pages:
            handled_prefs += p.handled_prefs

        return handled_prefs

    def get_prefs(self):
        def get_prefs_cb(worker, this):
            try:
                prefs = worker.get_result()
            except ximian_xmlrpclib.Fault, f:
                prefs = []
                rcd_util.dialog_from_fault(f)

            this.build(prefs)

        th = self.server.rcd.prefs.list_prefs()
        th.connect("ready", get_prefs_cb, self)

    def append(self, page, title):
        self.pages.append(page)

        label = gtk.Label(title)
        gtk.Notebook.append_page(self, page, label)

    def build(self, prefs):
        # Remove the "loading" "page".
        self.remove_page(0)
        self.set_show_tabs(1)

        prefs_dict = {}
        for p in prefs:
            prefs_dict[p["name"]] = p

        page = PrefsViewPage_General(self, prefs_dict)
        page.show_all()
        self.append(page, "General")

        page = PrefsViewPage_Cache(self, prefs_dict)
        page.show_all()
        self.append(page, "Cache")

        page = PrefsViewPage_Daemon(self, prefs_dict)
        page.show_all()
        self.append(page, "Daemon")

        page = PrefsViewPage_Advanced(self, prefs_dict)
        page.show_all()
        self.append(page, "Advanced")
        
class PrefsWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, _("%s Preferences") % red_main.red_name)

        self.set_default_size(550, 400)

        view = PrefsView()
        view.show()
        self.vbox.add(view)

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x:self.destroy())
        button.grab_default()

class CellRendererPref(gtk.GenericCellRenderer):
    __gproperties__ = {
        "value" : (gobject.TYPE_PYOBJECT, "value property", "the cell value",
                   gobject.PARAM_READWRITE)
    }
    
    def __init__(self):
        gobject.GObject.__init__(self)
        self.text_renderer = gtk.CellRendererText()
        self.toggle_renderer = gtk.CellRendererToggle()
        self.value = None

        self.text_renderer.set_property("editable", 1)
        self.toggle_renderer.set_property("activatable", 1)

    def do_set_property(self, pspec, value):
        if pspec.name == "value":
            self.value = value

            if isinstance(self.value, ximian_xmlrpclib.Boolean):
                mode = gtk.CELL_RENDERER_MODE_ACTIVATABLE
            else:
                mode = gtk.CELL_RENDERER_MODE_EDITABLE

            self.set_property("mode", mode)
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_get_property(self, pspec):
        if pspec.name == "value":
            return self.value
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def get_actual_renderer(self):
        if isinstance(self.value, ximian_xmlrpclib.Boolean):
            r = self.toggle_renderer
            r.set_property("active", self.value)
            r.set_property("xalign", 0)
        else:
            r = self.text_renderer
            r.set_property("text", str(self.value))

        return r

    def on_get_size(self, widget, cell_area):
        r = self.get_actual_renderer()

        return r.get_size(widget, cell_area)

    def on_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):
        r = self.get_actual_renderer()

        return r.render(window, widget, background_area,
                        cell_area, expose_area, flags)

    def on_activate(self, event, widget, path,
                    background_area, cell_area, flags):
        r = self.get_actual_renderer()

        # Should only be called for toggle renderer
        if r != self.toggle_renderer:
            assert 0

        model = widget.get_model()
        pref = model.get_list_item(int(path))
        self.emit("activated", pref)
        return r.activate(event, widget, path,
                          background_area, cell_area, flags)

    def on_start_editing(self, event, widget, path,
                         background_area, cell_area, flags):
        r = self.get_actual_renderer()

        # Should only be called for text renderer
        if r != self.text_renderer:
            assert 0

        model = widget.get_model()
        pref = model.get_list_item(int(path))

        entry = gtk.Entry()
        entry.set_property("has_frame", 0)
        entry.set_property("text", self.value)

        def editing_done_cb(e, p):
            self.emit("editing_done", p, e.get_text())

        entry.connect("editing_done", editing_done_cb, pref)
        entry.show()

        return entry

gobject.type_register(CellRendererPref)

gobject.signal_new("activated",
                   CellRendererPref,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

gobject.signal_new("editing_done",
                   CellRendererPref,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))

COLUMNS = (
    ("PREF",
     lambda x:x,
     gobject.TYPE_PYOBJECT),
    
    ("NAME",
     lambda x:x["name"],
     gobject.TYPE_STRING),
    
    ("DESCRIPTION",
     lambda x:string.join(rcd_util.linebreak(x["description"], 50), "\n"),
     gobject.TYPE_STRING),
    
    ("CATEGORY",
     lambda x:x["category"],
     gobject.TYPE_STRING),
    
    ("VALUE",
     lambda x:x["value"],
     gobject.TYPE_PYOBJECT)
)

for i in range(len(COLUMNS)):
    name = COLUMNS[i][0]
    exec("COLUMN_%s = %d" % (name, i))

class PrefsModel(red_listmodel.ListModel):
    def __init__(self, prefs, category=None):

        red_listmodel.ListModel.__init__(self)

        self.__category = category
        if self.__category:
            self.__prefs = [x for x in prefs if x["category"] == category]
        else:
            self.__prefs = prefs

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

        self.changed(lambda x:x)

    def get(self, i):
        return self.__prefs[i]

    def get_all(self):
        return self.__prefs
