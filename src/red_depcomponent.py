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
import gobject
import gtk

import rcd_util
import ximian_xmlrpclib
import red_main
import red_pixbuf
import red_pendingview
import red_component, red_pendingops, red_depview
from red_gettext import _

def filter_deps(dep_list):
    if not dep_list:
        return []

    def filter_dep(dep):
        if dep.has_key("operation"):
            return dep["package"]
        else:
            return dep

    return map(filter_dep, dep_list)


class DepComponent(gobject.GObject, red_component.Component):

    def __init__(self, install_packages=[], remove_packages=[], verify=0):
        gobject.GObject.__init__(self)
        red_component.Component.__init__(self)

        self.server = rcd_util.get_server()

        self.install_packages = install_packages
        self.remove_packages = remove_packages
        self.verify = verify

        self.__worker = None
        self.__worker_handler_id = 0

        self.get_deps()

    def name(self):
        return _("Dependency Resolution")

    def get_deps(self):
        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_is = 0
            self.__worker.cancel()

        def get_deps_cb(worker, this):
            this.busy(0)

            if not worker.is_cancelled():
                try:
                    F = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    if f.faultCode == rcd_util.fault.failed_dependencies:
                        this.dep_error = f.faultString
                    else:
                        rcd_util.dialog_from_fault(f,
                                                   post_dialog_thunk=lambda:self.pop())
                else:
                    this.dep_install, this.dep_remove, dep_info = F

            # Clean up
            if this.__worker_handler_id:
                this.__worker.disconnect(this.__worker_handler_id)
                this.__worker_handler_is = 0
            this.__worker = None

            self.emit("got-results")

        self.dep_install = []
        self.dep_remove = []
        self.dep_error = None

        server = rcd_util.get_server_proxy()
        self.busy(1)

        if self.verify:
            self.__worker = server.rcd.packsys.verify_dependencies()
        else:
            self.__worker = server.rcd.packsys.resolve_dependencies(
                self.install_packages,
                self.remove_packages,
                [])

        self.__worker_handler_id = self.__worker.connect("ready",
                                                         get_deps_cb,
                                                         self)


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

        # FIXME: Hold a reference to trans_win to work around
        # pygtk bug 92955.
        self.__scratch = trans_win

        def finished_cb(win, comp):
            comp.busy(0)
            comp.pop()
        trans_win.connect("finished", finished_cb, self)

    def build_dep_error_page(self):
        page = self.page
        # Assemble our warning banner
        banner_box = gtk.EventBox()
        style = banner_box.get_style().copy()
        bg_color = banner_box.get_colormap().alloc_color("red")
        style.bg[gtk.STATE_NORMAL] = bg_color
        banner_box.set_style(style)
        banner = gtk.Label("")
        msg = _("Dependency Resolution Failed")
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
        sw.set_shadow_type(gtk.SHADOW_OUT)
        sw.add(view)
        page.pack_start(sw, expand=1, fill=1, padding=0)

        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_END)
        button = gtk.Button(gtk.STOCK_OK)
        button.set_use_stock(1)
        buttons.add(button)

        page.pack_end(buttons, 0, 0, 2)

        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()

        button.connect("clicked",
                       lambda x: self.pop())

        page.show_all()

    def build_verified_ok_page(self):
        page = self.page

        hbox = gtk.HBox(0, 0)
        page.pack_start(hbox, expand=0, fill=0)

        image = red_pixbuf.get_widget("verify", width=48, height=48)
        hbox.pack_start(image, 0, 0, 0)

        label = gtk.Label(_("All package dependencies are satisfied"))
        hbox.pack_start(label, 0, 0 ,0)

        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_END)
        button = gtk.Button(gtk.STOCK_OK)
        button.set_use_stock(1)
        buttons.add(button)

        page.pack_end(buttons, 0, 0, 0)

        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()

        button.connect("clicked", lambda x:self.pop())
            
        page.show_all()

    def build_normal_page(self):
        page = self.page

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
            self.add_package_list(_("Requested Installations"),
                                  self.install_packages)

        if self.remove_packages:
            self.add_package_list(_("Requested Removals"),
                                  self.remove_packages, removal=1)

        if self.dep_install:
            self.add_package_list(_("Required Installations"),
                                  self.dep_install)

        if self.dep_remove:
            self.add_package_list(_("Required Removals"),
                                  self.dep_remove, removal=1)

        self.table.show_all()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_OUT)
        sw.add(self.table)

        page.pack_start(sw, 1, 1, 0)

        buttons = gtk.HButtonBox()
        buttons.set_spacing(6)
        buttons.set_layout(gtk.BUTTONBOX_END)

        cancel = gtk.Button(gtk.STOCK_CANCEL)
        cancel.set_use_stock(1)

        cont = gtk.Button()
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        cont.add(align)
        box = gtk.HBox(0, 2)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_GO_FORWARD, gtk.ICON_SIZE_BUTTON)
        box.pack_start(image, 0, 0)
        box.pack_start(gtk.Label(_("Continue")), 0, 0)
        align.add(box)

        buttons.add(cancel)
        buttons.add(cont)

        page.pack_end(buttons, 0, 0, 0)

        cont.set_flags(gtk.CAN_DEFAULT)
        cont.grab_default()

        page.show_all()

        cont.connect("clicked", lambda x:self.begin_transaction())
        cancel.connect("clicked", lambda x:self.pop())


    def build(self):
        ## That's all we can do here. We might (and usually don't)
        ## have enough information here to decide what kind of page
        ## to build.

        page = gtk.VBox(0, 6)
        page.show()
        self.page = page

        def build_cb(self):
            if self.dep_error:
                self.build_dep_error_page()

            elif self.verify and not self.dep_install and not self.dep_remove:
                self.build_verified_ok_page()

            else:
                self.build_normal_page()

        self.connect("got-results", build_cb)
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

        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_is = 0
            self.__worker.cancel()
            self.__worker = None

gobject.type_register(DepComponent)
gobject.signal_new("got-results",
                   DepComponent,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())
