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
import ConfigParser
import os

class RCConfig:

    def __init__(self):
        path = os.path.expanduser('~/')
        fname = "red-carpet"

        self.__public_fn = path + ".gnome2/" + fname
        self.__public = ConfigParser.ConfigParser()
        self.__public.read(self.__public_fn)

        self.__private_fn = path + ".gnome2_private/" + fname
        self.__private = ConfigParser.ConfigParser()
        self.__private.read(self.__private_fn)

    def parse_path(self, str):
        section, option = string.split(str, "/", 2)
        default = None
        if not string.find(option, "=") == -1:
            option, default = string.split(option, "=", 2)
        return (section, option, default)

    ## Start of public API

    def get(self, path):
        section, option, default = self.parse_path(path)
        if not self.__public.has_section(section) or \
           not self.__public.has_option(section, option):
            if default:
                return default
            return None

        return self.__public.get(section, option)

    def set(self, path, value):
        section, option, default = self.parse_path(path)
        if not self.__public.has_section(section):
            self.__public.add_section(section)
        return self.__public.set(section, option, value)

    def get_private(self, path):
        section, option, default = self.parse_path(path)
        if not self.__private.has_section(section) or \
           not self.__private.has_option(section, option):
            if default:
                return default
            return None

        return self.__private.get(section, option)

    def set_private(self, path, value):
        section, option, default = self.parse_path(path)
        if not self.__private.has_section(section):
            self.__private.add_section(section)
        return self.__private.set(section, option, value)

    def sync(self):
        f = open(self.__public_fn, 'w')
        self.__public.write(f)
        f.close

        f = open(self.__private_fn, 'w')
        self.__private.write(f)
        f.close

config = None

def get_config():
    global config

    if not config:
        config = RCConfig()
    return config


class DaemonData:
    def __init__(self):
        self.conf = get_config()
        self.url = None
        self.user = None
        self.password = None

        self.from_config()

    def from_config(self):
        self.url =      config.get("daemon/url=localhost")
        self.user =     config.get("daemon/user")
        self.password = config.get_private("daemon/pass")

    def save_config(self):
        self.conf.set("daemon/url", self.url)
        self.conf.set("daemon/user", self.user)
        self.conf.set_private("daemon/pass", self.password)

        self.conf.sync()

    def url_get(self):
        host = self.url
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

    def url_get_for_ui(self):
        return self.url

    def url_set(self, text):
        self.url = text

    def user_get(self):
        return self.user
    def user_set(self, text):
        self.user = text

    def password_get(self):
        return self.password

    def password_get_for_ui(self):
        if self.password:
            return "-*-unchanged-*-"

    def password_set(self, text):
        if text == "-*-unchanged-*-":
            return

        if text:
            text = rcd_util.md5ify_password(text)

        self.password = text

    def data_get(self):
        return (self.url_get(),
                self.user_get(),
                self.password_get())


class DaemonSettings(gtk.Frame):

    def __init__(self):
        gtk.Frame.__init__(self)

        self.data = DaemonData()
        self.build()
        self.populate()

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

    def populate(self):
        buf = self.data.url_get_for_ui()
        if buf:
            self.url.set_text(buf)

        buf = self.data.user_get()
        if buf:
            self.user.set_text(buf)

        buf = self.data.password_get_for_ui()
        if buf:
            self.password.set_text(buf)

    def save(self):
        self.data.url_set(self.url.get_text())
        self.data.user_set(self.user.get_text())
        self.data.password_set(self.password.get_text())

        self.data.save_config()

    def get_daemon_info(self):
        return self.data.data_get()


class ConnectionWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self)
        self.accepted = 0
        self.build()

    def build(self):
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        b = self.add_button("Connect", gtk.RESPONSE_ACCEPT)
        b.grab_default()
        def response_cb(dialog, id, this):
            if id == gtk.RESPONSE_ACCEPT:
                this.ui.save()
                this.accepted = 1

        self.ui = DaemonSettings()
        self.vbox.add(self.ui)
        self.connect("response", response_cb, self)

    def get_server_info(self):
        if self.accepted:
            return self.ui.get_daemon_info()

        return (None, None, None)
