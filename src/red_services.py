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

import string, gobject, gtk
import rcd_util
import ximian_xmlrpclib
import red_listmodel, red_serverlistener, red_thrashingtreeview

from red_gettext import _

COLUMNS = (
    ("SERVICE",
     lambda x:x,
     gobject.TYPE_PYOBJECT),

    ("ID",
     lambda x:x["id"],
     gobject.TYPE_STRING),
    
    ("NAME",
     lambda x:x["name"],
     gobject.TYPE_STRING),

    ("URL",
     lambda x:x["url"],
     gobject.TYPE_STRING),
    
)

for i in xrange(len(COLUMNS)):
    name = COLUMNS[i][0]
    exec("COLUMN_%s = %d" % (name, i))

class ServicesModel(red_listmodel.ListModel,
                    red_serverlistener.ServerListener):

    def __init__(self):
        red_listmodel.ListModel.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.__services = rcd_util.get_all_services()

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

        self.refresh()

    ###
    ### ListModel methods
    ###

    def get_all(self):
        return self.__services

    def spew(self):
        for s in self.get_all():
            print s

    ###
    ### ServerListener methods
    ###

    def channels_changed(self):
        self.refresh()

    def refresh(self):
        def refresh_cb(me):
            me.__services = rcd_util.get_all_services()
        self.changed(refresh_cb)

class ServiceAddWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, _("Add Service"))
        self.build()

    def build(self):
        ## self.set_has_separator(0)

        table = gtk.Table(rows=3, columns=2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        label = gtk.Label(_("Service URL"))
        table.attach(label, 0, 1, 0, 1)

        self.url = gtk.Entry()
        table.attach(self.url, 1, 2, 0, 1)

        label = gtk.Label(_("Service type"))
        table.attach(label, 0, 1, 1, 2)

        self.service_type = ServiceTypesOption()
        table.attach(self.service_type, 1, 2, 1, 2)

        label = gtk.Label(_("Registration key"))
        table.attach(label, 0, 1, 2, 3)

        self.key = gtk.Entry()
        table.attach(self.key, 1, 2, 2, 3)

        table.show_all()
        self.vbox.pack_start(table, expand=1, fill=1, padding=12)

        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

class ServicesWindow(gtk.Dialog, red_serverlistener.ServerListener):

    def __init__(self):
        gtk.Dialog.__init__(self, _("Edit Services"))
        red_serverlistener.ServerListener.__init__(self)

        self.__busy = 0

        self.build()
        self.set_size_request(500, 300)

##        def destroy_cb(win):
##            win.busy_stop()

##        self.connect("destroy", destroy_cb)

    def build(self):

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, expand=1, fill=1, padding=12)

        vbox = gtk.VBox()
        hbox.pack_start(vbox, expand=1, fill=1, padding=12)

        model = ServicesModel()
        self.view = red_thrashingtreeview.TreeView(model)

        col = gtk.TreeViewColumn(_("Name"),
                                 gtk.CellRendererText(),
                                 text=COLUMN_NAME)
        self.view.append_column(col)

        col = gtk.TreeViewColumn(_("URL"),
                                 gtk.CellRendererText(),
                                 text=COLUMN_URL)
        self.view.append_column(col)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.view)
                                 
        vbox.pack_start(sw)

        bbox = gtk.HButtonBox()
        bbox.set_spacing(6)
        bbox.set_layout(gtk.BUTTONBOX_END)

        self.remove_button = gtk.Button(_("_Remove service"))
        self.remove_button_sensitize()
        self.remove_button.connect("clicked", lambda x:self.remove_service())
        bbox.pack_start(self.remove_button, expand=0, fill=0, padding=3)

        def tree_changed_cb(this):
            this.remove_button_sensitize()

        model.connect("changed",
                      lambda x,y:tree_changed_cb(y),
                      self)

        select = self.view.get_selection()
        select.connect("changed",
                       lambda x,y:tree_changed_cb(y),
                       self)

        button = gtk.Button(_("_Add service"))
        button.set_sensitive(rcd_util.check_server_permission("superuser"))
        button.connect("clicked", lambda x:self.add_service())
        bbox.pack_start(button, expand=0, fill=0, padding=3)

        vbox.pack_end(bbox, expand=0, fill=0, padding=6)

        self.vbox.show_all()

        button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        button.grab_default()
        button.connect("clicked", lambda x:self.destroy())

    def get_selected_service(self):
        select = self.view.get_selection()
        if select == None:
            return None

        def selected_cb(model, path, iter, sl):
            service = model.get_value(iter, COLUMN_SERVICE)
            sl.append(service)

        service_list = []
        if select.get_tree_view().get_model():
            select.selected_foreach(selected_cb, service_list)

        if not service_list:
            return None
        else:
            return service_list[0]

    def remove_button_sensitize(self):
        if rcd_util.check_server_permission("superuser") \
           and self.get_selected_service() is not None:
            self.remove_button.set_sensitive(1)
        else:
            self.remove_button.set_sensitive(0)

    def remove_service(self):
        selected_service = self.get_selected_service()

        def remove_service_cb(th, win):
            try:
                th.get_result()
            except ximian_xmlrpclib.Fault, f:
                rcd_util.dialog_from_fault(f)
                return
            else:
                win.busy_start()

        server = rcd_util.get_server_proxy()
        th = server.rcd.service.remove(selected_service["id"])
        th.connect("ready", remove_service_cb, self)

    def add_service(self):

        def service_added_cb (th, parent):
            if th.is_cancelled():
                return

            try:
                th.get_result()
            except ximian_xmlrpclib.Fault, f:
                rcd_util.dialog_from_fault(f)
                return
            else:
                parent.busy_start()

        win = ServiceAddWindow()
        response = win.run()
        if response == gtk.RESPONSE_OK:
            server = rcd_util.get_server_proxy()
            try:
                th = server.rcd.service.add(win.service_type.get_service_id(),
                                            win.url.get_text(),
                                            win.key.get_text())
            except ximian_xmlrpclib.Fault, f:
                rcd_util.dialog_from_fault(f)
                return

            rcd_util.server_proxy_dialog(th, callback=service_added_cb,
                                         user_data=self, parent=self)
        win.destroy()

    def busy_start(self):
        self.__busy = 1
        if self.window:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))

    def busy_stop(self):
        self.__busy = 0
        if self.window:
            self.window.set_cursor(None)

    ###
    ### ServerListener methods
    ###

    def channels_changed(self):
        self.busy_stop()

class ServicesOption(gtk.OptionMenu, red_serverlistener.ServerListener):

    def __init__(self):
        gobject.GObject.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.build()
        self.__last_id = None

    def build(self):
        self.item_id_list = []
        
        menu = gtk.Menu()
        
        services = rcd_util.get_all_services()
        services.sort(lambda x,y:cmp(string.lower(x["name"]),
                                     string.lower(y["name"])))

        for s in services:
            self.item_id_list.append(s["id"])
            
            item = gtk.MenuItem(s["name"])
            item.show()

            def activate_cb(item, id, opt):
                if id != self.__last_id:
                    opt.__last_id = id
                    opt.emit("selected", id)

            item.connect("activate", activate_cb, s["id"], self)

            menu.append(item)

        menu.show()
        self.set_menu(menu)

    def get_service_id(self):
        h = self.get_history()
        if h < 0:
            return None
        return self.item_id_list[h]

    def set_service_by_id(self, id):
        if not id in self.item_id_list:
            print "Unknown service '%s'" % id
            assert 0

        i = self.item_id_list.index(id)
        self.set_history(i)

    ###
    ### ServerListener methods
    ###

    def channels_changed(self):
        id = self.get_service_id()
        self.build()
        if id is not None and id in self.item_id_list:
            self.set_service_by_id(id)

gobject.type_register(ServicesOption)

gobject.signal_new("selected",
                   ServicesOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,))

class ServiceTypesOption(gtk.OptionMenu, red_serverlistener.ServerListener):

    def __init__(self):
        gobject.GObject.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.build()
        self.__last_id = None

    def build(self):
        self.item_id_list = []
        
        menu = gtk.Menu()

        server = rcd_util.get_server()
        services = server.rcd.service.list_types()

        services.sort(lambda x,y:cmp(string.lower(x["alias"]),
                                     string.lower(y["alias"])))

        for s in services:
            self.item_id_list.append(s["alias"])
            
            item = gtk.MenuItem(s["name"])
            item.show()

            def activate_cb(item, id, opt):
                if id != self.__last_id:
                    opt.__last_id = id
                    opt.emit("selected", id)

            item.connect("activate", activate_cb, s["alias"], self)

            menu.append(item)

        menu.show()
        self.set_menu(menu)

        ## Let's try to advertise zenworks.
        for id in self.item_id_list:
            if id == "zenworks":
                self.set_service_by_id(id)
                break


    def get_service_id(self):
        h = self.get_history()
        if h < 0:
            return None
        return self.item_id_list[h]

    def set_service_by_id(self, id):
        if not id in self.item_id_list:
            print "Unknown service '%s'" % id
            assert 0

        i = self.item_id_list.index(id)
        self.set_history(i)

    ###
    ### ServerListener methods
    ###

    def channels_changed(self):
        id = self.get_service_id()
        self.build()
        if id is not None and id in self.item_id_list:
            self.set_service_by_id(id)

gobject.type_register(ServiceTypesOption)

gobject.signal_new("selected",
                   ServiceTypesOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,))
