###
### Copyright (C) 2003 Ximian, Inc.
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
from red_gettext import _

class MirrorsStore(gtk.ListStore):

    def __init__(self, mirrors):
        gtk.ListStore.__init__(self,
                               gobject.TYPE_INT,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING)

        self.__mirrors = mirrors
        self.__iters = {}

        i = 0
        for m in self.__mirrors:
            iter = self.append()
            self.set(iter,
                     0, 0,
                     1, m["name"],
                     2, m["location"],
                     3, m["url"])
            self.__iters[i] = iter
            i += 1

    def select(self, n):
        for i in range(len(self.__mirrors)):
            self.set(self.__iters[i], 0, i == n)


class MirrorsView(gtk.TreeView):

    def __init__(self, mirrors):
        gobject.GObject.__init__(self)
        self.__mirrors = mirrors

        sel = self.get_selection()
        sel.set_mode(gtk.SELECTION_NONE)

        self.__store = MirrorsStore(mirrors)
        self.set_model(self.__store)

        def toggle_cb(cr, path, view):
            model = view.get_model()
            n = int(path)
            model.select(n)
            self.emit("selected_mirror", self.__mirrors[n])
            
        toggle = gtk.CellRendererToggle()
        toggle.set_property("activatable", 1)
        toggle.connect("toggled", toggle_cb, self)
        col = gtk.TreeViewColumn("",
                                 toggle,
                                 active=0);
        self.append_column(col)

        col = gtk.TreeViewColumn(_("Mirror"),
                                 gtk.CellRendererText(),
                                 text=1)
        self.append_column(col)

        col = gtk.TreeViewColumn(_("Location"),
                                 gtk.CellRendererText(),
                                 text=2)
        self.append_column(col)

    def select_by_url(self, url):
        for i in range(len(self.__mirrors)):
            this_url = self.__mirrors[i]["url"]
            if this_url == url:
                self.__store.select(i)
                return
        self.__store.select(-1)


gobject.type_register(MirrorsView)
gobject.signal_new("selected_mirror",
                   MirrorsView,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))



class MirrorsWindow(gtk.Dialog):

    def __init__(self):
        gobject.GObject.__init__(self)
        self.set_title(_("Choose a Mirror"))

        self.set_size_request(550, 400)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox.add(sw)

        mirrors = rcd_util.get_mirrors()

        self.__view = MirrorsView(mirrors)
        sw.add(self.__view)

        def proxy_selected_mirror_cb(view, item, win):
            win.emit("selected_mirror", item)
        self.__view.connect("selected_mirror", proxy_selected_mirror_cb, self)

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x: self.destroy())
        button.grab_default()

    def select_by_url(self, url):
        self.__view.select_by_url(url)


gobject.type_register(MirrorsWindow)
gobject.signal_new("selected_mirror",
                   MirrorsWindow,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))
