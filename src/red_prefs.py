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

import string
import gobject, gtk
import rcd_util
import red_main
import red_pixbuf
import red_component
import ximian_xmlrpclib

model = None

def build_categories(prefs):
    categories = []
    for x in prefs:
        c = x.get("category", None)
        if c and not c in categories:
            categories.append(c)

    return categories

class PrefsView(gtk.Notebook):

    def __init__(self):
        gtk.Notebook.__init__(self)
        
        server = rcd_util.get_server()
        prefs = server.rcd.prefs.list_prefs()
        categories = build_categories(prefs)

        # Pre 1.2 daemons didn't have categories.
        if not categories:
            categories = [None]
            self.set_show_tabs(0)

        for c in categories:
            model = PrefsModel(prefs, c)
            view = gtk.TreeView(model)

            col = gtk.TreeViewColumn("Description",
                                     gtk.CellRendererText(),
                                     text=COLUMN_DESCRIPTION)
            view.append_column(col)

            r = CellRendererPref()

            def activated_cb(r, pref):
                opp = ximian_xmlrpclib.Boolean(not pref["value"])

                if rcd_util.set_pref(pref["name"], opp):
                    pref["value"] = opp
                else:
                    print "Couldn't set preference!"

            r.connect("activated", activated_cb)

            def editing_done_cb(r, pref, value):
                print "Setting '%s' to '%s'" % (pref["name"], str(value))
                if rcd_util.set_pref(pref["name"], value):
                    pref["value"] = value
                else:
                    print "Couldn't set preference!"

            r.connect("editing_done", editing_done_cb)

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
        pref = model.prefs[int(path)]
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
        pref = model.prefs[int(path)]

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

COLUMN_PREF        = 0
COLUMN_NAME        = 1
COLUMN_DESCRIPTION = 2
COLUMN_CATEGORY    = 3
COLUMN_VALUE       = 4
COLUMN_LAST        = 5
        
class PrefsModel(gtk.GenericTreeModel):
    def __init__(self, prefs, category=None):

        gtk.GenericTreeModel.__init__(self)
        
        if category:
            self.prefs = [x for x in prefs \
                          if x.get("category", None) == category]
        else:
            self.prefs = prefs

    def pref_to_column(self, pref, index):
        if index == COLUMN_PREF:
            return pref
        elif index == COLUMN_NAME:
            return pref["name"]
        elif index == COLUMN_DESCRIPTION:
            return string.join(rcd_util.linebreak(pref["description"], 50), "\n")
        elif index == COLUMN_CATEGORY:
            return pref.get("category", "")
        elif index == COLUMN_VALUE:
            return pref["value"]

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return COLUMN_LAST

    def on_get_column_type(self, index):
        if index == COLUMN_PREF or index == COLUMN_VALUE:
            return gobject.TYPE_PYOBJECT
        else:
            return gobject.TYPE_STRING

    def on_get_path(self, node):
        return node

    def on_get_iter(self, path):
        return path

    def on_get_value(self, node, column):
        pref = self.prefs[node[0]]
        if pref:
            return self.pref_to_column(pref, column)
        return "?no pref"

    def on_iter_next(self, node):
        next = node[0] + 1
        if next >= len(self.prefs):
            return None
        return (next,)

    def on_iter_children(self, node):
        if node == None:
            return (0,)
        else:
            return None

    def on_iter_has_child(self, node):
        return 0

    def on_iter_nth_child(self, node, n):
        if node == None and n == 0:
            return (0,)
        else:
            return None

    def on_iter_parent(self, node):
        return None
