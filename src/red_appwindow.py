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

import sys, gtk

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

def refresh_cb(app):
    try:
        stuff_to_poll = app.server.rcd.packsys.refresh_all_channels()
    except ximian_xmlrpclib.Fault, f:
        rcd_util.dialog_from_fault(f, parent=app)
        return

    pend = red_pendingview.PendingView_Simple(title="Refreshing channel data",
                                              parent=app)
    pend.set_label("Downloading channel information")
    pend.show_all()
    pend.set_pending_list(stuff_to_poll)

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

class AppWindow(gtk.Window, red_component.ComponentListener):

    def __init__(self, server):

        gtk.Window.__init__(self)
        red_component.ComponentListener.__init__(self)

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

        self.menubar = red_menubar.MenuBar(self.accel_group)
        self.menubar.set_user_data(self)
        self.assemble_menubar(self.menubar)

        self.transient_windows = {}

        self.transactionbar = red_transaction.TransactionBar(self)

        self.progressbar = gtk.ProgressBar()
        self.statusbar = gtk.Statusbar()

        # FIXME: Tambet will fix this tomorrow :)
##        icon_size = self.toolbar.get_icon_size()
##        width, height = gtk.icon_size_lookup(icon_size)
        self.throbber = red_throbber.Throbber(24, 24)

        # A box to put component widgets in.  We use an EventBox
        # instead of just a [HV]Box so that we can control the
        # background color if we want to.
        self.container = gtk.EventBox()
        self.container.set_border_width(6)

        self.vbox.pack_start(self.menubar, expand=0, fill=1)
        self.menubar.show()

        throbbox = gtk.Frame(None)
        throbbox.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        throbbox.set_border_width(2)
        throbbox.add(self.throbber)

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, expand=1, fill=1)

        self.sidebar = red_sidebar.SideBar()
        self.toolbar = self.sidebar.get_toolbar()

        self.go_button = self.sidebar.get_run_button()
        self.go_button.connect("clicked", lambda x,y:run_transaction_cb(y), self)
        self.sensitize_go_button(0)

        hbox.pack_start(self.sidebar, 0, 1)

        hbox.pack_start(self.container, expand=1, fill=1)
        hbox.show_all()

        south = gtk.HBox(0, 0)
        south.pack_start(self.transactionbar, 0, 1, 2)
        south.pack_start(self.statusbar, 1, 1, 2)
        south.show_all()
        self.vbox.pack_start(south, expand=0, fill=1)

        self.connect("delete_event", lambda x, y:self.shutdown())

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
            win.show()

    def select_all_cb(self, sel):
        comp = self.get_component()
        if not comp:
            return
        
        if sel:
            comp.select_all()
        else:
            comp.unselect_all()

    def assemble_menubar(self, bar):

        bar.add("/_File")
        bar.add("/_Edit")
        bar.add("/_View")
        bar.add("/_Help")

        bar.add("/File/Connect...",
                callback=lambda x:rcd_util.connect_to_server(1))

        bar.add("/File/sep", is_separator=1)

        def install_file_sensitive_fn():
            return rcd_util.check_server_permission("install")

        bar.add("/File/Install From File...",
                sensitive_fn=install_file_sensitive_fn,
                callback=lambda x:red_installfiles.install_local())

        def install_url_sensitive_fn():
            return rcd_util.check_server_permission("install") and \
                   red_installfiles.can_install_remote()

        bar.add("/File/Install From URL...",
                sensitive_fn=install_url_sensitive_fn,
                callback=lambda x:red_installfiles.install_remote())

        bar.add("/File/sep2", is_separator=1)

        ##
        ## Mount command
        ##

        def mount_callback(app):
            app.open_or_raise_window(red_mount.MountWindow)

        def mount_sensitive_fn():
            return rcd_util.check_server_permission("superuser")

        bar.add("/File/Mount Directory...",
                callback=mount_callback,
                sensitive_fn=mount_sensitive_fn)

        ##
        ## Unmount command
        ##

        def unmount_callback(app):
            app.open_or_raise_window(red_mount.UnmountWindow)

        def unmount_sensitive_fn():
            return rcd_util.check_server_permission("superuser") and \
                   red_mount.has_mounted_channels()

        bar.add("/File/Unmount Directory...",
                callback=unmount_callback,
                sensitive_fn=unmount_sensitive_fn)
        

        bar.add("/File/sep3", is_separator=1)

        ##
        ## Activate
        ##

        def activate_sensitive_fn():
            return rcd_util.check_server_permission("superuser")

        bar.add("/File/Activate...",
                callback=lambda x:self.open_or_raise_window(red_activation.ActivationWindow),
                sensitive_fn=activate_sensitive_fn)

        bar.add("/File/Refresh Channel Data",
                callback=refresh_cb)

        bar.add("/File/sep4", is_separator=1)

        bar.add("/File/Verify System Dependencies",
                callback=verify_deps_cb)

        bar.add("/File/sep5", is_separator=1)
        
        bar.add("/File/Quit",
                stock=gtk.STOCK_QUIT,
                callback=lambda x:self.shutdown())


        ##
        ## Select all/none

        def select_all_sensitive_cb():
            comp = self.get_component()
            if not comp:
                return 0
            return comp.select_all_sensitive()

        bar.add("/Edit/Select All",
                callback=lambda x:self.select_all_cb(1),
                accelerator="<Control>a",
                sensitive_fn=select_all_sensitive_cb)

        bar.add("/Edit/Select None",
                callback=lambda x:self.select_all_cb(0),
                sensitive_fn=select_all_sensitive_cb)

        bar.add("/Edit/sep", is_separator=1)

        bar.add("/Edit/Subscriptions...",
                callback=lambda x:self.open_or_raise_window(red_subscriptions.SubscriptionsWindow))

        bar.add("/Edit/Preferences...",
                stock=gtk.STOCK_PREFERENCES,
                callback=lambda x:self.open_or_raise_window(red_prefs.PrefsWindow))

        bar.add("/Edit/Users...",
                callback=lambda x:self.open_or_raise_window(red_users.UsersWindow))

        bar.add("/View/Server Information...",
                callback=red_serverinfo.view_server_info_cb)
        bar.add("/View/sep", is_separator=1)
        
        bar.add("/Help/About...",
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


    def sensitize_go_button(self, en):
        self.go_button.set_sensitive(en)

    def register_component(self, comp):

        self.toolbar.add(comp,
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
        
        self.menubar.add("/View/" + comp.long_name(),
                         checked_get=checked_get_cb,
                         checked_set=checked_set_cb,
                         accelerator=comp.accelerator())


        # We activate the first component that gets registered.
        if not self.components:
            self.activate_component(comp)

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

        # Clear the status bar
        self.statusbar.pop(0)

        # Show the new component, hide the old one.
        comp.visible(1)
        comp.set_parent(self)
        comp.activated()
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
        self.statusbar.push(context_id, msg)

    def do_component_message_pop(self, context_id):
        self.statusbar.pop(context_id)

    def do_component_busy(self, flag):
        if flag:
            self.busy_start()
        else:
            self.busy_stop()
        
        
