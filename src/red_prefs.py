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

model = None

def build_categories(prefs):
    categories = []
    for x in prefs:
        if not x["category"] in categories:
            categories.append(x["category"])

    return categories

class PrefsView(gtk.Notebook):

    def __init__(self):
        gtk.Notebook.__init__(self)

        self.set_show_tabs(0)
        label = gtk.Label("Loading preferences...")
        label.show()
        self.append_page(label, gtk.Label(""))
        
        self.server = rcd_util.get_server_proxy()
        self.get_prefs()

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

    def build(self, prefs):
        # Remove the "loading" "page".
        self.remove_page(0)
        self.set_show_tabs(1)

        categories = build_categories(prefs)

        for c in categories:
            model = PrefsModel(prefs, c)
            view = red_thrashingtreeview.TreeView(model)
            view.set_sensitive(rcd_util.check_server_permission("superuser"))

            col = gtk.TreeViewColumn("Description",
                                     gtk.CellRendererText(),
                                     text=COLUMN_DESCRIPTION)
            view.append_column(col)

            r = CellRendererPref()

            def set_pref_cb(th, pref, value, model):
                try:
                    result = th.get_result()
                except ximian_xmlrpclib.Fault, f:
                    if f.faultCode == rcd_util.fault.type_mismatch:
                        result = 1
                    else:
                        raise

                print "Setting '%s' to '%s'" % (pref["name"], str(value))
                if not result:
                    def set_cb(m, p, v):
                        p["value"] = v
                    model.changed(set_cb, pref, value)
                else:
                    print "Couldn't set pref!"

            def activated_cb(r, pref, model):
                opp = ximian_xmlrpclib.Boolean(not pref["value"])

                th = self.server.rcd.prefs.set_pref(pref["name"], opp)
                th.connect("ready", set_pref_cb, pref, opp, model)

            r.connect("activated", activated_cb, model)

            def editing_done_cb(r, pref, value, model):
                try:
                    v = int(value)
                except ValueError:
                    v = value

                th = self.server.rcd.prefs.set_pref(pref["name"], v)
                th.connect("ready", set_pref_cb, pref, v, model)

            r.connect("editing_done", editing_done_cb, model)

            col = gtk.TreeViewColumn("Value", r, value=COLUMN_VALUE)
            view.append_column(col)

            view.show_all()

            if c:
                label = gtk.Label(c)
            else:
                label = gtk.Label("Settings")
            self.append_page(view, label)        

class PrefsWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, "%s Preferences" % red_main.red_name)

        self.set_default_size(550, 400)

        view = PrefsView()
        view.show()
        self.vbox.add(view)

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x:self.destroy())

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

            if self.value == ximian_xmlrpclib.True or self.value == ximian_xmlrpclib.False:
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
        if self.value == ximian_xmlrpclib.True:
            r = self.toggle_renderer
            r.set_property("active", 1)
            r.set_property("xalign", 0)
        elif self.value == ximian_xmlrpclib.False:
            r = self.toggle_renderer
            r.set_property("active", 0)
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
