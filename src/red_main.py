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

import sys, os
import gtk
import ximian_xmlrpclib
import rcd_util
import red_packagearray
import red_explodedview
import red_appwindow
import red_channeloption
import red_channelbrowse
import red_summary

def connect_to_server():
    ## Make contact with the daemon.
    ## We assume local access only
    url = "/var/run/rcd"
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

    rcd_util.register_server(server)

    return server

def opt_test(server):

    opt = red_channeloption.ChannelOption()
    app = red_appwindow.AppWindow()
    app.show_all()
    app.set_main_widget(opt)

def main(version):
    server = connect_to_server()

    app = red_appwindow.AppWindow(server)
    app.set_title("Red Carpet 2: Electric Boogaloo")
    app.show_all()

    app.register_component(red_summary.SummaryComponent())
    app.register_component(red_channelbrowse.ChannelBrowseComponent())

    gtk.main()
    


