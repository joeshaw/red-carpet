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

import string, sys, gtk

import ximian_xmlrpclib
import rcd_util
import red_main
import red_menubar
import red_transaction
import red_installfiles
import red_component
import red_pendingview
import red_pixbuf
import red_pendingops
import red_depcomponent
import red_prefs
import red_subscriptions
import red_users
import red_throbber
import red_activation
import red_about
import red_mount
import red_serverinfo
import red_sidebar
import red_toolbar
import red_packagearray
import red_packagebook
import red_searchbox
import red_settings
import red_actionbar
from red_gettext import _


def refresh_cb(app):
    server = rcd_util.get_server_proxy()

    def got_channels_cb(worker, app):
        if worker.is_cancelled():
            return
        try:
            stuff_to_poll = worker.get_result()
        except ximian_xmlrpclib.Fault, f:
            rcd_util.dialog_from_fault(f, parent=app)
            return
        
        pend = red_pendingview.PendingView_Simple(title=_("Refreshing channel data"),
                                                  parent=app)
        pend.set_label(_("Downloading channel information"))
        pend.set_icon("dialog-refreshing")
        pend.show_all()
        pend.set_pending_list(stuff_to_poll)

    try:
        worker = server.rcd.packsys.refresh_all_channels()
    except ximian_xmlrpclib.Fault, f:
        rcd_util.dialog_from_fault(f, parent=app)
        return

    rcd_util.server_proxy_dialog(worker,
                                 callback=got_channels_cb,
                                 user_data=app,
                                 parent=app)


def run_transaction_cb(app):
    install_packages = red_pendingops.packages_with_actions(
        red_pendingops.TO_BE_INSTALLED)
    remove_packages = red_pendingops.packages_with_actions(
        red_pendingops.TO_BE_REMOVED)

    # FIXME: This feels like a hack.  Go through the remove_packages and
    # if any of them have an __old_package field, use that package for
    # the removal instead of the actual package.  This is so you can right
    # click on an upgrade and select "remove".
    remove_packages = [x.get("__old_package", x) for x in remove_packages]

    dep_comp = red_depcomponent.DepComponent(install_packages, remove_packages)
    app.push_component(dep_comp)

def verify_deps_cb(app):
    dep_comp = red_depcomponent.DepComponent(verify=1)
    app.push_component(dep_comp)

class AppWindow(gtk.Window,
                red_component.ComponentListener,
                red_pendingops.PendingOpsListener):

    def __init__(self, server):

        gtk.Window.__init__(self)
        red_component.ComponentListener.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)

        self.server = server
        self.__title = None
        self.component_stack = []

        self.busy_count = 0
        self.busy_handler = 0

        self.vbox = gtk.VBox(0, 0)
        self.add(self.vbox)
        self.vbox.show()

        self.components = []

        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.set_icon(red_pixbuf.get_pixbuf("red-carpet"))

        self.menubar = red_menubar.MenuBar(self.accel_group)
        self.menubar.set_user_data(self)
        self.assemble_menubar(self.menubar)

        self.transient_windows = {}

        self.progressbar = gtk.ProgressBar()
        self.statusbar = gtk.Statusbar()

        # A box to put component widgets in.  We use an EventBox
        # instead of just a [HV]Box so that we can control the
        # background color if we want to.
        self.container = gtk.EventBox()

        self.vbox.pack_start(self.menubar, expand=0, fill=1)
        self.menubar.show()

        self.hpaned = gtk.HPaned()
        self.vbox.pack_start(self.hpaned, expand=1, fill=1)

        self.sidebar = red_sidebar.SideBar()
        self.shortcut_bar = self.sidebar.get_shortcut_bar()

        #  Connect sidebar's buttons later
        # (when the components are registered)
        gtk.idle_add(self.connect_sidebar_buttons, self.sidebar)

        self.hpaned.pack1(self.sidebar, resize=0, shrink=0)

        main_box = gtk.VBox(0, 6)
        main_box.set_border_width(6)
        self.hpaned.pack2(main_box, resize=1, shrink=1)

        ## Toolbar
        toolbar_box = gtk.HBox(0, 0)
        main_box.pack_start(toolbar_box, 0, 0)

        self.toolbar = red_toolbar.Toolbar()
        self.assemble_toolbar(self.toolbar)
        toolbar_box.pack_start(self.toolbar, 1, 1)

        ## Throbber
        icon_size = self.toolbar.get_icon_size()
        width, height = gtk.icon_size_lookup(icon_size)
        toolbar_box.pack_end(self.create_throbber(width, height),
                             0, 0)

        ## Actionbar
        self.actionbar = red_actionbar.Actionbar()
        self.assemble_actionbar(self.actionbar)
        main_box.pack_end(self.actionbar, 0, 0)

        main_box.pack_start(self.container, expand=1, fill=1)
        main_box.show_all()
        self.hpaned.show()

        self.statusbar.show()
        self.vbox.pack_start(self.statusbar, expand=0, fill=1)

        self.connect("delete_event", lambda x, y:self.shutdown())

        ## Geometry handling
        self.load_geometry()

        self.save_geometry_id = 0

        def size_allocate_cb(win, alloc):

            def save_geometry_cb(win):
                win.save_geometry()
                win.save_geometry_id = 0

                return 0
            
            if not self.save_geometry_id:
                self.save_geometry_id = gtk.idle_add(save_geometry_cb, win)

        self.connect("size_allocate", size_allocate_cb)

    def save_geometry(self):
        conf = red_settings.get_config()

        x, y, w, h = self.allocation

        conf.set("Geometry/width", w)
        conf.set("Geometry/height", h)

        x, y, w, h = self.sidebar.allocation

        conf.set("Geometry/sidebar_width", w)
        
        conf.sync()

    def load_geometry(self):
        conf = red_settings.get_config()

        w = int(conf.get("Geometry/width=0"))
        h = int(conf.get("Geometry/height=0"))

        if w and h:
            self.set_default_size(w, h)

        w = int(conf.get("Geometry/sidebar_width=0"))

        if w:
            self.hpaned.set_position(w)

    def connect_sidebar_buttons(self, bar):
        ## Details button
        details = bar.get_details_button()
        for comp in self.components:
            if isinstance(comp, red_transaction.TransactionComponent):
                details.connect("clicked",
                                lambda x,y:self.activate_component(y), comp)
                return

        details.set_sensitive(0)

    def create_throbber(self, height, width):
        self.throbber = red_throbber.Throbber(height, width)

        throbbox = gtk.Frame(None)
        throbbox.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        throbbox.set_border_width(2)
        throbbox.add(self.throbber)

        return throbbox

    def set_title(self, title, component=None):
        buf = ""
        if component:
            buf += component + " - "

        if title == None:
            title = self.__title
        else:
            self.__title = title

        if title:
            buf += title

        gtk.Window.set_title(self, buf)

    ##
    ## Toolbar and menubar callback and sensitivity functions
    ##

    def install_sensitive_cb(self):
        comp = self.get_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()
        return red_pendingops.can_perform_action_multiple(
            pkgs, red_pendingops.TO_BE_INSTALLED)

    def remove_sensitive_cb(self):
        comp = self.get_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()
        return red_pendingops.can_perform_action_multiple(
            pkgs, red_pendingops.TO_BE_REMOVED)

    def cancel_sensitive_cb(self):
        comp = self.get_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()
        return red_pendingops.can_perform_action_multiple(
            pkgs, red_pendingops.NO_ACTION)

    def set_package_action_cb(self, action):
        comp = self.get_component()

        assert comp is not None
        
        pkgs = comp.get_current_packages()
        for pkg in pkgs:
            if red_pendingops.can_perform_action_single(pkg, action):
                red_pendingops.set_action(pkg, action)

    def info_sensitive_cb(self):
        comp = self.get_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()
        return len(pkgs) == 1

    def package_info_cb(self):
        comp = self.get_component()

        assert comp is not None
        
        pkgs = comp.get_current_packages()

        assert len(pkgs) == 1

        red_packagebook.show_package_info(pkgs[0])

    ##
    ## Toolbar
    ##

    def assemble_toolbar(self, bar):

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_LARGE_TOOLBAR)

        bar.run = bar.add(text=_("Run Now"),
                          tooltip=_("Perform Pending Operations"),
                          sensitive_fn=red_pendingops.pending_ops_exist,
                          stock=gtk.STOCK_EXECUTE,
                          callback=lambda x:run_transaction_cb(self))

        bar.append_space()

        bar.info = bar.add(text=_("Info"),
                           tooltip=_("Package Information"),
                           pixbuf=red_pixbuf.get_pixbuf("info",
                                                        width=width, height=height),
                           sensitive_fn=self.info_sensitive_cb,
                           callback=lambda x:self.package_info_cb())

        bar.append_space()

        bar.subs = bar.add(text=_("Channels"),
                           tooltip=_("Change your channel subscriptions"),
                           pixbuf=red_pixbuf.get_pixbuf("subscribed",
                                                        width=width, height=height),
                           callback=lambda x:self.open_or_raise_window(red_subscriptions.SubscriptionsWindow))

        bar.refresh = bar.add(text=_("Refresh"),
                              tooltip=_("Refresh Channel Data"),
                              stock = gtk.STOCK_REFRESH,
                              callback=lambda x:refresh_cb(self))

    ##
    ## Actionbar.
    ##

    def assemble_actionbar(self, bar):

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_BUTTON)

        bar.install = bar.add(text=_("Mark for Installation"),
                              tooltip=_("Mark selected packages for installation"),
                              pixbuf=red_pixbuf.get_pixbuf("to-be-installed",
                                                           width=width,
                                                           height=height),
                              sensitive_fn=self.install_sensitive_cb,
                              callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_INSTALLED))

        bar.remove = bar.add(text=_("Mark for Removal"),
                             tooltip=_("Mark selected packages for removal"),
                             pixbuf=red_pixbuf.get_pixbuf("to-be-removed",
                                                          width=width, height=height),
                             sensitive_fn=self.remove_sensitive_cb,
                             callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_REMOVED))

        bar.cancel = bar.add(text=_("Remove Marked Actions"),
                             tooltip=_("Remove marked package actions"),
                             stock=gtk.STOCK_CANCEL,
                             sensitive_fn=self.cancel_sensitive_cb,
                             callback=lambda x:self.set_package_action_cb(red_pendingops.NO_ACTION))


    # The return value is for the benefit of our delete_event handler.
    def shutdown(self):
        if red_transaction.ok_to_quit(self):
            gtk.mainquit()
            return 0
        return 1

    def open_or_raise_window(self, type):
        if self.transient_windows.has_key(type):
            self.transient_windows[type].present()
        else:
            win = type()
            self.transient_windows[type] = win
            def remove_window_cb(w, a, t):
                del a.transient_windows[t]
            win.connect("destroy", remove_window_cb, self, type)
            win.set_transient_for(self)
            win.show()

    def select_all_cb(self, sel):
        comp = self.get_component()
        if not comp:
            return
        
        if sel:
            comp.select_all()
        else:
            comp.unselect_all()

    ##
    ## Menubar
    ##

    def assemble_menubar(self, bar):

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_BUTTON)

        bar.add("/_File")
        bar.add("/_Edit")
        bar.add("/_View")
        bar.add("/_Actions")
        bar.add("/_Help")

        bar.add("/File/_Connect...",
                callback=lambda x:rcd_util.connect_to_server(),
                pixbuf_name="connect",
                accelerator="<Control>O")

        bar.add("/File/sep", is_separator=1)

        def install_file_sensitive_fn():
            return rcd_util.check_server_permission("install")

        bar.add("/File/Install From _File...",
                sensitive_fn=install_file_sensitive_fn,
                callback=lambda x:red_installfiles.install_local(self))

        def install_url_sensitive_fn():
            return rcd_util.check_server_permission("install") and \
                   red_installfiles.can_install_remote()

        bar.add("/File/Install From _URL...",
                sensitive_fn=install_url_sensitive_fn,
                callback=lambda x:red_installfiles.install_remote(self))

        bar.add("/File/sep2", is_separator=1)

        ##
        ## Mount command
        ##

        def mount_callback(app):
            app.open_or_raise_window(red_mount.MountWindow)

        def mount_sensitive_fn():
            return rcd_util.check_server_permission("superuser")

        bar.add("/File/_Mount Directory...",
                callback=mount_callback,
                sensitive_fn=mount_sensitive_fn,
                accelerator="<Control>M")

        ##
        ## Unmount command
        ##

        def unmount_callback(app):
            app.open_or_raise_window(red_mount.UnmountWindow)

        def unmount_sensitive_fn():
            return rcd_util.check_server_permission("superuser") and \
                   red_mount.has_mounted_channels()

        bar.add("/File/U_nmount Directory...",
                callback=unmount_callback,
                sensitive_fn=unmount_sensitive_fn,
                accelerator="<Control>U")
        

        bar.add("/File/sep3", is_separator=1)

        ##
        ## Activate
        ##

        def activate_sensitive_fn():
            return rcd_util.check_server_permission("superuser")

        bar.add("/File/_Activate...",
                callback=lambda x:self.open_or_raise_window(red_activation.ActivationWindow),
                sensitive_fn=activate_sensitive_fn)

        bar.add("/File/sep4", is_separator=1)
        
        bar.add("/File/Quit",
                stock=gtk.STOCK_QUIT,
                callback=lambda x:self.shutdown())


        ##
        ## Select all/none
        ##

        def select_all_sensitive_cb():
            comp = self.get_component()
            if not comp:
                return 0
            return comp.select_all_sensitive()

        bar.add("/Edit/Select _All",
                callback=lambda x:self.select_all_cb(1),
                accelerator="<Control>a",
                sensitive_fn=select_all_sensitive_cb)

        bar.add("/Edit/Select _None",
                callback=lambda x:self.select_all_cb(0),
                sensitive_fn=select_all_sensitive_cb,
                accelerator="<Shift><Control>A")

        bar.add("/Edit/sep", is_separator=1)

        bar.add("/Edit/Channel _Subscriptions...",
                callback=lambda x:self.open_or_raise_window(red_subscriptions.SubscriptionsWindow),
                pixbuf=red_pixbuf.get_pixbuf("subscribed",
                                             width=width, height=height),
                accelerator="<Control>B")

        bar.add("/Edit/_Preferences...",
                stock=gtk.STOCK_PREFERENCES,
                callback=lambda x:self.open_or_raise_window(red_prefs.PrefsWindow))

        bar.add("/Edit/_Users...",
                callback=lambda x:self.open_or_raise_window(red_users.UsersWindow))

        ##
        ## Sidebar
        ##

        def checked_get_cb():
            return self.sidebar.get_property("visible")
        def checked_set_cb(flag):
            self.sidebar.change_visibility()

        bar.add("/View/_Sidebar",
                checked_get=checked_get_cb,
                checked_set=checked_set_cb)

        bar.add("/View/Advanced Search Options",
                checked_get=red_searchbox.show_advanced_get,
                checked_set=red_searchbox.show_advanced_set)

        bar.add("/View/sep", is_separator=1)

        bar.add("/View/Package _Information...",
                pixbuf_name="info",
                callback=lambda x:self.package_info_cb(),
                sensitive_fn=self.info_sensitive_cb,
                accelerator="<Control>I")

        bar.add("/View/sep1", is_separator=1)

        bar.add("/View/_Daemon Information...",
                callback=red_serverinfo.view_server_info_cb)
        bar.add("/View/sep2", is_separator=1)

        ##
        ## Run Transaction
        ##

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)

        bar.add("/Actions/Run _Transaction",
                image=image,
                callback=run_transaction_cb,
                sensitive_fn=red_pendingops.pending_ops_exist,
                accelerator="<Control>X")

        ##
        ## Verify System Dependencies
        ##

        def verify_and_refresh_sensitive_cb():
            return self.sidebar.get_property("sensitive")
                
        bar.add("/Actions/_Verify System Dependencies",
                callback=verify_deps_cb,
                sensitive_fn=verify_and_refresh_sensitive_cb,
                accelerator="<Control>D")

        bar.add("/Actions/sep1", is_separator=1)

        ##
        ## Install Package
        ##

        bar.add("/Actions/I_nstall Package",
                pixbuf_name="to-be-installed",
                callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_INSTALLED),
                sensitive_fn=self.install_sensitive_cb)

        ##
        ## Remove Package
        ##

        bar.add("/Actions/_Remove Package",
                pixbuf_name="to-be-removed",
                callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_REMOVED),
                sensitive_fn=self.remove_sensitive_cb)

        ##
        ## Cancel Action
        ##

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)

        bar.add("/Actions/_Cancel Action",
                image=image,
                callback=lambda x:self.set_package_action_cb(red_pendingops.NO_ACTION),
                sensitive_fn=self.cancel_sensitive_cb)

        bar.add("/Actions/sep2", is_separator=1)

        ##
        ## Refresh Channel Data
        ##

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_MENU)

        bar.add("/Actions/Re_fresh Channel Data",
                image=image,
                callback=refresh_cb,
                sensitive_fn=verify_and_refresh_sensitive_cb,
                accelerator="<Control>R")

        bar.add("/Help/_About...",
                callback=lambda x:red_about.About().show())

        if red_main.debug:
            self.assemble_debug_menubar(bar)


    def assemble_debug_menubar(self, bar):
        
        bar.add("/Debug")
        
        bar.add("/Debug/Exercise Components",
                callback=lambda x: x.exercise_components())

        bar.add("/Debug/Exercise Menu Items",
                callback=lambda x: x.menubar.exercise_menubar())

        self.__throb_debug = 0

        def throb_checked_get():
            return self.__throb_debug

        def throb_checked_set(flag):
            self.__throb_debug = flag
            if flag:
                self.busy_start()
            else:
                self.busy_stop()
        bar.add("/Debug/Throb",
                checked_get=throb_checked_get,
                checked_set=throb_checked_set)


    def register_component(self, comp):

        self.shortcut_bar.add(comp,
                              lambda x:self.activate_component(comp))

        # We need to make the component menu items checked
        # instead of radio-style, because with a radio group you
        # always have to have exactly one item set: when a non-navigable
        # component is on the screen (like the dep resolution page),
        # the component gets reset if you open any menu.
        def checked_get_cb():
            return id(self.get_component()) == id(comp)
        def checked_set_cb(flag):
            if flag:
                self.activate_component(comp)

        ln = comp.long_name()
        if comp.access_key():
            index = string.index(string.lower(ln),
                                 string.lower(comp.access_key()))
            ln = ln[:index] + "_" + ln[index:]
        
        self.menubar.add("/View/" + ln,
                         checked_get=checked_get_cb,
                         checked_set=checked_set_cb,
                         accelerator=comp.accelerator())


        # We activate the first component that gets registered.
        if not self.components:
            gtk.idle_add(self.activate_component, comp)

        self.components.append(comp)


    def activate_component(self, comp):
        old_comp = self.get_component()
        if id(old_comp) == id(comp):
            return

        if comp.is_busy():
            self.busy_start()

        self.set_component(comp)

        if old_comp and old_comp.is_busy():
            self.busy_stop()

        # Clear the status bar, update toolbar
        self.statusbar.pop(0)
        self.toolbar.sensitize_toolbar_items()
        self.actionbar.sensitize_actionbar_items()

        # Show the new component, hide the old one.
        comp.visible(1)
        comp.set_parent(self)
        comp.activated()
        if not comp.show_actionbar():
            self.actionbar.hide()
        else:
            self.actionbar.show()

        if old_comp:
            old_comp.visible(0)
            old_comp.deactivated()
            old_comp.set_parent(None)

        self.set_title(None, comp.name())
        
        # Force the componet to emit a display event.  This causes
        # it to get displayed.
        comp.pull_widget()

    def push_component(self, new_comp):
        old_comp = self.get_component()
        if old_comp:
            self.component_stack.append(old_comp)
        self.activate_component(new_comp)

    def pop_component(self):
        if self.component_stack:
            new_comp = self.component_stack.pop()
            if new_comp:
                self.activate_component(new_comp)

    def exercise_components(self):
        interval = 1000
        when = interval
        for c in self.components:
            gtk.timeout_add(when, lambda x, y: x.push_component(y), self, c)
            when += interval
        for c in self.components:
            gtk.timeout_add(when, lambda x: x.pop_component(), self)
            when += interval


    def busy_start(self):
        self.throbber.start()
        self.busy_count += 1
        self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))

    def busy_stop(self):
        self.throbber.stop()
        if self.busy_count > 0:
            self.busy_count -= 1
        if self.busy_count == 0:
            self.window.set_cursor(None)

    ###
    ### Handlers for PendingOpsListener
    ###

    def pendingops_changed(self, pkg, key, value, old_value):
        def sensitize_run_cb(app):
            have_pending = red_pendingops.pending_ops_exist()
            app.toolbar.run.set_sensitive(have_pending)
        gtk.idle_add(sensitize_run_cb, self)
        
    ###
    ### Handlers for Component signals (via the ComponentListener API)
    ###

    def do_component_display(self, widget):
        # Clean any old widgets out of self.container,
        # then stick in our new widget and show it.
        for c in self.container.get_children():
            self.container.remove(c)
        self.container.add(widget)
        widget.show()

    def do_component_switch(self, new_comp):
        self.activate_component(new_comp)

    do_component_push = push_component
    do_component_pop  = pop_component

    def do_component_message_push(self, msg, context_id):
        self.statusbar.pop(0) # always pop off transient messages
        self.statusbar.push(context_id, msg)

    def do_component_message_pop(self, context_id):
        self.statusbar.pop(context_id)

    def do_component_busy(self, flag):
        if flag:
            self.busy_start()
        else:
            self.busy_stop()
        
    def do_component_package_selected(self, pkg):
        self.toolbar.sensitize_toolbar_items()
        self.actionbar.sensitize_actionbar_items()
