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
import gtk
import red_serverlistener
import red_component, red_pendingops, red_depview
import red_transaction

def filter_deps(dep_list):
    if not dep_list:
        return []

    def filter_dep(dep):
        if dep.has_key("operation"):
            return dep["package"]
        else:
            return dep

    return map(filter_dep, dep_list)


class DepComponent(red_component.Component):

    def __init__(self):
        red_component.Component.__init__(self)

    def name(self):
        return "Dependency Resolution"


    def add_package_list(self, title, package_list, removal=0):
        
        if removal:
            bg_color = "red"
            fg_color = "white"
        else:
            bg_color = "#fcdc7b"
            fg_color = "black"

        # The section heading
        if self.table.row > 0:
            self.table.add_empty_row()
        self.table.add_header(title, fg_color=fg_color, bg_color=bg_color)

        def sort_func(a, b):
            if a.has_key("operation"):
                a = a["package"]

            if b.has_key("operation"):
                b = b["package"]

            return cmp(string.lower(a["name"]), string.lower(b["name"]))

        package_list.sort(sort_func)

        for p in package_list:
            if p.has_key("operation"):
                pkg = p["package"]
                self.table.add_package(pkg, removal)
                for d in p.get("details", []):
                    self.table.add_note(d)
            else:
                self.table.add_package(p, removal)                

    def get_install_packages(self):
        return self.install_packages + filter_deps(self.dep_install)

    def get_remove_packages(self):
        return self.remove_packages + filter_deps(self.dep_remove)


    def build(self):

        page = gtk.VBox(0, 0)
        
        # Freeze the daemon listeners while we're doing a dependency
        # resolution.  Otherwise we detect a change and slow things down.
        #red_serverlistener.freeze_polling()
        #self.connect("destroy", lambda x:red_serverlistener.thaw_polling())

        self.install_packages, self.remove_packages, self.dep_install, self.dep_remove = red_pendingops.resolve_dependencies()

        self.table = red_depview.DepView()

        if self.install_packages:
            self.add_package_list("Requested Installations",
                                  self.install_packages)
            
        if self.remove_packages:
            self.add_package_list("Requested Removals",
                                  self.remove_packages, removal=1)

        if self.dep_install:
            self.add_package_list("Required Installations", self.dep_install)

        if self.dep_remove:
            self.add_package_list("Required Removals",
                                  self.dep_remove, removal=1)

        self.table.show_all()

        sw = gtk.ScrolledWindow()
        sw.add(self.table)
        sw.show()

        page.pack_start(sw, 1, 1, 0)

        buttons = gtk.HBox(0, 0)
        cancel = gtk.Button("Cancel")
        cont = gtk.Button("Continue")
        buttons.pack_end(cont, 0, 0, 2)
        buttons.pack_end(cancel, 0, 0, 2)
        buttons.show_all()

        page.pack_start(buttons, 0, 0, 0)

        def continue_cb(b, dep_comp):
            to_install = dep_comp.get_install_packages()
            to_remove  = dep_comp.get_remove_packages()

            red_transaction.begin_transaction(to_install, to_remove,
                                              parent=dep_comp.parent())
            print "Install:", map(lambda x:x["name"], to_install)
            print "Remove:", map(lambda x:x["name"], to_remove)

        cont.connect("clicked", continue_cb, self)

        def cancel_cb(b, dep_comp):
            dep_comp.pop()
        cancel.connect("clicked", cancel_cb, self)

        return page

    def activated(self):
        self.parent().sensitize_go_button(0)

    def deactivated(self):
        self.parent().sensitize_go_button(1)
