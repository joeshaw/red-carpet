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
import rcd_util
import red_main
import ximian_xmlrpclib
import red_settings

class ActivationWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, "Group Activation")
        self.build()
        self.fill()

    def build(self):
        table = gtk.Table(2, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label("Email:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label("Activation Code:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        self.email = gtk.Entry()
        table.attach_defaults(self.email, 1, 2, 0, 1)

        self.code = gtk.Entry()
        table.attach_defaults(self.code, 1, 2, 1, 2)

        table.show_all()
        self.vbox.add(table)

        button = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        button.connect("clicked", lambda x:self.destroy())

        button = self.add_button("Activate", gtk.RESPONSE_CLOSE)
        button.grab_default()
        button.connect("clicked", self.activate)

    def fill(self):
        config = red_settings.get_config()
        email = config.get("Activation/email")
        if email:
            self.email.set_text(email)

    def activate(self, button):
        email = self.email.get_text()
        code = self.code.get_text()

        if not email or not code:
            dialog = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                       "Please fill in both email and activation code.")
            dialog.run()
            dialog.destroy()
            return

        server = rcd_util.get_server()
        err = None

        try:
            success = server.rcd.system.activate(code, email)
        except ximian_xmlrpclib.Fault, f:
            if f.faultCode == rcfault.undefined_method:
                err = "This daemon does not support activation."
            else:
                err = "Unknown error."

        if err or not success:
            if not err:
                err = "System could not be activated: Invalid activation code or email address."

            dialog = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, err)
            dialog.run()
            dialog.destroy()
        else:
            config = red_settings.get_config()
            config.set("Activation/email", email)
            dialog = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                       "System successfully activated.")
            dialog.run()
            dialog.destroy()
            rcd_util.reset_channels()

        self.destroy()
