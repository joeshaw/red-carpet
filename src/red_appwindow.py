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

import red_menubar, red_sidebar

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


    def assemble_sidebar(self, bar):

        bar.add(pixbuf="summary",
                label="Summary")

        bar.add(pixbuf="featured",
                label="Browse by Channel")

        bar.add(pixbuf="news",
                label="News")
        

    def __init__(self):

        gtk.Window.__init__(self)

        self.table = gtk.Table(2, 3)
        self.add (self.table)

        self.menubar = red_menubar.MenuBar()
        self.assemble_menubar(self.menubar)
        
        self.sidebar = red_sidebar.SideBar()
        self.assemble_sidebar(self.sidebar)

        self.control = gtk.EventBox()

        self.main = gtk.EventBox()
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
                          0, 1, 1, 3,
                          gtk.FILL, gtk.FILL,
                          0, 0)

        self.table.attach(self.control,
                          1, 2, 1, 2,
                          gtk.FILL | gtk.EXPAND, gtk.FILL,
                          0, 0)

        self.table.attach(self.sw,
                          1, 2, 2, 3,
                          gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND,
                          0, 0)

        self.connect("delete_event", lambda x, y:self.shutdown())

    def set_control_widget(self, item):
        for c in self.control.get_children():
            self.control.remove(c)
        self.control.add(item)
        item.show()

    def set_main_widget(self, item):
        for c in self.main.get_children():
            self.main.remove(c)
        self.main.add(item)
        item.show()
        
