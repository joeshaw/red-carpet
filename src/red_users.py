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

import string, re
import gobject, gtk
import rcd_util
import red_main
import red_pixbuf
import red_component
import ximian_xmlrpclib

import red_listmodel, red_serverlistener, red_thrashingtreeview

users_data = None

class User:
    def __init__(self, name, pwd=None, privileges=[]):
        self.name_set(name)
        self.pwd_set(pwd)
        self.privileges_set(privileges)

    def name_get(self):
        return self.name
    def name_set(self, name):
        self.name = name

    def pwd_get(self):
        if self.pwd:
            return self.pwd
        else:
            return "-*-unchanged-*-"
    def pwd_set(self, pwd):
        if pwd:
            self.pwd = rcd_util.md5ify_password(pwd)
        else:
            self.pwd = None

    def privileges_get(self):
        return self.privileges
    def privileges_set(self, privileges):
        self.privileges = privileges
    def has_privilege(self, privilege):
        return "superuser" in self.privileges or \
               privilege in self.privileges

    def privilege_set(self, privilege, active):
        if active:
            if not privilege in self.privileges:
                self.privileges.append(privilege)
        else:
            if privilege in self.privileges:
                self.privileges.remove(privilege)

        self.update()

    def update(self):
        server = rcd_util.get_server()
        privs_str = string.join(self.privileges_get(), ", ")
        server.rcd.users.update(self.name_get(),
                                self.pwd_get(),
                                privs_str)

        server.set_password(self.pwd_get())

    def delete(self):
        server = rcd_util.get_server()
        server.rcd.users.remove(self.name_get())


class UsersData(red_serverlistener.ServerListener, gobject.GObject):

    def __init__(self):
        red_serverlistener.ServerListener.__init__(self)
        gobject.GObject.__init__(self)

        self.__users = []
        self.__privileges = []
        self.active_user = None

        self.refresh()

    def fetch_users(self):
        serv = rcd_util.get_server()
        users = serv.rcd.users.get_all()
        self.__users = []
        for u in users:
            user = User(u[0])
            user.privileges_set(u[1].split(", "))
            self.__users.append(user)

    def fetch_privileges(self):
        serv = rcd_util.get_server()
        self.__privileges = map(string.lower,
                                serv.rcd.users.get_valid_privileges())
        self.__privileges.sort()
        self.__privileges.append("superuser")

    def users_changed(self):
        self.refresh()

    def refresh(self):
        self.fetch_users()
        self.fetch_privileges()
        self.emit("changed")

    def get_all_users(self):
        return self.__users

    def get_all_privileges(self):
        return self.__privileges

    def user_exists(self, user_name):
        for u in self.__users:
            if u.name_get() == user_name:
                return 1

        return 0

    def get_active_user(self):
        if self.active_user:
            return self.active_user

    def set_active_user(self, user):
        self.active_user = user
        self.emit("active-changed")

gobject.type_register(UsersData)
gobject.signal_new("changed",
                   UsersData,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())

gobject.signal_new("active-changed",
                   UsersData,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())


class UsersView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        global users_model
        if not users_model:
            server = rcd_util.get_server()
            users_model = UsersModel(server)

        view = gtk.TreeView(users_model)
        view.set_headers_visible(0)

        col = gtk.TreeViewColumn("User",
                                 gtk.CellRendererText(),
                                 text=COLUMN_NAME)
        view.append_column(col)

        selection = view.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)

        def selection_changed_cb(selection, component):
            model, iter = selection.get_selected()
            if iter:
                model.current_set(iter)

        selection.connect("changed", selection_changed_cb, self)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(view)

def make_users_view(model):
    view = red_thrashingtreeview.TreeView(model)
    view.set_headers_visible(0)

    col = gtk.TreeViewColumn("User",
                             gtk.CellRendererText(),
                             text=COLUMN_NAME)
    view.append_column(col)
    return view
    

class PermissionsView(gtk.ScrolledWindow):

    def __init__(self, users_data):
        gtk.ScrolledWindow.__init__(self)

        server = rcd_util.get_server()
        model = PrivilegesModel(users_data)

        view = gtk.TreeView(model)
        view.set_headers_visible(0)

        col = gtk.TreeViewColumn("Privilege",
                                 gtk.CellRendererText(),
                                 text=PRIVILEGE_COLUMN_PRIVILEGE)
        view.append_column(col)

        def activated_cb(renderer, path, model):
            path = (int(path),)
            privilege = model.get_list_item(path[0])
            user = users_data.get_active_user()
            if user:
                current_user = rcd_util.get_current_user()
                if user.name_get() == current_user and privilege == "superuser":
                    # Warn the user about removing their own superuser priv
                    dialog = gtk.MessageDialog(None,
                                               0,
                                               gtk.MESSAGE_WARNING,
                                               gtk.BUTTONS_YES_NO,
                                               "If you remove superuser "
                                               "privileges from yourself, you "
                                               "will be unable to re-add them."
                                               "\n\n"
                                               "Are you sure you want to do "
                                               "this?")
                    response = dialog.run()
                    dialog.destroy()
                    if response == gtk.RESPONSE_NO or response == gtk.RESPONSE_DELETE_EVENT:
                        return

                # We want opposite state
                active = not renderer.get_active()
                user.privilege_set(privilege, active)

        r = gtk.CellRendererToggle()
        r.set_property("activatable", 1)
        r.connect("toggled", activated_cb, model)
        col = gtk.TreeViewColumn("Enabled", r, active=PRIVILEGE_COLUMN_ENABLED)
        view.append_column(col)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(view)


class UsersWindow(gtk.Dialog,
                  red_serverlistener.ServerListener):

    def __init__(self):
        gtk.Dialog.__init__(self, "Edit Users")
        red_serverlistener.ServerListener.__init__(self)
        self.build()
        self.set_size_request(500, -1)

    def build_password_part(self):
        table = gtk.Table(3, 2)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label("Password")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label("Confirm:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        self.pwd1 = gtk.Entry()
        self.pwd1.set_visibility(0)
        table.attach_defaults(self.pwd1, 1, 2, 0, 1)
        self.pwd2 = gtk.Entry()
        self.pwd2.set_visibility(0)
        table.attach_defaults(self.pwd2, 1, 2, 1, 2)

        def user_changed_cb(model, this):
            this.pwd1.set_text("-*-unchanged-*-")
            this.pwd2.set_text("-*-unchanged-*-")

        users_data.connect("active-changed", user_changed_cb, self)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)

        button = gtk.Button()
        button.set_label("Set Password")
        button_box.add(button)
        table.attach_defaults(button_box, 0, 2, 2, 3)

        def password_update_cb(button, this):
            p1 = this.pwd1.get_text()
            p2 = this.pwd2.get_text()

            msg = None
            if not p1:
                msg = "Password can not be empty."
            elif p1 != p2:
                msg = "Passwords do not match."

            if msg:
                dialog = gtk.MessageDialog(this, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
                dialog.run()
                dialog.destroy()
            else:
                if p1 != "-*-unchanged-*-":
                    user = users_data.get_active_user()
                    user.pwd_set(p1)
                    user.update()

        button.connect("clicked", password_update_cb, self)

        return table

    def build(self):
        main_box = gtk.HBox(0, 5)
        main_box.set_border_width(5)
        self.vbox.add(main_box)

        left_box = gtk.VBox(0, 5)
        main_box.add(left_box)

        global users_data
        if not users_data:
            users_data = UsersData()

        box = gtk.HBox(0, 5)
        frame = gtk.Frame("Users")
        users_model = UsersModel(users_data)
        view = make_users_view(users_model)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(view)
        frame.add(sw)
        box.add(frame)

        def selection_changed_cb(selection):
            model, iter = selection.get_selected()
            if iter:
                u = model.get_value(iter, COLUMN_USER)
                users_data.set_active_user(u)

        selection = view.get_selection()
        selection.connect("changed", selection_changed_cb)

        is_superuser = rcd_util.check_server_permission("superuser")

        button_box = gtk.VButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        button_box.set_spacing(5)

        button = gtk.Button()
        button.set_label("Add")
        button.set_sensitive(is_superuser)
        button.connect("clicked", lambda x:UserAdd())
        button_box.add(button)
        self.__add_button = button

        def remove_cb(button, selection):
            model, iter = selection.get_selected()
            if iter:
                u = model.get_value(iter, COLUMN_USER)

                def remove_dialog_cb(dialog, id, user):
                    if id == gtk.RESPONSE_YES:
                        user.delete()

                dialog = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                           "Are you sure you want to delete '%s'?" % u.name_get())
                dialog.connect("response", remove_dialog_cb, u)
                dialog.run()
                dialog.destroy()

        button = gtk.Button()
        button.set_label("Remove")
        button.set_sensitive(is_superuser)
        button.connect("clicked", remove_cb, selection)
        button_box.add(button)
        self.__remove_button = button

        box.pack_start(button_box, 0)

        user_list_frame = gtk.Frame(None)
        user_list_frame.add(box)

        left_box.add(user_list_frame)

        table = self.build_password_part()
        left_box.pack_start(table, 0)
        self.__password_part = table

        def sensitize_password_part_cb(ud, t):
            is_superuser = rcd_util.check_server_permission("superuser")

            is_me = 0
            user = ud.get_active_user()
            if user and user.name_get() == rcd_util.get_current_user():
                is_me = 1
            t.set_sensitive(is_superuser or is_me)
        
        users_data.connect("active-changed", sensitize_password_part_cb, table)
        sensitize_password_part_cb(users_data, table)

        frame = gtk.Frame("Privileges")
        view = PermissionsView(users_data)
        frame.add(view)
        frame.set_sensitive(is_superuser)
        main_box.add(frame)

        main_box.show_all()

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x:self.destroy())

    def users_changed(self):
        is_superuser = rcd_util.check_server_permission("superuser")
        self.__add_button.set_sensitive(is_superuser)
        self.__remove_button.set_sensitive(is_superuser)
        self.__password_part.set_sensitive(is_superuser)

class UserAdd(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self, "Add new user")

        box = gtk.VBox(0, 5)
        self.vbox.add(box)

        table = gtk.Table(3, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label("User name:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)
        self.user_entry = gtk.Entry()
        table.attach_defaults(self.user_entry, 1, 2, 0, 1)
        
        l = gtk.Label("Password:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        l = gtk.Label("Confirm:")
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 2, 3)

        self.pwd1 = gtk.Entry()
        self.pwd1.set_visibility(0)
        table.attach_defaults(self.pwd1, 1, 2, 1, 2)
        self.pwd2 = gtk.Entry()
        self.pwd2.set_visibility(0)
        table.attach_defaults(self.pwd2, 1, 2, 2, 3)

        box.add(table)

        button = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        button.connect("clicked", lambda x:self.destroy())

        def add_cb(button, this):
            name = this.user_entry.get_text()
            p1 = this.pwd1.get_text()
            p2 = this.pwd2.get_text()

            msg = None
            if not p1:
                msg = "Password can not be empty."
            elif p1 != p2:
                msg = "Passwords do not match."
            if not re.compile("^\w+$").match(name):
                msg = "Invalid user name."
            elif users_data.user_exists(name):
                msg = "User '" + name + "' already exists."

            if msg:
                dialog = gtk.MessageDialog(this, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                           msg)
                dialog.run()
                dialog.destroy()
            else:
                user = User(name, p1)
                user.update()
                this.destroy()

        button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        button.connect("clicked", add_cb, self)

        self.show_all()


COLUMNS = (
    ("USER",
     lambda x:x,
     gobject.TYPE_PYOBJECT),

    ("NAME",
     lambda x:x.name_get(),
     gobject.TYPE_STRING),
    )

for i in range(len(COLUMNS)):
    name = COLUMNS[i][0]
    exec("COLUMN_%s = %d" % (name, i))

class UsersModel(red_listmodel.ListModel):

    def __init__(self, users_data, sort_fn=None, filter_fn=None):
        red_listmodel.ListModel.__init__(self, sort_fn, filter_fn)
        self.__users = []

        users_data.connect("changed", self.refresh)

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

        self.refresh(users_data)

    def refresh(self, users_data):
        def refresh_cb(this, users_data):
            self.__users = users_data.get_all_users()

        self.changed(refresh_cb, users_data)

    ###
    ### red_listmodel.ListModel implementation
    ###

    def get_all(self):
        return self.__users


def get_enabled(privilege):
    u = users_data.get_active_user()
    if u and u.has_privilege(privilege):
        return 1

    return 0

PRIVILEGE_COLUMNS = (
    ("PRIVILEGE",
     lambda x:x,
     gobject.TYPE_STRING),

    ("ENABLED",
     lambda x:get_enabled(x),
     gobject.TYPE_BOOLEAN),
    )

for i in range(len(PRIVILEGE_COLUMNS)):
    name = PRIVILEGE_COLUMNS[i][0]
    exec("PRIVILEGE_COLUMN_%s = %d" % (name, i))

class PrivilegesModel(red_listmodel.ListModel):

    def __init__(self, users_data, sort_fn=None, filter_fn=None):
        red_listmodel.ListModel.__init__(self, sort_fn, filter_fn)
        self.__privileges = []

        users_data.connect("changed", self.refresh)
        users_data.connect("active-changed", self.active_changed)

        for name, callback, type in PRIVILEGE_COLUMNS:
            self.add_column(callback, type)

        self.refresh(users_data)

    def refresh(self, users_data):
        def refresh_cb(this, users_data):
            self.__privileges = users_data.get_all_privileges()

        self.changed(refresh_cb, users_data)

    def active_changed(self, users_data):
        def active_changed_cb(self, path, iter):
            self.row_changed(path[0])
        self.foreach(active_changed_cb)

    ###
    ### red_listmodel.ListModel implementation
    ###

    def get_all(self):
        return self.__privileges
