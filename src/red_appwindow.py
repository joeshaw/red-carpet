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
import red_header, red_menubar, red_sidebar
import red_transaction
import red_component
import red_pendingview

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

class AppWindow(gtk.Window, red_component.ComponentListener):

    # The return value is for the benefit of our delete_event handler.
    def shutdown(self):
        if red_transaction.ok_to_quit(self):
            gtk.mainquit()
            return 0
        return 1

    def assemble_menubar(self, bar):

        bar.add("/_File")
        bar.add("/_Edit")
        bar.add("/_View")
        bar.add("/_Actions")
        bar.add("/_Settings")
        bar.add("/_Help")

        bar.add("/File/Quit",
                stock=gtk.STOCK_QUIT,
                callback=lambda x:self.shutdown())

        bar.add("/Actions/Refresh Channel Data",
                callback=refresh_cb)
        bar.add("/Actions/sep", is_separator=1)

        def set_show_sidebar_cb(x):
            self.show_sidebar = x
            if x:
                self.sidebar.show_all()
            else:
                self.sidebar.hide()

        bar.add("/View/Show Sidebar",
                checked_get=lambda: self.show_sidebar,
                checked_set=set_show_sidebar_cb)

        bar.add("/View/sep", is_separator=1)

        bar.add("/View/Server Information",
                callback=view_server_info_cb)
        
        bar.add("/Edit/Foo")

        bar.add("/Settings/Foo")
        bar.add("/Help/Foo")


    def __init__(self, server):

        gtk.Window.__init__(self)
        red_component.ComponentListener.__init__(self)

        self.server = server
        self.component_stack = []

        self.busy_count = 0
        self.busy_handler = 0

        self.table = gtk.Table(2, 6)
        self.add(self.table)
        self.table.show()

        self.components = []
        self.current_comp = None
        self.comp_display_id = 0
        self.comp_message_id = 0
        self.comp_switch_id = 0

        self.menubar = red_menubar.MenuBar()
        self.menubar.set_user_data(self)
        self.assemble_menubar(self.menubar)
        
        self.sidebar = red_sidebar.SideBar()
        self.show_sidebar = 0
        
        self.transactionbar = red_transaction.TransactionBar(self)

        self.progressbar = gtk.ProgressBar()
        self.statusbar = gtk.Statusbar()


        self.header = gtk.EventBox()

        # A box to put component widgets in.  We use an EventBox
        # instead of just a [HV]Box so that we can control the
        # background color if we want to.
        self.container = gtk.EventBox()

        self.table.attach(self.menubar,
                          0, 2, 0, 1,
                          gtk.FILL, gtk.FILL,
                          0, 0)
        self.menubar.show()

        self.table.attach(self.sidebar,
                          0, 1, 1, 5,
                          gtk.FILL, gtk.FILL,
                          0, 0)
        if self.show_sidebar:
            self.sidebar.show_all()
            
        self.table.attach(self.header,
                          1, 2, 1, 2,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)
        self.header.show()

        self.table.attach(self.container,
                          1, 2, 2, 5,
                          gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND,
                          0, 0)
        self.container.show()

        south = gtk.HBox(0, 0)
        south.pack_start(self.transactionbar, 0, 1, 2)
        south.pack_start(self.progressbar, 0, 1, 2)
        south.pack_start(self.statusbar, 1, 1, 2)
        south.show_all()
        self.table.attach(south,
                          0, 2, 5, 6,
                          gtk.FILL, gtk.FILL,
                          0, 2)
        south.show()

        self.connect("delete_event", lambda x, y:self.shutdown())

    def register_component(self, comp):

        self.sidebar.add(label=comp.name(),
                         pixbuf=comp.pixbuf(),
                         callback=lambda: self.activate_component(comp))

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
        self.menubar.add("/Actions/" + comp.long_name(),
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

        # Set the header
        hdr = red_header.Header(comp.pixbuf(), comp.long_name())
        hdr.show_all()
        for c in self.header.get_children():
            self.header.remove(c)
        self.header.add(hdr)

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
        def busy_cb(app):
            if app.busy_count > 0:
                app.progressbar.pulse()
                return 1
            app.progressbar.set_fraction(0)
            return 0
        gtk.timeout_add(100, busy_cb, self)
        self.busy_count += 1

    def busy_stop(self):
        if self.busy_count > 0:
            self.busy_count -= 1
        
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

    def do_component_message(self, msg):
        self.statusbar.push(0, msg)

    def do_component_busy(self, flag):
        if flag:
            self.busy_start()
        else:
            self.busy_stop()
        
        
