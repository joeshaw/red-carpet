###
### Copyright (C) 2002-2003 Ximian, Inc.
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
import rcd_util
import red_main
import red_channelmodel
import red_thrashingtreeview

from red_gettext import _

model = None

class SubscriptionsView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        global model
        if not model:
            model = red_channelmodel.ChannelModel()

        view = self.make_channel_view()

        view.show_all()
        view.set_sensitive(rcd_util.check_server_permission("subscribe"))

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_sensitive(gtk.SHADOW_IN)
        self.add(view)

    def make_channel_view(self):
        global model

        view = red_thrashingtreeview.TreeView(model)

        def toggle_cb(cr, path, model):
            c = model.get_list_item(int(path))
            model.toggle_subscribed(c)

        toggle = gtk.CellRendererToggle()
        toggle.set_property("activatable", 1)
        col = gtk.TreeViewColumn(_("Subscribed"),
                                 toggle,
                                 active=red_channelmodel.COLUMN_SUBSCRIBED)
        toggle.connect("toggled", toggle_cb, model)
        view.append_column(col)

        col = gtk.TreeViewColumn()
        col.set_title(_("Channel Name"))
        r1 = gtk.CellRendererPixbuf()
        r2 = gtk.CellRendererText()
        col.pack_start(r1, 0)
        col.pack_start(r2, 0)
        col.set_attributes(r1, pixbuf=red_channelmodel.COLUMN_ICON)
        col.set_attributes(r2, text=red_channelmodel.COLUMN_NAME)
        view.append_column(col)

        return view

class SubscriptionsWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, _("%s Channel Subscriptions") % red_main.red_name)
        self.set_default_size(500, 300)

        view = SubscriptionsView()
        view.show()

        hbox = gtk.HBox()
        hbox.show()
        hbox.pack_start(view, expand=1, fill=1, padding=12)
        
        self.vbox.pack_start(hbox, expand=1, fill=1, padding=12)

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.grab_default()
        button.connect("clicked", lambda x:self.destroy())

def show_sub_privs_dialog():
    message_box = gtk.MessageDialog(None, # FIXME: Make transient of app
                                    0,
                                    gtk.MESSAGE_INFO,
                                    gtk.BUTTONS_OK,
                                    _("You do not have permission to "
                                    "subscribe or unsubscribe from "
                                    "channels.  You will be unable "
                                    "to make any changes to the "
                                    "subscriptions."))

    def response_cb(dialog, response_id):
        dialog.destroy()

    message_box.connect("response", response_cb)
    message_box.show()
