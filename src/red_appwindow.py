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

class AppWindow(gtk.Window):

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

        self.server = server

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

        self.statusbar = gtk.Statusbar()

        self.header  = gtk.EventBox()
        self.upper   = gtk.EventBox()
        self.lower   = gtk.EventBox()
        self.main    = gtk.EventBox()

        style = self.main.get_style().copy()
        color = self.main.get_colormap().alloc_color("white")
        style.bg[gtk.STATE_NORMAL] = color
        self.main.set_style(style)

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

        self.table.attach(self.upper,
                          1, 2, 2, 3,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)
        self.upper.show()

        self.table.attach(self.main,
                          1, 2, 3, 4,
                          gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND,
                          0, 0)
        self.main.show()

        self.table.attach(self.lower,
                          1, 2, 4, 5,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)
        self.lower.show()

        south = gtk.HBox(0, 0)
        south.pack_start(self.transactionbar, 0, 1, 2)
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

        self.menubar.add("/Actions/" + comp.long_name(),
                         radiogroup="actions",
                         radio_get=lambda x=comp: self.current_comp,
                         radio_set=lambda x:self.activate_component(x),
                         radiotag=comp)

        comp.set_server(self.server)

        # We activate the first component that gets registered.
        if not self.components:
            self.activate_component(comp)

        self.components.append(comp)


    def switch_children(self, type, widget):
        if type == "header":
            box = self.header
        elif type == "upper":
            box = self.upper
        elif type == "lower":
            box = self.lower
        elif type == "main":
            box = self.main
        else:
            print "Unknown type '%s'" % type
            assert 0
            
        for c in box.get_children():
            box.remove(c)
            
        if not widget:
            widget = gtk.EventBox()
            
        box.add(widget)
        widget.show()


    def activate_component(self, comp):

        # Disconnect from the old component's display signal
        if self.comp_display_id:
            self.current_comp.disconnect(self.comp_display_id)
            self.comp_display_id = 0

        # Disconnect from the old component's message signal
        if self.comp_message_id:
            self.current_comp.disconnect(self.comp_message_id)
            self.comp_message_id = 0

        # Disconnect from the old component's switch signal
        if self.comp_switch_id:
            self.current_comp.disconnect(self.comp_switch_id)
            self.comp_switch_id = 0

        # Clear the status bar
        self.statusbar.pop(0)

        # Show the new component, hide the old one.
        comp.visible(1)
        comp.set_parent(self)
        if self.current_comp:
            self.current_comp.visible(0)
            self.current_comp.set_parent(None)

        self.current_comp = comp

        # Set the header
        hdr = red_header.Header(comp.pixbuf(), comp.long_name())
        hdr.show_all()
        self.switch_children("header", hdr)

        # Handle all of the widget reparenting
        for t in red_component.valid_widget_types:
            self.switch_children(t, comp.get(t))

        def display_cb(c, type, w, win):
            win.switch_children(type, w)

        def message_cb(c, msg, win):
            win.statusbar.push(0, msg)

        def switch_cb(c, win):
            win.activate_component(c)

        # Listen for display and message signals from the the new component
        if comp:
            self.comp_display_id = comp.connect("display",
                                                display_cb,
                                                self)
            self.comp_message_id = comp.connect("message",
                                                message_cb,
                                                self)
            self.comp_switch_id = comp.connect("switch",
                                               switch_cb,
                                               self)
