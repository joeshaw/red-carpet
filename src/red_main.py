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

import sys, os, string
import gtk, gtk.glade
import ximian_xmlrpclib
import packagemodel, channelmodel

import rcd_util

import red_menubar, red_packagearray, red_packageview, red_header
import red_explodedview, red_appwindow


def build_main_window(server):
    xml = gtk.glade.XML ("red-carpet.glade")

    store = packagemodel.PackageModel(server)
    store.set_query([["name", "contains", "gnome"]])

    view = xml.get_widget("package_tree")
    view.set_model(store)

    col = gtk.TreeViewColumn("Installed",
                             gtk.CellRendererText(),
                             text=packagemodel.COLUMN_INSTALLED)
    view.append_column(col)

    col = gtk.TreeViewColumn("Channel",
                             gtk.CellRendererText(),
                             text=packagemodel.COLUMN_CHANNEL_NAME)
    view.append_column(col)

    col = gtk.TreeViewColumn("Name",
                             gtk.CellRendererText(),
                             text=packagemodel.COLUMN_NAME)
    view.append_column(col)

    col = gtk.TreeViewColumn("Version",
                             gtk.CellRendererText(),
                             text=packagemodel.COLUMN_EVR)
    view.append_column(col)

    # We have to thrash the model on a sync, because there is no way
    # for a TreeModel to emit a global "everything-or-anything-
    # has-changed" signal.  (I've bitched about this to jrb, so
    # hopefully it will be get fixed for gtk+ 2.2.)
    def thrash_model(source,view):
        view.set_model(None)
        view.set_model(source)
    store.connect("sync", thrash_model, view)

    # Channel tree
    store = channelmodel.ChannelModel(server)

    view = xml.get_widget("channel_tree")
    view.set_model(store)

    col = gtk.TreeViewColumn("Icon",
                             gtk.CellRendererPixbuf(),
                             pixbuf=channelmodel.COLUMN_ICON)

    view.append_column(col)

    col = gtk.TreeViewColumn("Name",
                             gtk.CellRendererText(),
                             text=channelmodel.COLUMN_NAME)
    view.append_column(col)

    # We have to thrash the model on a sync, because there is no way
    # for a TreeModel to emit a global "everything-or-anything-
    # has-changed" signal.  (I've bitched about this to jrb, so
    # hopefully it will be get fixed for gtk+ 2.2.)
    store.connect("sync", thrash_model, view)

    win = xml.get_widget("main_window")

    win.show_all()
    win.connect("delete_event",
                lambda x,y:sys.exit(0))


def menubar_test_window():

    bar = red_menubar.RedMenuBar(gtk.AccelGroup())

    bar.add("/Foo")
    bar.add("/Bar")

    bar.add("/Foo/Fooo", stock=gtk.STOCK_QUIT)
    bar.add("/Foo/XXXX")

    bar.blah = 1
    def foo_get():
        print "bar.blah is %d" % bar.blah
        return bar.blah
    def foo_set(x):
        bar.blah=x
        print "set bar.blah to %d" % bar.blah
        
    bar.add("/Foo/XXXX/YYYY", checked_set=foo_set, checked_get=foo_get)
    bar.add("/Foo/XXXX/blah", is_separator=1)
    bar.add("/Foo/XXXX/ZZZZ", checked_set=foo_set, checked_get=foo_get)

    bar.add("/Bar/Blah")

    win = gtk.Window()
    win.add(bar)
    win.show_all()

    win.connect("delete_event", lambda x,y:sys.exit(0))



def main(version):
    server = connect_to_server()

    query_test(server)

    gtk.main()
    
    
