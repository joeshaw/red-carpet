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
import sys, string
import rcd_util
import ConfigParser
import os

from red_gettext import _

class RCConfig:

    def __init__(self):
        path = os.path.expanduser('~/')
        fname = "red-carpet"

        self.__public_dir = path + ".gnome2"
        self.__public_fn = self.__public_dir + "/" + fname
        self.__public = ConfigParser.ConfigParser()
        self.__public.read(self.__public_fn)

        self.__private_dir = path + ".gnome2_private"
        self.__private_fn = self.__private_dir + "/" + fname
        self.__private = ConfigParser.ConfigParser()
        self.__private.read(self.__private_fn)

        self.__show_pub_sync_error = 1
        self.__show_priv_sync_error = 1

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
            return ""

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
            return ""

        return self.__private.get(section, option)

    def set_private(self, path, value):
        section, option, default = self.parse_path(path)
        if not self.__private.has_section(section):
            self.__private.add_section(section)
        return self.__private.set(section, option, value)

    def sync(self):
        # FIXME: This error message isn't great, but is better than a
        # cryptic backtrace.
        error_msg = "Sync failed: couldn't write to '%s'\n" \
                    "This means that settings will not be saved!\n" \
                    "Maybe some permissions are set incorrectly?\n"
        
        try:
            if not os.path.exists(self.__public_dir):
                os.mkdir(self.__public_dir, 0755)
            f = open(self.__public_fn, 'w')
            self.__public.write(f)
            f.close()
            self.__show_pub_sync_error = 1
        except:
            if self.__show_pub_sync_error:
                sys.stderr.write(error_msg % self.__public_fn)
                self.__show_pub_sync_error = 0

        try:
            if not os.path.exists(self.__private_dir):
                os.mkdir(self.__private_dir, 0700)
            f = open(self.__private_fn, 'w')
            self.__private.write(f)
            f.close()
            self.__show_priv_sync_error = 1
        except:
            if self.__show_priv_sync_error:
                sys.stderr.write(error_msg % self.__private_fn)
                self.__show_priv_sync_error = 0

config = None

def get_config():
    global config

    if not config:
        config = RCConfig()
    return config

MAX_SAVED_URLS = 5

class DaemonData:
    def __init__(self):
        self.conf = get_config()
        self.local = 1
        self.url = []
        self.user = None
        self.password = None

        self.from_config()

    def from_config(self):
        user_path = "daemon/user"
        if os.environ.has_key("USER"):
            user_path += "=" + os.environ["USER"]

        self.local =    int(config.get("daemon/local=1"))
        self.user =     config.get(user_path)
        self.password = config.get_private("daemon/pass")

        for i in range(0, MAX_SAVED_URLS):
            url = config.get("daemon/url%d" % i)
            if not url:
                break

            self.url.append(url)

    def save_config(self):
        self.conf.set("daemon/local", str(self.local))
        self.conf.set("daemon/user", self.user)
        self.conf.set_private("daemon/pass", self.password)

        i = 0
        for u in self.url:
            self.conf.set("daemon/url" + str(i), u)
            i += 1

        self.conf.sync()

    def local_get(self):
        return self.local

    def local_set(self, local):
        self.local = local

    def url_get(self):
        if len(self.url):
            return self.url[0]
        return ""

    def url_get_list(self):
        return self.url

    def url_set(self, text):
        if text in self.url:
            self.url.remove(text)

        self.url.insert(0, text)

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
                self.password_get(),
                self.local_get())


class DaemonSettings(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)

        self.local = 1

        self.data = DaemonData()
        self.build()
        self.populate()

    def build(self):
        self.local_rb = gtk.RadioButton(None,
                                        _("Connect to daemon on this computer"))
        self.pack_start(self.local_rb)

        self.remote_rb = gtk.RadioButton(self.local_rb,
                                         _("Connect to a remote daemon"))
        self.pack_start(self.remote_rb)

        table = gtk.Table(3, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label(_("Server:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label(_("User name:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        l = gtk.Label(_("Password:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 2, 3)

        self.url = gtk.Combo()
        self.url.disable_activate() # Don't activate the dropdown with enter
        self.url.entry.set_activates_default(1)
        table.attach_defaults(self.url, 1, 2, 0, 1)

        self.user = gtk.Entry()
        self.user.set_activates_default(1)
        table.attach_defaults(self.user, 1, 2, 1, 2)

        self.password = gtk.Entry()
        self.password.set_visibility(0)
        self.password.set_activates_default(1)
        table.attach_defaults(self.password, 1, 2, 2, 3)
        
        hbox = gtk.HBox()
        hbox.pack_start(table, padding=20)
        self.pack_start(hbox)

        # desensitize the table by default.
        table.set_sensitive(0)

        def toggled_cb(b, s):
            s.local = b.get_active()
        self.local_rb.connect("toggled", toggled_cb, self)

        self.remote_rb.connect("toggled",
                               lambda x,y:y.set_sensitive(x.get_active()),
                               table)

        self.show_all()

    def populate(self):
        buf = self.data.url_get_list()
        if buf:
            self.url.set_popdown_strings(buf)

        buf = self.data.user_get()
        if buf:
            self.user.set_text(buf)

        buf = self.data.password_get_for_ui()
        if buf:
            self.password.set_text(buf)

        if self.data.local_get():
            self.local_rb.set_active(1)
        else:
            self.remote_rb.set_active(1)

    def save(self):
        self.data.local_set(self.local)

        if not self.local:
            self.data.url_set(self.url.entry.get_text())
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
        b = self.add_button(_("Connect"), gtk.RESPONSE_ACCEPT)
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

        return (None, None, None, 0)
