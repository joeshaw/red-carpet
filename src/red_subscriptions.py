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

    def pixbuf(self):
        return "subscribed"

    def construct(self):
        channels = rcd_util.get_all_channels()

        rows = len(channels) * 4
        cols = 3

        table = gtk.Table(rows, cols, 0)

        r = 0
        for c in channels:

            # a spacer
            table.attach(gtk.VBox(0, 0),
                         0, 3, r, r+1,
                         0, gtk.EXPAND | gtk.FILL,
                         0, 8)

            r = r + 1

            pixbuf = rcd_util.get_channel_icon(c["id"])
            img = gtk.Image()
            img.set_from_pixbuf(pixbuf)
            img.show()
            table.attach(img,
                         0, 1, r, r+2,
                         0, 0,
                         0, 0)

            label = gtk.Label("")
            label.set_alignment(0, 0)
            label.set_markup("<b>%s</b>" % c["name"])
            label.show()
            table.attach(label,
                         1, 2, r, r+1,
                         gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL,
                         0, 0)

            view = gtk.TextView()
            view.get_buffer().set_text(c["description"])
            view.set_wrap_mode(gtk.WRAP_WORD)
            table.attach(view,
                         1, 2, r+1, r+2,
                         gtk.FILL, gtk.FILL,
                         0, 0)

            b = gtk.Button("Foo!")
            b.show()
            table.attach(b,
                         2, 3, r, r+2,
                         gtk.FILL, gtk.FILL,
                         0, 0)

            def popup(self, channel):
                win = gtk.Window()
                info = red_channelinfo.ChannelInfo()
                info.set_channel(channel)
                win.add(info)
                win.show_all()

            b.connect("clicked", popup, c)

            
            r = r + 3

        table.show_all()

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
