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
import ximian_xmlrpclib
import red_settings, red_services
from red_gettext import _

class ActivationWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, _("Group Activation"))
        self.build()
        self.fill()

    def sensitize_window_elements(self):
        any_services = self.service_opt.get_service_id() is not None

        self.email.set_sensitive(any_services)
        self.code.set_sensitive(any_services)
        self.activate_button.set_sensitive(any_services)

    def build(self):
        table = gtk.Table(rows=3, columns=2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label(_("Service:"))
        l.set_alignment(0, 0.5)
        table.attach(l, 0, 1, 0, 1)

        l = gtk.Label(_("Email:"))
        l.set_alignment(0, 0.5)
        table.attach(l, 0, 1, 1, 2)

        l = gtk.Label(_("Activation Code:"))
        l.set_alignment(0, 0.5)
        table.attach(l, 0, 1, 2, 3)

        self.service_opt = red_services.ServicesOption()
        table.attach(self.service_opt, 1, 2, 0, 1)

        def changed_cb(opt, this):
            this.sensitize_window_elements()

        self.service_opt.connect("changed", changed_cb, self)

        self.email = gtk.Entry()
        self.email.set_activates_default(1)
        table.attach(self.email, 1, 2, 1, 2)

        self.code = gtk.Entry()
        self.code.set_activates_default(1)
        table.attach(self.code, 1, 2, 2, 3)

        table.show_all()
        self.vbox.add(table)

        button = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        button.connect("clicked", lambda x:self.destroy())

        self.activate_button = self.add_button(_("Activate"),
                                               gtk.RESPONSE_CLOSE)
        self.activate_button.grab_default()
        self.activate_button.connect("clicked", self.activate)

        self.sensitize_window_elements()

    def fill(self):
        config = red_settings.get_config()
        email = config.get("Activation/email")
        if email:
            self.email.set_text(email)

    def activate(self, button):
        service_id = self.service_opt.get_service_id()
        email = self.email.get_text()
        code = self.code.get_text()

        if not email or not code:
            dialog = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                       _("Please fill in both email and activation code."))
            dialog.run()
            dialog.destroy()
            return

        server = rcd_util.get_server_proxy()

        def activate_finished_cb(worker, this):
            if worker.is_cancelled():
                return

            try:
                success = worker.get_result()
            except ximian_xmlrpclib.Fault, f:
                rcd_util.dialog_from_fault(f,
                                           error_text=_("Unable to activate"),
                                           additional_text=_("Please ensure "
                                           "you typed the email address "
                                           "and activation code correctly"),
                                           parent=self)
                return
            
            if success:
                # Store email to config.
                config = red_settings.get_config()
                config.set("Activation/email", this.email_to_save)
                config.sync()

                rcd_util.refresh(this)
            else:
                dialog = gtk.MessageDialog(this,
                                           gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_OK,
                                           _("System could not be activated: "
                                             "Invalid activation code or "
                                             "email address."))

                dialog.run()
                gtk.threads_leave()
                dialog.destroy()
                
            this.destroy()

        activation_info = {"service" : service_id,
                           "activation_code" : code,
                           "email" : email}
        
        worker = server.rcd.service.activate(activation_info)
        self.email_to_save = email
        rcd_util.server_proxy_dialog(worker,
                                     callback=activate_finished_cb,
                                     user_data=self,
                                     parent=self)
