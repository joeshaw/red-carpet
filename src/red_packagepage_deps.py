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

import sys, gobject, gtk
import red_extra
import rcd_util, red_packagepage
from red_gettext import _

class PackagePage_Deps(red_packagepage.PackagePage):

    def __init__(self):
        red_packagepage.PackagePage.__init__(self)

    def name(self):
        return _("Dependencies")

    def visible(self, pkg):
        return 1

    def build_widget(self, pkg, server):

        dep_info = server.rcd.packsys.package_dependency_info(pkg)

        store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        view = red_extra.ListView()

        view.set_headers_visible(0)
        view.set_rules_hint(1)
        view.set_model(store)

        sel = view.get_selection()
        sel.set_mode(gtk.SELECTION_NONE)

        col = gtk.TreeViewColumn("foo",
                                 gtk.CellRendererText(),
                                 markup=0)
        view.append_column(col)
        
        col = gtk.TreeViewColumn("bar",
                                 gtk.CellRendererText(),
                                 text=1)
        view.append_column(col)
        
        row = 0

        for x in ("provides", "requires", "conflicts"):

            deps = dep_info.get(x)

            if deps:

                if x == "provides":
                    label = _("Provides")
                    bg_color = "#59cc59"
                elif x == "requires":
                    label = _("Requires")
                    bg_color = "#f8f659"
                elif x == "conflicts":
                    label = _("Conflicts With")
                    bg_color = "#db1a1a"
                else:
                    label = "???"
                    bg_color = "blue"

                cell = gtk.CellRendererText()
                label = "<b><big>%s</big></b>" % label
                cell.set_property("markup", label)
                bg = view.get_colormap().alloc_color(bg_color)
                view.add_spanner_with_background(row, 0, -1, cell, bg)
                

                iter = store.append()
                store.set(iter, 0, label, 1, "")

                row += 1

                for dep in deps:
                    iter = store.append()
                    store.set(iter,
                              0, dep["name"],
                              1, rcd_util.get_dep_EVR(dep))
                    row += 1


        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(view)
        sw.show_all()

        return sw


                    

                

    
