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

import sys, string
import rcd_util
import gobject, gtk
import red_pixbuf, red_component, red_channelinfo
import red_channelmodel

class SubscriptionsComponent(red_component.Component):

    def name(self):
        return "Subscriptions"

    def long_name(self):
        return "Manage Subscriptions"

    def pixbuf(self):
        return "subscribed"

    def construct(self):
        channels = rcd_util.get_all_channels()

        model = red_channelmodel.ChannelModel()
        view = red_channelmodel.make_channel_view(model)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.add(view)
        view.show_all()

        return scrolled

    def build(self):
        widget = self.construct()
        self.display("main", widget)

    first_time = 1
    
    def visible(self, flag):
        if self.first_time:
            self.first_time = 0

            server = rcd_util.get_server()
            if not server.rcd.users.has_privilege("subscribe"):
                show_sub_privs_dialog()

        return red_component.Component.visible(self, flag)

def show_sub_privs_dialog():
    message_box = gtk.MessageDialog(None, # FIXME: Make transient of app
                                    0,
                                    gtk.MESSAGE_INFO,
                                    gtk.BUTTONS_OK,
                                    "You do not have permission to "
                                    "subscribe or unsubscribe from "
                                    "channels.  You will be unable "
                                    "to make any changes to the "
                                    "subscriptions.")

    def response_cb(dialog, response_id):
        dialog.destroy()

    message_box.connect("response", response_cb)
    message_box.show()
