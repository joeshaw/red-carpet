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

import string
import gobject, gtk
import rcd_util
import red_main
import red_header, red_pixbuf
import red_component
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

class PermissionsView(gtk.ScrolledWindow):

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)

        global privileges_model
        if not privileges_model:
            server = rcd_util.get_server()
            privileges_model = PrivilegesModel(server, users_model)

        view = gtk.TreeView(privileges_model)
        view.set_headers_visible(0)

        col = gtk.TreeViewColumn("Privilege",
                                 gtk.CellRendererText(),
                                 text=COL_PERM_PRIVILEGE)
        view.append_column(col)

        def activated_cb(renderer, path, model):
            path = (int(path),)
            privilege = model.privileges[path[0]]
            users_model.current_set_privilege(privilege, renderer.get_active())

        r = gtk.CellRendererToggle()
        r.set_property("activatable", 1)
        r.connect("toggled", activated_cb, privileges_model)
        col = gtk.TreeViewColumn("Enabled", r, active=COL_PERM_ENABLED)
        view.append_column(col)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add(view)

PREFS_ADD = 0
PREFS_EDIT = 1

class PrefsWindow(gtk.Dialog):
    def __init__(self, action):
        gtk.Dialog.__init__(self, "Users' Preferences")
        self.build()

        if action == PREFS_EDIT:
            self.fill()

    def build(self):
        self.set_default_size(30, 400)

        box = gtk.VBox(0, 5)
        self.vbox.add(box)

        frame = gtk.Frame("User Information")
        frame.set_border_width(5)
        box.pack_start(frame, 0)

        table = gtk.Table(3, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label("User:")
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
        frame.add(table)

        frame = gtk.Frame("Privileges:")
        frame.set_border_width(5)
        box.add(frame)

        view = PermissionsView()
        view.set_border_width(5)
        frame.add(view)

        box.show_all()

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x:self.destroy())

    def fill(self):
        user = users_model.current_get()
        if not user:
            return

        self.user_entry.set_text(user["name"])
        self.user_entry.set_sensitive(0)

        self.pwd1.set_text("-*-unchanged-*-")
        self.pwd2.set_text("-*-unchanged-*-")

class UsersWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, "Users' Preferences")
        self.build()

    def build(self):
        self.set_default_size(220, 200)

        box = gtk.HBox(0, 5)
        self.vbox.add(box)


        view = UsersView()
        view.show()
        box.pack_start(view)

        button_box = gtk.VButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        def prefs_cb(data, action):
            win = PrefsWindow(action)
            win.set_modal(0)
            win.run()

        button = gtk.Button()
        button.set_label("Add...")
        button.connect("clicked", prefs_cb, PREFS_ADD)
        button_box.add(button)

        button = gtk.Button()
        button.set_label("Edit...")
        button.connect("clicked", prefs_cb, PREFS_EDIT)
        button_box.add(button)

        button = gtk.Button()
        button.set_label("Remove")
        button_box.add(button)

        box.pack_start(button_box, 0, 0, 0)

        box.show_all()

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.connect("clicked", lambda x:self.destroy())

class UsersComponent(red_component.Component):

    def name(self):
        return "Users"

    def pixbuf(self):
        # fixme
        return "summary"

    def build(self):
        view = UsersView()
        view.show()

        return view

COLUMN_USER = 0
COLUMN_NAME = 1
COLUMN_LAST = 2

class UsersModel(gtk.GenericTreeModel):
    def __init__ (self, server):
        gobject.GObject.__init__(self)

        self.server = server
        self.users = []
        self.current = None

        users = server.rcd.users.get_all()
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

    def current_set(self, node):
        self.current = self.get_value(node, COLUMN_USER)
        self.emit("changed")

    def current_get(self):
        return self.current

    def current_has_privilege(self, privilege):
        if not self.current:
            return 0

        privs = self.current["privileges"]
        if "superuser" in privs or privilege in privs:
            return 1

        return 0

    def current_set_privilege(self, privilege, active):
        if not self.current:
            return

        if privilege == "superuser":
            if not active:
                self.current["privileges"] = []
            else:
                self.current["privileges"] = ["superuser"]
        else:
            if not active:
                if not privilege in self.current["privileges"]:
                    self.current["privileges"].append(privilege)
                else:
                    if privilege in self.current["privileges"]:
                        self.current["privileges"].remove(privilege)

        new_password = "-*-unchanged-*-"
        new_privs_str = string.join(self.current["privileges"], ", ")

        self.server.rcd.users.update(self.current["name"], new_password, new_privs_str)

gobject.type_register(UsersModel)
gobject.signal_new("changed",
                   UsersModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())


COL_PERM_USER =      0
COL_PERM_PRIVILEGE = 1
COL_PERM_ENABLED =   2
COL_PERM_LAST =      3

class PrivilegesModel(gtk.GenericTreeModel):
    def __init__ (self, server, users_model):
        gtk.GenericTreeModel.__init__(self)

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
    def refresh(self, data):
        def refresh_cb(self, path, iter):
            self.row_changed(path, iter)
        self.foreach(refresh_cb)
