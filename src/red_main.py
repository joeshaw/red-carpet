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
import os
import gtk
import ximian_xmlrpclib
import packagemodel

def thrash_model(source,view):
    view.set_model(None)
    view.set_model(source)

def main(version):
    ## Make contact with the daemon.
    ## We assume local access only
    url = "/tmp/rcd"
    username = None
    password = None

    transport_debug = os.environ.has_key("RC_TRANSPORT_DEBUG")

    try:
        server = ximian_xmlrpclib.Server(url,
                                         auth_username=username,
                                         auth_password=password,
                                         verbose=transport_debug)
    except:
        sys.stderr.write("Unable to connect to the daemon.\n")
        sys.exit(1)

    store = packagemodel.PackageModel(server)
    store.set_query([["name", "contains", "gnome"]])

    view = gtk.TreeView(store)

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
    store.connect("sync", thrash_model, view)

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    sw.add(view)

    win = gtk.Window()
    win.add(sw)

    win.show_all()
    win.connect("delete_event",
                lambda x,y:sys.exit(0))

    gtk.main()
    
    
