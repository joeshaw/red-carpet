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
import red_serverlistener
import ximian_xmlrpclib

users_model = None
privileges_model = None

class UsersView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        global users_model
        if not users_model:
            server = rcd_util.get_server()
            users_model = UsersModel(server)

        view = gtk.TreeView(users_model)
        view.set_headers_visible(0)
        self.view = view

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

class PermissionsView(gtk.ScrolledWindow,
                      red_serverlistener.ServerListener):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        global privileges_model
        if not privileges_model:
            server = rcd_util.get_server()
            privileges_model = PrivilegesModel(server, users_model)

        is_superuser = rcd_util.check_server_permission("superuser")

        view = gtk.TreeView(privileges_model)
        view.set_headers_visible(0)
        self.view = view

        col = gtk.TreeViewColumn("Privilege",
                                 gtk.CellRendererText(),
                                 text=COL_PERM_PRIVILEGE)
        view.append_column(col)

        def activated_cb(renderer, path, model):
            path = (int(path),)
            privilege = model.privileges[path[0]]

            # We want opposite state
            active = not renderer.get_active()
            users_model.current_set_privilege(privilege, active)

        r = gtk.CellRendererToggle()
        self.__toggle = r

        r.set_property("activatable", is_superuser)
        r.connect("toggled", activated_cb, privileges_model)
        col = gtk.TreeViewColumn("Enabled", r, active=COL_PERM_ENABLED)
        view.append_column(col)

        sel = view.get_selection()
        if is_superuser:
            sel.set_mode(gtk.SELECTION_SINGLE)
        else:
            sel.set_mode(gtk.SELECTION_NONE)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(view)

    def users_changed(self):
        is_superuser = rcd_util.check_server_permission("superuser")
        self.__toggle.set_property("activatable", is_superuser)
        sel = self.view.get_selection()
        if is_superuser:
            sel.set_mode(gtk.SELECTION_SINGLE)
        else:
            sel.set_mode(gtk.SELECTION_NONE)



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

        frame = gtk.Frame(None)
        frame.add(table)

        l = gtk.Label("Password:")
        l.set_alignment(1.0, 0.5)
        table.attach(l, 0, 1, 0, 1, 0, 0, 0, 0)

        l = gtk.Label("Confirm:")
        l.set_alignment(1.0, 0.5)
        table.attach(l, 0, 1, 1, 2, 0, 0, 0, 0)

        self.pwd1 = gtk.Entry()
        self.pwd1.set_visibility(0)
        table.attach_defaults(self.pwd1, 1, 2, 0, 1)
        self.pwd2 = gtk.Entry()
        self.pwd2.set_visibility(0)
        table.attach_defaults(self.pwd2, 1, 2, 1, 2)

        def user_changed_cb(model, user, this):
            this.pwd1.set_text("-*-unchanged-*-")
            this.pwd2.set_text("-*-unchanged-*-")

        users_model.connect("changed", user_changed_cb, self)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)

        button = gtk.Button()
        button.set_label("Set Password")
        button_box.add(button)
        table.attach_defaults(button_box, 1, 2, 2, 3)

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
                    p1 = rcd_util.md5ify_password(p1)
                    users_model.current_update(p1)

        button.connect("clicked", password_update_cb, self)

        return frame

    def build(self):
        main_box = gtk.HBox(0, 5)
        main_box.set_border_width(5)
        self.vbox.add(main_box)

        left_box = gtk.VBox(0, 5)
        main_box.add(left_box)

        box = gtk.HBox(0, 5)
        frame = gtk.Frame("Users")
        view = UsersView()
        frame.add(view)
        box.add(frame)
        self.__users_view = view.view

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

        def remove_cb(button, this):
            user = users_model.current_get()
            if not user:
                return

            def remove_dialog_cb(dialog, id, user):
                if id == gtk.RESPONSE_YES:
                    users_model.current_delete()

            dialog = gtk.MessageDialog(this, gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                       "Are you sure you want to delete '%s'?" % user["name"])
            dialog.connect("response", remove_dialog_cb, user)
            dialog.run()
            dialog.destroy()

        button = gtk.Button()
        button.set_label("Remove")
        button.set_sensitive(is_superuser)
        button.connect("clicked", remove_cb, self)
        button_box.add(button)
        self.__remove_button = button
        
        box.pack_start(button_box, 0)

        user_list_frame = gtk.Frame(None)
        user_list_frame.add(box)

        left_box.add(user_list_frame)

        table = self.build_password_part()
        left_box.pack_start(table, 0)
        self.__password_part = table
        table.set_sensitive(is_superuser)

        frame = gtk.Frame("Privileges")
        view = PermissionsView()
        frame.add(view)
        main_box.add(frame)
        self.__permissions_view = view.view

        main_box.show_all()

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x:self.destroy())

    def users_changed(self):
        is_superuser = rcd_util.check_server_permission("superuser")
        self.__add_button.set_sensitive(is_superuser)
        self.__remove_button.set_sensitive(is_superuser)
        self.__password_part.set_sensitive(is_superuser)

        # Thrash our views so that changes in the model will be reflected.
        # We do it in an idle function, so that the thrash won't happen
        # until after all of the other users_changed handlers have
        # executed.
        def thrash_cb(user_win):
            print "Thrash!"
            m = user_win.__users_view.get_model()
            user_win.__users_view.set_model(None)
            user_win.__users_view.set_model(m)

            m = user_win.__permissions_view.get_model()
            user_win.__permissions_view.set_model(None)
            user_win.__permissions_view.set_model(m)

        gtk.idle_add(thrash_cb, self)
        

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
            elif users_model.user_exists(name):
                msg = "User '" + name + "' already exists."

            if msg:
                dialog = gtk.MessageDialog(this, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                           msg)
                dialog.run()
                dialog.destroy()
            else:
                p1 = rcd_util.md5ify_password(p1)
                if users_model.add(name, p1):
                    this.destroy()

        button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        button.connect("clicked", add_cb, self)

        self.show_all()


COLUMN_USER = 0
COLUMN_NAME = 1
COLUMN_LAST = 2

class UsersModel(gtk.GenericTreeModel,
                 red_serverlistener.ServerListener):
    def __init__ (self, server):
        gobject.GObject.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.server = server
        self.current = None
        self.__fetch_user_info()
        
    def __fetch_user_info(self):
        self.users = []
        users = self.server.rcd.users.get_all()
        for u in users:
            user = {}
            user["name"] = u[0]
            user["privileges"] = u[1].split(", ")
            self.users.append(user)

    def user_to_column(self, user, index):
        if index == COLUMN_USER:
            return user
        elif index == COLUMN_NAME:
            return user["name"]

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return COLUMN_LAST

    def on_get_column_type(self, index):
        if index == COLUMN_USER:
            return gobject.TYPE_PYOBJECT
        else:
            return gobject.TYPE_STRING

    def on_get_tree_path(self, node):
        return node

    def on_get_iter(self, path):
        return path

    def on_get_value(self, node, column):
        user = self.users[node[0]]
        if user:
            return self.user_to_column(user, column)
        return "?no user"

    def on_iter_next(self, node):
        next = node[0] + 1
        if next >= len(self.users):
            return None
        return (next,)

    def on_iter_children(self, node):
        if node == None:
            return (0,)
        else:
            return None

    def on_iter_has_child(self, node):
        return 0

    def on_iter_nth_child(self, node, n):
        if node == None and n == 0:
            return (0,)
        else:
            return None

    def on_iter_parent(self, node):
        return None

    def user_exists(self, name):
        for u in self.users:
            if u["name"] == name:
                return 1
        return 0

    def add(self, name, pwd):
        user = { "name" : name, "privileges" : [] }
        self.users.append(user)

        path = len(self.users) - 1
        path = (path,)
        node = self.get_iter(path)

        self.row_inserted(path, node)
        self.current_set(node)
        if self.current_update(pwd):
            return 1
        else:
            self.users.remove(user)
            self.current_set(None)
            return 0

    def current_set(self, node):
        self.current = node
        self.emit("changed", self.current_get())

    def current_get(self):
        if not self.current:
            return None
        return self.get_value(self.current, COLUMN_USER)

    def current_has_privilege(self, privilege):
        user = self.current_get()
        if not user:
            return 0

        privs = user["privileges"]
        if "superuser" in privs or privilege in privs:
            return 1

        return 0

    def current_update(self, pwd=None):
        user = self.current_get()
        if not user:
            return 0

        if not pwd:
            pwd = "-*-unchanged-*-"

        new_privs_str = string.join(user["privileges"], ", ")
        if self.server.rcd.users.update(user["name"], pwd, new_privs_str):
            return 1
        else:
            return 0

    def current_set_privilege(self, privilege, active):
        user = self.current_get()
        if not user:
            return

        if active:
            if not privilege in user["privileges"]:
                user["privileges"].append(privilege)
        else:
            if privilege in user["privileges"]:
                user["privileges"].remove(privilege)

        if privilege == "superuser":
            self.emit("changed", self.current_get())

        self.current_update()

    def current_delete(self):
        user = self.current_get()
        if not user:
            return
        if self.server.rcd.users.remove(user["name"]):
            self.users.remove(user)
            self.row_deleted(self.get_path(self.current))
            self.current_set(None)

    def users_changed(self):
        # Re-fetch the user information
        self.__fetch_user_info()
        

gobject.type_register(UsersModel)
gobject.signal_new("changed",
                   UsersModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))


COL_PERM_USER =      0
COL_PERM_PRIVILEGE = 1
COL_PERM_ENABLED =   2
COL_PERM_LAST =      3

class PrivilegesModel(gtk.GenericTreeModel,
                      red_serverlistener.ServerListener):
    def __init__ (self, server, users_model):
        gtk.GenericTreeModel.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.users_model = users_model
        self.privileges = map(string.lower,
                              server.rcd.users.get_valid_privileges())
        self.privileges.sort()
        self.privileges.append("superuser")

        users_model.connect("changed", self.refresh)

    def privilege_to_column(self, privilege, index):
        if index == COL_PERM_USER:
            return self.user
        elif index == COL_PERM_PRIVILEGE:
            return privilege
        elif index == COL_PERM_ENABLED:
            return self.users_model.current_has_privilege(privilege)

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return COL_PERM_LAST

    def on_get_column_type(self, index):
        if index == COL_PERM_PRIVILEGE:
            return gobject.TYPE_STRING
        else:
            return gobject.TYPE_BOOLEAN

    def on_get_path(self, node):
        return node

    def on_get_iter(self, path):
        return path

    def on_get_value(self, node, column):
        privilege = self.privileges[node[0]]
        if privilege:
            return self.privilege_to_column(privilege, column)
        return "?no user"

    def on_iter_next(self, node):
        next = node[0] + 1
        if next >= len(self.privileges):
            return None
        return (next,)

    def on_iter_children(self, node):
        if node == None:
            return (0,)
        else:
            return None

    def on_iter_has_child(self, node):
        return 0

    def on_iter_nth_child(self, node, n):
        if node == None and n == 0:
            return (0,)
        else:
            return None

    def on_iter_parent(self, node):
        return None

## Additional methods

    # Refresh model
    def refresh(self, model, user):
        def refresh_cb(self, path, iter):
            self.row_changed(path, iter)
        self.foreach(refresh_cb)

    def users_changed(self):
        pass
