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
import gtk

import rcd_util
import ximian_xmlrpclib
import red_main
import red_pixbuf
import red_pendingview
import red_component, red_pendingops, red_depview

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

    def __init__(self, install_packages=[], remove_packages=[], verify=0):
        red_component.Component.__init__(self)

        self.server = rcd_util.get_server()
    
        self.install_packages = install_packages
        self.remove_packages = remove_packages
        self.verify = verify

        self.dep_install = []
        self.dep_remove = []
        self.dep_error = None

        try:
            if self.verify:
                F = self.server.rcd.packsys.verify_dependencies()
            else:
                F = self.server.rcd.packsys.resolve_dependencies(
                    self.install_packages,
                    self.remove_packages,
                    [])
        except ximian_xmlrpclib.Fault, f:
            if f.faultCode == rcd_util.fault.failed_dependencies:
                self.dep_error = f.faultString
            else:
                rcd_util.dialog_from_fault(f,
                                           post_dialog_thunk=lambda:self.pop())
        else:
            self.dep_install, self.dep_remove, dep_info = F

    def name(self):
        return "Dependency Resolution"

    def get_install_packages(self):
        return self.install_packages + filter_deps(self.dep_install)

    def get_remove_packages(self):
        return self.remove_packages + filter_deps(self.dep_remove)


    def begin_transaction(self):
        self.busy(1)
        install_packages = self.get_install_packages()
        remove_packages = self.get_remove_packages()
        
        try:
            download_id, transact_id, step_id = \
                         self.server.rcd.packsys.transact(install_packages,
                                                          remove_packages,
                                                          0, # FIXME: flags
                                                          red_main.red_name,
                                                          red_main.red_version)
        except ximian_xmlrpclib.Fault, f:
            self.busy(0)
            rcd_util.dialog_from_fault(f)
            return

        trans_win = red_pendingview.PendingView_Transaction(download_id,
                                                            transact_id,
                                                            step_id,
                                                            parent=self.parent())
        trans_win.show()

        def finished_cb(win, comp):
            comp.busy(0)
            comp.pop()
        trans_win.connect("finished", finished_cb, self)

    def build_dep_error(self):

        page = gtk.VBox(0, 0)

        # Assemble our warning banner
        banner_box = gtk.EventBox()
        style = banner_box.get_style().copy()
        bg_color = banner_box.get_colormap().alloc_color("red")
        style.bg[gtk.STATE_NORMAL] = bg_color
        banner_box.set_style(style)
        banner = gtk.Label("")
        msg = "Dependency Resolution Failed"
        banner.set_markup("<span size=\"large\"><b>%s</b></span>" % msg)
        banner_box.add(banner)
        page.pack_start(banner_box, 0, 0, 0)

        # double-space our dependency error to make it easier to read
        lines = filter(lambda x: x != "", string.split(self.dep_error, "\n"))
        msg = "\n" + string.join(lines, "\n\n")

        view = gtk.TextView()
        view.set_editable(0)
        view.set_cursor_visible(0)
        view.set_wrap_mode(gtk.WRAP_WORD)
        view.get_buffer().set_text(msg)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.add(view)
        page.pack_start(sw, expand=1, fill=1, padding=0)

        buttons = gtk.HBox(0, 0)
        button = gtk.Button(gtk.STOCK_OK)
        button.set_use_stock(1)
        buttons.pack_end(button, 0, 0, 2)

        page.pack_end(buttons, 0, 0, 2)

        button.connect("clicked",
                       lambda x: self.pop())

        page.show_all()

        return page

    def build(self):

        if self.dep_error:
            return self.build_dep_error()

        # If we're verifying and we don't need to do anything...
        if self.verify and not self.dep_install and not self.dep_remove:
            page = gtk.VBox(0, 6)

            hbox = gtk.HBox(0, 0)
            page.pack_start(hbox, expand=0, fill=0)

            image = red_pixbuf.get_widget("progress-verify",
                                          width=48, height=48)
            hbox.pack_start(image, 0, 0, 0)

            label = gtk.Label("All package dependencies are satisfied")
            hbox.pack_start(label, 0, 0 ,0)

            buttons = gtk.HBox(0, 0)
            ok_button = gtk.Button(gtk.STOCK_OK)
            ok_button.set_use_stock(1)
            buttons.pack_end(ok_button, 0, 0, 2)

            page.pack_end(buttons, 0, 0, 0)

            ok_button.connect("clicked", lambda x:self.pop())
            
            page.show_all()
            
            return page

        page = gtk.VBox(0, 6)

        label = gtk.Label("")
        label.set_alignment(0, 0.5)
        label.set_markup("<b>" + self.long_name() + "</b>")
        page.pack_start(label, 0, 0)

        # Freeze the daemon listeners while we're doing a dependency
        # resolution.  Otherwise we detect a change and slow things down.
        #red_serverlistener.freeze_polling()
        #self.connect("destroy", lambda x:red_serverlistener.thaw_polling())

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
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_OUT)
        sw.add(self.table)

        page.pack_start(sw, 1, 1, 0)

        buttons = gtk.HBox(0, 0)
        cancel = gtk.Button(gtk.STOCK_CANCEL)
        cancel.set_use_stock(1)
        cont = gtk.Button("Continue")
        buttons.pack_end(cont, 0, 0, 2)
        buttons.pack_end(cancel, 0, 0, 2)

        page.pack_end(buttons, 0, 0, 0)
        page.show_all()

        cont.connect("clicked", lambda x:self.begin_transaction())
        cancel.connect("clicked", lambda x:self.pop())

        return page

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

    def activated(self):
        sidebar = self.parent().sidebar
        sidebar.set_sensitive(0)

    def deactivated(self):
        sidebar = self.parent().sidebar
        sidebar.set_sensitive(1)
