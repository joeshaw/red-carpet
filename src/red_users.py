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

import string, re, gobject, gtk
import rcd_util
import ximian_xmlrpclib
import red_listmodel, red_serverlistener, red_thrashingtreeview

from red_gettext import _

opt = None

class User:
    def __init__(self, name, pwd=None, privileges=[]):
        self.name_set(name)
        self.pwd_set(pwd)
        self.privileges_set(privileges)

    def __cmp__(self, other):
        if not isinstance(other, User):
            return 1
        return cmp(self.name_get(), other.name_get())

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
        ## Make sure we have at least 'view'
        if not self.privileges:
            self.privileges.append("view")
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

    def rpc_call_ready_cb(self, th, reset_polling=1):
        try:
            success = th.get_result()
        except ximian_xmlrpclib.Fault, f:
            rcd_util.dialog_from_fault(f)
            return

        if reset_polling:
            red_serverlistener.reset_polling(1)

    def update(self):
        server = rcd_util.get_server_proxy()
        privs_str = string.join(self.privileges_get(), ", ")
        th = server.rcd.users.update(self.name_get(),
                                     self.pwd_get(),
                                     privs_str)
        th.connect("ready", self.rpc_call_ready_cb, 0)

        th = server.set_password(self.pwd_get())
        th.connect("ready", self.rpc_call_ready_cb)

    def delete(self):
        server = rcd_util.get_server_proxy()
        th = server.rcd.users.remove(self.name_get())
        th.connect("ready", self.rpc_call_ready_cb)


def make_users_view(model):
    view = red_thrashingtreeview.TreeView(model)
    view.set_headers_visible(0)

    col = gtk.TreeViewColumn(_("User"),
                             gtk.CellRendererText(),
                             text=COLUMN_NAME)
    view.append_column(col)
    return view


class PermissionsView(gtk.ScrolledWindow):

    def __init__(self, opt):
        gtk.ScrolledWindow.__init__(self)

        model = PrivilegesModel(opt)

        view = red_thrashingtreeview.TreeView()
        view.set_model(model)
        view.set_headers_visible(0)

        col = gtk.TreeViewColumn(_("Privilege"),
                                 gtk.CellRendererText(),
                                 text=PRIVILEGE_COLUMN_PRIVILEGE)
        view.append_column(col)

        def activated_cb(renderer, path, model):
            path = (int(path),)
            privilege = model.get_list_item(path[0])
            user = opt.get_selected_user()
            if user:
                current_user = rcd_util.get_current_user()
                if user.name_get() == current_user and privilege == "superuser":
                    # Warn the user about removing their own superuser priv
                    dialog = gtk.MessageDialog(None,
                                               0,
                                               gtk.MESSAGE_WARNING,
                                               gtk.BUTTONS_YES_NO,
                                               _("If you remove superuser "
                                               "privileges from yourself, you "
                                               "will be unable to re-add them."
                                               "\n\n"
                                               "Are you sure you want to do "
                                               "this?"))
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
        col = gtk.TreeViewColumn(_("Enabled"),
                                 r, active=PRIVILEGE_COLUMN_ENABLED)
        view.append_column(col)

        view.show_all()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_OUT)
        self.add(view)


class UsersWindow(gtk.Dialog,
                  red_serverlistener.ServerListener):

    def __init__(self):
        gtk.Dialog.__init__(self, _("Edit Users"))
        red_serverlistener.ServerListener.__init__(self)
        self.build()
        self.set_size_request(300, 500)

    def build_password_part(self):
        table = gtk.Table(3, 2)
        table.set_col_spacings(5)
        table.set_row_spacings(5)
        table.set_border_width(6)

        l = gtk.Label(_("Password:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label(_("Confirm:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        self.pwd1 = gtk.Entry()
        self.pwd1.set_visibility(0)
        table.attach_defaults(self.pwd1, 1, 2, 0, 1)
        self.pwd2 = gtk.Entry()
        self.pwd2.set_visibility(0)
        table.attach_defaults(self.pwd2, 1, 2, 1, 2)

        def init_pwd_entries(this):
            this.pwd1.set_text("-*-unchanged-*-")
            this.pwd2.set_text("-*-unchanged-*-")

        self.opt.connect("selected", lambda x,y,z:init_pwd_entries(z), self)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)

        button = gtk.Button()
        button.set_label(_("Set Password"))
        button_box.add(button)
        self.pwd_button = button
        table.attach_defaults(button_box, 0, 2, 2, 3)

        def sensitize_pwd_widgets(w, this):
            if this.pwd1.get_text() == "-*-unchanged-*-":
                this.pwd2.set_sensitive(0)
                this.pwd_button.set_sensitive(0)
                return

            this.pwd2.set_sensitive(1)

            if this.pwd2.get_text() == "-*-unchanged-*-":
                this.pwd_button.set_sensitive(0)
                return

            # else:
            this.pwd_button.set_sensitive(1)

        self.pwd1.connect("changed", sensitize_pwd_widgets, self)
        self.pwd2.connect("changed", sensitize_pwd_widgets, self)

        def password_update_cb(button, this):
            p1 = this.pwd1.get_text()
            p2 = this.pwd2.get_text()

            msg = None
            if not p1:
                msg = _("Password can not be empty.")
            elif p1 != p2:
                msg = _("Passwords do not match.")

            if msg:
                dialog = gtk.MessageDialog(this,
                                           gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                           msg)
                dialog.run()
                dialog.destroy()
            else:
                if p1 != "-*-unchanged-*-":
                    user = this.opt.get_selected_user()
                    user.pwd_set(p1)
                    user.update()
                    init_pwd_entries(this)

        button.connect("clicked", password_update_cb, self)

        def update_frame_label(ud, u, frame):
            if u:
                label = _("Set %s's password") % u.name_get()
            else:
                label = ""

            frame.set_label(label)

        frame = gtk.Frame()
        frame.add(table)
        self.opt.connect("selected", update_frame_label, frame)

        return frame

    def build(self):
        main_box = gtk.VBox(0, 5)
        main_box.set_border_width(5)
        self.vbox.add(main_box)

        left_box = gtk.VBox(0, 5)
        main_box.pack_start(left_box, 0, 0)

        box = gtk.HBox(0, 5)
        frame = gtk.Frame(_("Users"))
        frame.set_border_width(6)

        global opt
        opt = UsersOption()
        opt.set_border_width(6)
        self.opt = opt
        
        frame.add(opt)
        box.add(frame)

        is_superuser = rcd_util.check_server_permission("superuser")

        button_box = gtk.VButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        button_box.set_spacing(5)
        button_box.set_border_width(6)

        button = gtk.Button()
        button.set_label(_("Add"))
        button.set_sensitive(is_superuser)
        button.connect("clicked", lambda x,y:UserAdd(y), opt)
        button_box.add(button)
        self.__add_button = button

        def remove_cb(button, opt):
            u = opt.get_selected_user()
            if u:
                def remove_dialog_cb(dialog, id, user):
                    if id == gtk.RESPONSE_YES:
                        self.opt.delete_user(user)

                dialog = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                           _("Are you sure you want to delete '%s'?") % u.name_get())
                dialog.connect("response", remove_dialog_cb, u)
                dialog.run()
                dialog.destroy()

        button = gtk.Button()
        button.set_label(_("Remove"))
        button.set_sensitive(is_superuser)
        button.connect("clicked", remove_cb, opt)
        button_box.add(button)
        self.__remove_button = button

        box.pack_start(button_box, 0)

        left_box.pack_start(box, 0, 0)

        table = self.build_password_part()
        left_box.pack_start(table, 0)
        self.__password_part = table

        def sensitize_password_part_cb(opt, user, t):
            is_superuser = rcd_util.check_server_permission("superuser")

            is_me = 0
            if user and user.name_get() == rcd_util.get_current_user():
                is_me = 1
            t.set_sensitive(is_superuser or is_me)
        
        opt.connect("selected", sensitize_password_part_cb, table)

        frame = gtk.Frame(_("Privileges"))
        view = PermissionsView(opt)
        view.set_border_width(6)
        frame.add(view)
        frame.set_sensitive(is_superuser)
        main_box.add(frame)

        main_box.show_all()

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.grab_default()
        button.connect("clicked", lambda x:self.destroy())

    def users_changed(self):
        is_superuser = rcd_util.check_server_permission("superuser")
        self.__add_button.set_sensitive(is_superuser)
        self.__remove_button.set_sensitive(is_superuser)
        self.__password_part.set_sensitive(is_superuser)

class UserAdd(gtk.Dialog):
    def __init__(self, opt):
        gtk.Dialog.__init__(self, _("Add new user"))

        box = gtk.VBox(0, 5)
        self.vbox.add(box)

        table = gtk.Table(3, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label(_("User name:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)
        self.user_entry = gtk.Entry()
        table.attach_defaults(self.user_entry, 1, 2, 0, 1)
        
        l = gtk.Label(_("Password:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        l = gtk.Label(_("Confirm:"))
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
                msg = _("Password can not be empty.")
            elif p1 != p2:
                msg = _("Passwords do not match.")
            if not re.compile("^\w+$").match(name):
                msg = _("Invalid user name.")
            elif opt.user_name_exists(name):
                msg = _("User '%s' already exists.") % name

            if msg:
                dialog = gtk.MessageDialog(this, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                           msg)
                dialog.run()
                dialog.destroy()
            else:
                user = User(name, p1)
                opt.add_user(user)
                this.destroy()

        button = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        button.connect("clicked", add_cb, self)

        self.show_all()


def get_enabled(privilege):
    if not opt:
        return 0
    u = opt.get_selected_user()
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

    def __init__(self, opt, sort_fn=None, filter_fn=None):
        red_listmodel.ListModel.__init__(self, sort_fn, filter_fn)

        self.__worker = None
        self.__worker_handler_id = 0

        opt.connect("selected", lambda x,y:self.refresh())
        opt.connect("updated", lambda x:self.request_update())

        for name, callback, type in PRIVILEGE_COLUMNS:
            self.add_column(callback, type)

        self.refresh()


    def set_privileges(self, privs):
        def set_privileges_cb(this, privs):
            self.__privileges = privs
        self.changed(set_privileges_cb, privs)

    def refresh(self):
        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_is = 0
            self.__worker.cancel()

        def got_cb(worker, this):
            if not worker.is_cancelled():
                try:
                    privs = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    rcd_util.dialog_from_fault(f)
                    return
                if privs:
                    privs = map(string.lower, privs)
                    privs.sort()
                    privs.append("superuser")

                    this.set_privileges(privs)

        self.set_privileges([])

        server = rcd_util.get_server_proxy()
        self.__worker = server.rcd.users.get_valid_privileges()
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         got_cb,
                                                         self)

    def request_update(self):
        def request_update_cb(self, path, iter):
            self.row_changed(path[0])
        self.foreach(request_update_cb)

    ###
    ### red_listmodel.ListModel implementation
    ###

    def get_all(self):
        return self.__privileges



class UsersOption(gtk.OptionMenu, red_serverlistener.ServerListener):

    def __init__(self, allow_all=0):
        gobject.GObject.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.__worker = None
        self.__worker_handler_id = 0
        self.__last_user = None
        self.__new_user = None
        self.__allow_all = allow_all

        self.refresh()

    def __assemble(self):
        menu = gtk.Menu()

        if self.__allow_all:
            u = User("All")
            self.__users.insert(0, u)

        for u in self.__users:
            item = gtk.MenuItem(u.name_get())
            item.show()

            item.connect("activate", lambda x,y:self.select_user(y), u)

            menu.append(item)

        menu.show()
        self.set_menu(menu)

    def users_changed(self):
        self.refresh()

    def set_users(self, users):
        list = []
        for u in users:
            user = User(u[0])
            user.privileges_set(u[1].split(", "))
            list.append(user)
        self.__users = list
        self.__assemble()

        u = self.__new_user
        if not u:
            u = self.__last_user
        if not u:
            u = self.user_name_exists(rcd_util.get_current_user())
        if not u and len(list):
            u = list[0]

        if u:
            self.select_user(u)
            self.__new_user = None

    def select_user(self, user):
        id = 0
        for u in self.__users:
            if not cmp(u, user):
                self.set_history(id)
                
                if cmp(self.__last_user, user):
                    self.__last_user = user
                    self.emit("selected", user)

                return
            id += 1

    def get_selected_user(self):
        return self.__last_user

    def user_name_exists(self, name):
        for u in self.__users:
            if u and u.name_get() == name:
                return u
        return 0

    def add_user(self, user):
        if user and isinstance(user, User):
            user.update()
            self.__new_user = user

    def delete_user(self, user):
        if user and isinstance(user, User):
            user.delete()
            self.__last_user = None

    def refresh(self):
        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_is = 0
            self.__worker.cancel()

        def got_cb(worker, this):
            if not worker.is_cancelled():
                try:
                    users = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    rcd_util.dialog_from_fault(f)
                    return
                if users:
                    this.set_users(users)
                    self.emit("updated")

        server = rcd_util.get_server_proxy()
        self.__worker = server.rcd.users.get_all()
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         got_cb,
                                                         self)

gobject.type_register(UsersOption)

gobject.signal_new("selected",
                   UsersOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

gobject.signal_new("updated",
                   UsersOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())
