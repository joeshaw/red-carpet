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

import red_header, red_menubar, red_sidebar, red_statusbar
import red_transaction
import red_component
import red_pendingview

def refresh_cb(app):
    # FIXME: this should be in a try
    stuff_to_poll = app.server.rcd.packsys.refresh_all_channels()

    pend = red_pendingview.PendingView()
    win = gtk.Window()
    win.add(pend)
    win.show_all()

    pend.set_server(app.server)
    pend.set_pending_list(stuff_to_poll)
    

class AppWindow(gtk.Window):

    def shutdown(self):
        gtk.mainquit()
        #sys.exit(0)

    def assemble_menubar(self, bar):

        bar.add("/_File")
        bar.add("/_Edit")
        bar.add("/_View")
        bar.add("/_Actions")
        bar.add("/S_ubscriptions")
        bar.add("/_Settings")
        bar.add("/_Help")

        bar.add("/File/Quit",
                stock=gtk.STOCK_QUIT,
                callback=lambda x:self.shutdown())

        bar.add("/Actions/Refresh Channel Data",
                callback=refresh_cb)
        
        bar.add("/Edit/Foo")
        bar.add("/View/Foo")
        bar.add("/Subscriptions/Foo")
        bar.add("/Settings/Foo")
        bar.add("/Help/Foo")


    def __init__(self, server):

        gtk.Window.__init__(self)

        self.server = server

        self.paned = gtk.VPaned()
        self.add(self.paned)

        self.table = gtk.Table(2, 5)
        self.paned.pack1 (self.table, 1, 1)

        self.components = []
        self.current_comp = None
        self.comp_display_id = 0

        self.menubar = red_menubar.MenuBar()
        self.menubar.set_user_data(self)
        self.assemble_menubar(self.menubar)
        
        self.sidebar = red_sidebar.SideBar()

        self.header  = gtk.EventBox()
        self.upper   = gtk.EventBox()
        self.lower   = gtk.EventBox()
        self.mainbox = gtk.EventBox()

        self.transaction = red_transaction.Transaction()
        self.statusbar = red_statusbar.StatusBar(self.transaction)

        style = self.mainbox.get_style().copy()
        color = self.mainbox.get_colormap().alloc_color("white")
        style.bg[gtk.STATE_NORMAL] = color
        self.mainbox.set_style(style)

        self.main = gtk.ScrolledWindow()
        self.main.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.mainbox.add(self.main)

        self.table.attach(self.menubar,
                          0, 2, 0, 1,
                          gtk.FILL, gtk.FILL,
                          0, 0)

        self.table.attach(self.sidebar,
                          0, 1, 1, 5,
                          gtk.FILL, gtk.FILL,
                          0, 0)

        self.table.attach(self.header,
                          1, 2, 1, 2,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)

        self.table.attach(self.upper,
                          1, 2, 2, 3,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)

        self.table.attach(self.mainbox,
                          1, 2, 3, 4,
                          gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND,
                          0, 0)

        self.table.attach(self.lower,
                          1, 2, 4, 5,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)

        self.paned.pack2(self.statusbar, 1, 0)

        self.connect("delete_event", lambda x, y:self.shutdown())

    def register_component(self, comp):

        self.sidebar.add(label=comp.name(),
                         pixbuf=comp.pixbuf(),
                         callback=lambda: self.activate_component(comp))

        comp.set_server(self.server)
        comp.set_transaction(self.transaction)

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

        # Show the new component, hide the old one.
        comp.visible(1)
        if self.current_comp:
            self.current_comp.visible(0)

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

        # Listen for display signals from the the new component
        if comp:
            self.comp_display_id = comp.connect("display",
                                                display_cb,
                                                self)
