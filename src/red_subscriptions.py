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

import gtk
import red_main
import red_channelmodel

model = None

class SubscriptionsView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        global model
        if not model:
            model = red_channelmodel.ChannelModel()

        view = red_channelmodel.make_channel_view(model)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(view)

class SubscriptionsWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, "%s Channel Subscriptions" % red_main.red_name)

        self.set_default_size(500, 300)

        view = SubscriptionsView()
        view.show()
        self.vbox.add(view)

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x:self.destroy())

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
