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

import sys
import gobject, gtk
import string

import ximian_xmlrpclib

import rcd_util
import red_extra
import red_menubar
import red_transaction
import red_installfiles
import red_component
import red_pendingview
import red_pixbuf
import red_prefs
import red_subscriptions
import red_users
import red_throbber
import red_activation
import red_about
import red_settings
import red_mount

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

def view_server_info_cb(app):

    # We only allow one server info window at a time
    if getattr(app, "server_info_window", None):
        app.server_info_window.destroy()
    
    server = rcd_util.get_server()
    try:
        results = server.rcd.system.ping()
    except:
        results = None

    if results:
        dialog_type = gtk.MESSAGE_INFO

        messages = ["The server identified itself as:", ""]

        if results.has_key("name"):
            messages.append("%s" % results["name"])

        if results.has_key("copyright"):
            messages.append(results["copyright"])

        messages.append("")

        if results.has_key("distro_info"):
            messages.append("System type: %s" % results["distro_info"])

        if results.has_key("server_url"):
            messages.append("Server URL: %s" % results["server_url"])

        if results.get("server_premium", 0):
            messages.append("Server supports enhanced features.")

    else: # couldn't ping the server

        dialog_type = gtk.MESSAGE_WARNING
        messages = ["Unable to contact the server."]

    dialog = gtk.MessageDialog(app, 0, dialog_type, gtk.BUTTONS_OK,
                               string.join(messages, "\n"))

    def destroy_cb(x, y, z):
        z.server_info_window = None
        x.destroy()
    dialog.connect("response", destroy_cb, app)
    dialog.show_all()

    app.server_info_window = dialog

def connect_cb():
    while 1:
        d = red_settings.ConnectionWindow()
        response = d.run()
        if response == gtk.RESPONSE_ACCEPT:
            url, username, password = d.get_server_info()

            server = rcd_util.connect_to_server(url, username, password)

            if isinstance(server, ximian_xmlrpclib.Server):
                d.destroy()
                break
        else:
            d.destroy()
            break
    
class AppWindow(gtk.Window, red_component.ComponentListener):

    def __init__(self, server):

        gtk.Window.__init__(self)
        red_component.ComponentListener.__init__(self)

        self.server = server
        self.component_stack = []

        self.busy_count = 0
        self.busy_handler = 0

        self.vbox = gtk.VBox(0, 0)
        self.add(self.vbox)
        self.vbox.show()

        self.components = []
        self.current_comp = None
        self.comp_display_id = 0
        self.comp_message_id = 0
        self.comp_switch_id = 0

        self.menubar = red_menubar.MenuBar()
        self.menubar.set_user_data(self)
        self.assemble_menubar(self.menubar)

        self.toolbar = red_extra.Toolbar()
        self.toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)

        self.go_button = self.toolbar.append_item("Go!",
                                                  "Run transaction",
                                                  None,
                                                  red_pixbuf.get_widget("progress-config", width=24, height=24),
                                                  lambda x:red_transaction.resolve_deps_and_transact(self),
                                                  None)

        self.sensitize_go_button(0)

        self.toolbar.append_space()

        self.transient_windows = {}
        
        self.transactionbar = red_transaction.TransactionBar(self)

        self.progressbar = gtk.ProgressBar()
        self.statusbar = gtk.Statusbar()

        icon_size = self.toolbar.get_icon_size()
        width, height = gtk.icon_size_lookup(icon_size)
        self.throbber = red_throbber.Throbber(width, height)

        # A box to put component widgets in.  We use an EventBox
        # instead of just a [HV]Box so that we can control the
        # background color if we want to.
        self.container = gtk.EventBox()

        self.vbox.pack_start(self.menubar, expand=0, fill=1)
        self.menubar.show()

        throbbox = gtk.Frame(None)
        throbbox.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        throbbox.set_border_width(2)
        throbbox.add(self.throbber)

        toolbox = gtk.HBox()
        toolbox.pack_start(self.toolbar, expand=1, fill=1)
        toolbox.pack_end(throbbox, expand=0, fill=0)
        toolbox.show_all()

        self.vbox.pack_start(toolbox, expand=0, fill=1)

        self.vbox.pack_start(self.container, expand=1, fill=1)
        self.container.show()

        south = gtk.HBox(0, 0)
        south.pack_start(self.transactionbar, 0, 1, 2)
        south.pack_start(self.statusbar, 1, 1, 2)
        south.show_all()
        self.vbox.pack_start(south, expand=0, fill=1)

        self.connect("delete_event", lambda x, y:self.shutdown())

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

    def assemble_menubar(self, bar):

        bar.add("/_File")
        bar.add("/_Edit")
        bar.add("/_View")
        bar.add("/_Help")

        bar.add("/File/Connect...",
                callback=lambda x:connect_cb())

        bar.add("/File/sep", is_separator=1)

        bar.add("/File/Install From File...",
                callback=lambda x:red_installfiles.install_local())

        bar.add("/File/Install From URL...",
                callback=lambda x:red_installfiles.install_remote(),
                sensitive_fn=red_installfiles.can_install_remote)

        bar.add("/File/sep2", is_separator=1)

        bar.add("/File/Mount Directory...",
                callback=lambda x:red_mount.select_and_mount())

        bar.add("/File/Unmount Directory...",
                callback=lambda x:self.open_or_raise_window(red_mount.UnmountWindow))

        bar.add("/File/sep3", is_separator=1)

        bar.add("/File/Activate...",
                callback=lambda x:self.open_or_raise_window(red_activation.ActivationWindow))

        bar.add("/File/Refresh Channel Data",
                callback=refresh_cb)

        bar.add("/File/sep4", is_separator=1)
        
        bar.add("/File/Quit",
                stock=gtk.STOCK_QUIT,
                callback=lambda x:self.shutdown())

        bar.add("/Edit/Subscriptions...",
                callback=lambda x:self.open_or_raise_window(red_subscriptions.SubscriptionsWindow))

        bar.add("/Edit/Preferences...",
                stock=gtk.STOCK_PREFERENCES,
                callback=lambda x:self.open_or_raise_window(red_prefs.PrefsWindow))

        bar.add("/Edit/Users...",
                callback=lambda x:self.open_or_raise_window(red_users.UsersWindow))

        bar.add("/View/Server Information...",
                callback=view_server_info_cb)
        bar.add("/View/sep", is_separator=1)
        
        bar.add("/Help/About...",
                callback=lambda x:red_about.About().show())

    def sensitize_go_button(self, en):
        self.go_button.set_sensitive(en)

    def register_component(self, comp):

        self.toolbar.append_item(comp.name(),
                                 comp.long_name(),
                                 None,
                                 red_pixbuf.get_widget(comp.pixbuf(), width=24, height=24),
                                 lambda x:self.activate_component(comp),
                                 None)

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
                         checked_set=checked_set_cb)


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
        if old_comp:
            old_comp.visible(0)
            old_comp.set_parent(None)

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
        
        
