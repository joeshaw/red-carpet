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

import red_header, red_menubar, red_sidebar

class AppWindow(gtk.Window):

    def shutdown(self):
        sys.exit(0)

    def assemble_menubar(self, bar):

        bar.add("/_File")
        bar.add("/_Edit")
        bar.add("/_View")
        bar.add("/S_ubscriptions")
        bar.add("/_Settings")
        bar.add("/_Help")

        bar.add("/File/Quit",
                stock=gtk.STOCK_QUIT,
                callback=lambda x:self.shutdown())
        bar.add("/Edit/Foo")
        bar.add("/View/Foo")
        bar.add("/Subscriptions/Foo")
        bar.add("/Settings/Foo")
        bar.add("/Help/Foo")


    def __init__(self, server):

        gtk.Window.__init__(self)

        self.server = server

        self.table = gtk.Table(2, 5)
        self.add (self.table)

        self.components = []

        self.menubar = red_menubar.MenuBar()
        self.assemble_menubar(self.menubar)
        
        self.sidebar = red_sidebar.SideBar()

        self.header = gtk.EventBox()
        self.upper  = gtk.EventBox()
        self.lower  = gtk.EventBox()
        self.main   = gtk.EventBox()

        style = self.main.get_style().copy()
        color = self.main.get_colormap().alloc_color("white")
        style.bg[gtk.STATE_NORMAL] = color
        self.main.set_style(style)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.sw.add_with_viewport(self.main)

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

        self.table.attach(self.sw,
                          1, 2, 3, 4,
                          gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND,
                          0, 0)

        self.table.attach(self.lower,
                          1, 2, 4, 5,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)


        self.connect("delete_event", lambda x, y:self.shutdown())


    def add_component(self, comp):
        
        self.sidebar.add(label=comp.name(),
                         pixbuf=comp.pixbuf(),
                         callback=lambda: self.set_component(comp))

        if not self.components:
            self.set_component(comp)

        self.components.append(comp)
        

    def set_component(self, comp):

        def switch_children(parent, child):
            for c in parent.get_children():
                parent.remove(c)
            if not child:
                child = gtk.EventBox()
            parent.add(child)
            child.show()

        self.component = comp

        comp.set_server(self.server)

        # Create a pure virtual component, which will return None
        # when asked for any widget.
        if not comp:
            comp = red_appcomponent.AppComponent()

        comp.prebuild()

        hdr = red_header.Header(comp.pixbuf(), comp.long_name())
        hdr.show_all()

        switch_children(self.header, hdr)
        switch_children(self.upper, comp.get_upper_widget())
        switch_children(self.main,  comp.get_main_widget())
        switch_children(self.lower, comp.get_lower_widget())

        comp.postbuild()

        # Might also need to hook up some signals, etc.

