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
import string
import rcd_util

class DaemonSettings(gtk.Frame):

    def __init__(self, url=None, user=None, password=None):
        gtk.Frame.__init__(self)

        self.build()
        self.url_set(url)
        self.user_set(user)
        self.password_set(password)

    def build(self):
        self.set_border_width(5)
        self.set_label("Connect to rcd daemon")

        table = gtk.Table(3, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label("Server:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label("User name:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        l = gtk.Label("Password:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 2, 3)

        self.url = gtk.Entry()
        table.attach_defaults(self.url, 1, 2, 0, 1)

        self.user = gtk.Entry()
        table.attach_defaults(self.user, 1, 2, 1, 2)

        self.password = gtk.Entry()
        self.password.set_visibility(0)
        table.attach_defaults(self.password, 1, 2, 2, 3)

        self.add(table)
        self.show_all()

    def url_get(self):
        host = self.url.get_text()
        if host == "" or host == "localhost" or string.find(host, "/") == 0:
            local = 1
        else:
            local = 0

        if not local:
            # Prepend "https://" if it isn't already specified
            if string.find(host, "http://") == -1 \
               and string.find(host, "https://") == -1:
                host = "https://" + host

            # Append the port number (505) if one isn't specified
            hparts = string.split(host, ":", 2)
            if len(hparts) < 3:
                hparts.append("505")
            url = string.join(hparts, ":") + "/RPC2"
        else:
            url = "/var/run/rcd/rcd"

        return url

    def url_set(self, text):
        if not text:
            text = "localhost"
        self.url.set_text(text)

    def user_get(self):
        return self.user.get_text()
    def user_set(self, text):
        if not text:
            text = ""
        self.user.set_text(text)

    def password_get(self):
        pwd = self.password.get_text()
        if pwd:
            pwd = rcd_util.md5ify_password(pwd)
        return pwd
    def password_set(self, text):
        if not text:
            text = ""
        self.password.set_text(text)


RESPONSE_CONNECT = 1

class ConnectionWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self)

        self.url = None
        self.user = None
        self.password = None
        self.build()

    def build(self):
        self.add_button(gtk.STOCK_QUIT, gtk.RESPONSE_NONE)
        b = self.add_button("Connect", RESPONSE_CONNECT)
        b.grab_default()
        def response_cb(dialog, id, this):
            if id != RESPONSE_CONNECT:
                this.url = this.user = this.password = None
            else:
                buf = this.ui.url_get()
                if buf:
                    this.url = buf

                buf = this.ui.user_get()
                if buf:
                    this.user = buf

                buf = this.ui.password_get()
                if buf:
                    this.password = buf

        self.ui = DaemonSettings()
        self.vbox.add(self.ui)
        self.connect("response", response_cb, self)

    def run(self):
        gtk.Dialog.run(self)
        return (self.url, self.user, self.password)
