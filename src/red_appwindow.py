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

import os, string, sys, gtk

import ximian_xmlrpclib
import rcd_util
import red_main
import red_menubar
import red_transaction
import red_installfiles
import red_component
import red_componentbook
import red_pixbuf
import red_pendingops
import red_depcomponent
import red_prefs
import red_subscriptions
import red_users
import red_activation
import red_about
import red_mount
import red_serverinfo
import red_sidebar
import red_toolbar
import red_packagearray, red_packageview
import red_packagebook
import red_searchbox
import red_services
import red_settings
import red_actionbar
import red_connection
import red_statusbar
from red_gettext import _

def run_transaction_cb(app):
    install_packages = red_pendingops.packages_with_actions(
        red_pendingops.TO_BE_INSTALLED)
    remove_packages = red_pendingops.packages_with_actions(
        red_pendingops.TO_BE_REMOVED)

    # FIXME: This feels like a hack.  Go through the remove_packages and
    # if any of them have an __old_package field, use that package for
    # the removal instead of the actual package.  This is so you can right
    # click on an upgrade and select "remove".
    remove_packages = [x.get("__old_package", x) for x in remove_packages]

    transaction_type = rcd_util.PACKAGE_TYPE_PACKAGE
    if len(install_packages) > 0:
        transaction_type = rcd_util.get_package_type(install_packages[0])
    elif len(remove_packages) > 0:
        transaction_type = rcd_util.get_package_type(remove_packages[0])

    dep_comp = red_depcomponent.DepComponent(install_packages,
                                             remove_packages,
                                             0,
                                             transaction_type)
    app.componentbook.push_component(dep_comp)

def verify_deps_cb(app):
    dep_comp = red_depcomponent.DepComponent(verify=1)
    app.componentbook.push_component(dep_comp)

def help_cb(app):

    def which(file):
        for p in string.split(os.environ["PATH"], ":"):
            if not p:
                continue

            path = os.path.normpath(p + "/" + file)

            if os.access(path, os.F_OK | os.X_OK):
                return path

    # TRANSLATORS: *Only* localize this to the language code if the
    # Red Carpet help is localized.
    help_locale = _("C")

    xml_files = ("%s/%s/red-carpet.xml" % (red_main.help_path, help_locale),
                 "%s/C/red-carpet.xml" % red_main.help_path)
    html_files = ("%s/%s/red-carpet.html" % (red_main.help_path, help_locale),
                  "%s/C/red-carpet.html" % red_main.help_path)

    url_handlers = (
        ("gnome-help", "ghelp", xml_files),           # GNOME 2
        ("gnome-url-show", "file", html_files),       # XD2 w/o yelp?
        ("htmlview", "file", html_files),             # RH 9
        ("khelpcenter", "file", html_files),          # KDE
        ("gnome-help-browser", "file", html_files),   # GNOME 1.x
        ("gnome-moz-remote", "file", html_files),     # GNOME 1.x w/o help
                                                      #   browser?
        ("mozilla", "file", html_files),              # dunno, but a sane
                                                      #   fallback
        ("netscape", "file", html_files),             # CDE
    )

    for url_info in url_handlers:
        fullpath = which(url_info[0])
        if not fullpath:
            continue

        for f in url_info[2]:
            if not os.path.exists(f):
                continue

            url = url_info[1] + "://" + f

            pid = os.spawnv(os.P_NOWAIT, fullpath, (fullpath, url))
            return

        dialog = gtk.MessageDialog(app, 0,
                                   gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,
                                   _("Unable to show help because the help "
                                     "files were missing.  Please report "
                                     "this to your vendor."))
        dialog.run()
        dialog.destroy()
        return

    dialog = gtk.MessageDialog(app, 0,
                               gtk.MESSAGE_ERROR,
                               gtk.BUTTONS_OK,
                               _("Unable to show help because there are no "
                                 "applications available to view help."))
    dialog.run()
    dialog.destroy()
            
class AppWindow(gtk.Window,
                red_component.ComponentListener,
                red_pendingops.PendingOpsListener):

    def __init__(self, server):

        gtk.Window.__init__(self)
        red_component.ComponentListener.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)

        self.server = server
        self.__title = None
        self.component_stack = []

        self.busy_count = 0
        self.busy_handler = 0

        self.vbox = gtk.VBox(0, 0)
        self.add(self.vbox)
        self.vbox.show()

        self.components = []

        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.set_icon(red_pixbuf.get_pixbuf("red-carpet"))

        # Menubar
        self.menubar = red_menubar.MenuBar(self.accel_group)
        self.menubar.set_user_data(self)
        self.assemble_menubar(self.menubar)
        self.vbox.pack_start(self.menubar, expand=0, fill=1)
        self.menubar.show()

        ## Toolbar
        self.toolbar = red_toolbar.Toolbar()
        self.assemble_toolbar(self.toolbar)
        self.vbox.pack_start(self.toolbar, expand=0, fill=1)
        self.toolbar.show_all()

        ## GtkSettings
        settings = gtk.settings_get_default()
        self.toolbar.set_style(settings.get_property("gtk-toolbar-style"))
        self.toolbar.set_icon_size(settings.get_property("gtk-toolbar-icon-size"))

        def settings_notify_toolbar_style_cb(set, pspec, app):
            app.toolbar.set_style(set.get_property("gtk-toolbar-style"))

        def settings_notify_toolbar_icon_size_cb(set, pspec, app):
            app.toolbar.set_icon_size(settings.get_property("gtk-toolbar-icon-size"))
        
        settings.connect("notify::gtk-toolbar-style",
                         settings_notify_toolbar_style_cb, self)
        settings.connect("notify::gtk-toolbar-icon-size",
                         settings_notify_toolbar_icon_size_cb, self)

        self.transient_windows = {}

        self.hpaned = gtk.HPaned()
        self.vbox.pack_start(self.hpaned, expand=1, fill=1)

        self.sidebar = red_sidebar.SideBar()
        # Ensure a sane width for the sidebar if visible
        if self.sidebar.get_property("visible"):
            w, h = self.sidebar.size_request()
            self.sidebar.set_size_request(int(w * 1.5), -1)

        self.hpaned.pack1(self.sidebar, resize=0, shrink=0)

        main_box = gtk.VBox(0, 6)
        main_box.set_border_width(6)
        self.hpaned.pack2(main_box, resize=1, shrink=1)

        ## Actionbar
        self.actionbar = red_actionbar.Actionbar()
        self.assemble_actionbar(self.actionbar)
        main_box.pack_end(self.actionbar, expand=0, fill=0)

        # Componentbook
        self.componentbook = red_componentbook.ComponentBook()

        def componentbook_switched_cb(cbook, comp):
            old_comp = self.get_component()
            if id(old_comp) == id(comp):
                return
            self.set_component(comp)
            
            if comp.is_busy():
                self.busy_start()
            if old_comp and old_comp.is_busy():
                self.busy_stop()

            # Clear the status bar, update the toolbar
            self.statusbar.pop(0)
            self.toolbar.sensitize_toolbar_items()
            self.actionbar.sensitize_actionbar_items()

            # Show the new component, hide the old one
            comp.visible(1)
            comp.set_parent(self)
            comp.activated()
            if not comp.show_actionbar():
                self.actionbar.hide()
            else:
                self.actionbar.show()

            if old_comp:
                old_comp.visible(0)
                old_comp.deactivated()
                old_comp.set_parent(None)
                
            self.set_title(comp.name())
            
        self.componentbook.connect("switched", componentbook_switched_cb)

        main_box.pack_start(self.componentbook, expand=1, fill=1)
        main_box.show_all()
        self.hpaned.show()

        ## Statusbar
        self.statusbar = red_statusbar.Statusbar()
        self.statusbar.show()
        self.vbox.pack_start(self.statusbar, expand=0, fill=1)
        notifier = red_connection.get_notifier()
        notifier.connect("connected",
                         lambda x,y,z:z.set_connected(y), self.statusbar)
        self.statusbar.connect("connect", lambda x:self.connect_to_daemon())
        notifier.notify()

        self.menubar.set_statusbar(self.statusbar)

        self.connect("delete_event", lambda x, y:self.shutdown())

        ## Geometry handling
        self.load_geometry()

        self.save_geometry_id = 0

        def size_allocate_cb(win, alloc):

            def save_geometry_cb(win):
                win.save_geometry()
                win.save_geometry_id = 0

                return 0
            
            if not self.save_geometry_id:
                self.save_geometry_id = gtk.idle_add(save_geometry_cb, win)

        self.connect("size_allocate", size_allocate_cb)

    def save_geometry(self):
        conf = red_settings.get_config()

        x, y, w, h = self.allocation

        conf.set("Geometry/width", w)
        conf.set("Geometry/height", h)

        x, y, w, h = self.sidebar.allocation

        conf.set("Geometry/sidebar_width", w)
        
        conf.sync()

    def load_geometry(self):
        conf = red_settings.get_config()

        w = int(conf.get("Geometry/width=0"))
        h = int(conf.get("Geometry/height=0"))

        if w and h:
            self.set_default_size(w, h)
        else:
            w, h = self.size_request()
            w = int(w * 1.3)
            h = int(w * .667)
            self.set_default_size(w, h)

        w = int(conf.get("Geometry/sidebar_width=0"))

        if w:
            self.hpaned.set_position(w)

    def set_title(self, component=None):
        buf = ""
        if component:
            buf += component + " - "

        buf += red_main.get_title()

        gtk.Window.set_title(self, buf)

    ##
    ## Toolbar and menubar callback and sensitivity functions
    ##

    def install_sensitive_cb(self):
        comp = self.componentbook.get_visible_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()

        if not pkgs:
            return 0
        
        return red_pendingops.can_perform_action_multiple(
            pkgs, red_pendingops.TO_BE_INSTALLED)

    def remove_sensitive_cb(self):
        comp = self.componentbook.get_visible_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()

        if not pkgs:
            return 0
        
        return red_pendingops.can_perform_action_multiple(
            pkgs, red_pendingops.TO_BE_REMOVED)

    def cancel_sensitive_cb(self):
        comp = self.componentbook.get_visible_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()

        if not pkgs:
            return 0
        
        return red_pendingops.can_perform_action_multiple(
            pkgs, red_pendingops.NO_ACTION)

    def set_package_action_cb(self, action):
        comp = self.componentbook.get_visible_component()

        assert comp is not None
        
        pkgs = comp.get_current_packages()
        for pkg in pkgs:
            if red_pendingops.can_perform_action_single(pkg, action):
                red_pendingops.set_action(pkg, action)

    def info_sensitive_cb(self):
        comp = self.componentbook.get_visible_component()

        if not comp:
            return 0

        pkgs = comp.get_current_packages()
        return len(pkgs) > 0

    def package_info_cb(self):
        comp = self.componentbook.get_visible_component()

        assert comp is not None
        
        pkgs = comp.get_current_packages()

        if len(pkgs) > 5:
            dialog = gtk.MessageDialog(self, 0,
                                       gtk.MESSAGE_QUESTION,
                                       gtk.BUTTONS_OK_CANCEL,
                                       _("Are you sure you want to open %d "
                                         "package information windows?") % len(pkgs))
            resp = dialog.run()
            dialog.destroy()
            if resp != gtk.RESPONSE_OK:
                return

        for p in pkgs:
            red_packagebook.show_package_info(p, parent=self)

    def sensitize_run_button(self):
        comp = self.componentbook.get_visible_component()

        if not comp:
            allow_run = 1
        else:
            allow_run = comp.run_sensitized()

        return allow_run and red_pendingops.pending_ops_exist()

    ##
    ## Toolbar
    ##

    def assemble_toolbar(self, bar):

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_LARGE_TOOLBAR)

        bar.run = bar.add(text=_("Run Now"),
                          tooltip=_("Perform installations and removals"),
                          sensitive_fn=self.sensitize_run_button,
                          stock=gtk.STOCK_EXECUTE,
                          callback=lambda x:run_transaction_cb(self))

        bar.append_space()

        bar.subs = bar.add(text=_("Catalogs"),
                           tooltip=_("Change your catalog subscriptions"),
                           pixbuf=red_pixbuf.get_pixbuf("channels-24"),
                           callback=lambda x:self.open_or_raise_window(red_subscriptions.SubscriptionsWindow))

        def verify_and_refresh_sensitive_cb():
            comp=self.componentbook.get_visible_component()
            return comp.run_sensitized()

        bar.refresh = bar.add(text=_("Refresh"),
                              tooltip=_("Refresh catalog data"),
                              stock = gtk.STOCK_REFRESH,
                              sensitive_fn=verify_and_refresh_sensitive_cb,
                              callback=lambda x:rcd_util.refresh(self))

    ##
    ## Actionbar.
    ##

    def assemble_actionbar(self, bar):

        bar.install = bar.add(text=_("Mark for _Installation"),
                              tooltip=_("Mark selected packages for installation"),
                              pixbuf=red_pixbuf.get_pixbuf("to-be-installed"),
                              sensitive_fn=self.install_sensitive_cb,
                              callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_INSTALLED))

        bar.remove = bar.add(text=_("Mark for _Removal"),
                             tooltip=_("Mark selected packages for removal"),
                             pixbuf=red_pixbuf.get_pixbuf("to-be-removed"),
                             sensitive_fn=self.remove_sensitive_cb,
                             callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_REMOVED))

        bar.cancel = bar.add(text=_("_Cancel"),
                             tooltip=_("Cancel marked package actions"),
                             stock=gtk.STOCK_CANCEL,
                             sensitive_fn=self.cancel_sensitive_cb,
                             callback=lambda x:self.set_package_action_cb(red_pendingops.NO_ACTION))

        bar.info = bar.add(text=_("I_nformation"),
                           tooltip=_("Package information"),
                           pixbuf=red_pixbuf.get_pixbuf("info"),
                           sensitive_fn=self.info_sensitive_cb,
                           callback=lambda x:self.package_info_cb())


    def connect_to_daemon(self):
        # We want to revert to our old settings if we don't connect to
        # a new daemon successfully.
        daemon_data = red_settings.DaemonData()
        old_settings = daemon_data.data_get()
        
        server, local = red_connection.connect_from_window(self)

        if server is None:
            daemon_data.data_set(old_settings)
            return

        rcd_util.register_server(server, local)

    # The return value is for the benefit of our delete_event handler.
    def shutdown(self):
        if red_transaction.ok_to_quit(self):
            gtk.mainquit()
            return 0
        return 1

    def open_or_raise_window(self, type):
        if self.transient_windows.has_key(type):
            self.transient_windows[type].present()
        else:
            win = type()
            self.transient_windows[type] = win
            def remove_window_cb(w, a, t):
                del a.transient_windows[t]
            win.connect("destroy", remove_window_cb, self, type)
            win.set_transient_for(self)
            win.show()

    def select_all_cb(self, sel):
        comp = self.componentbook.get_visible_component()
        if not comp:
            return
        
        if sel:
            comp.select_all()
        else:
            comp.unselect_all()

    ##
    ## Menubar
    ##

    def assemble_menubar(self, bar):

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_BUTTON)

        file_str = _("_File")
        edit_str = _("_Edit")
        view_str = _("_View")
        actions_str = _("_Actions")
        help_str = _("_Help")

        bar.add("/" + file_str)
        bar.add("/" + edit_str)
        bar.add("/" + view_str)
        bar.add("/" + actions_str)
        bar.add("/" + help_str)

        bar.add("/%s/%s" % (file_str, _("Connect to daemon...")),
                description=_("Connect to a remote daemon"),
                callback=lambda x:self.connect_to_daemon(),
                pixbuf_name="connect",
                accelerator="<Control>O")

        bar.add("/%s/sep" % file_str, is_separator=1)

        def install_file_sensitive_fn():
            return rcd_util.check_server_permission("install")

        bar.add("/%s/%s" % (file_str, _("Install from _File...")),
                description=_("Install a package from a local file"),
                pixbuf=red_pixbuf.get_pixbuf("install-from-file"),
                sensitive_fn=install_file_sensitive_fn,
                callback=lambda x:red_installfiles.install_local(self))

        def install_url_sensitive_fn():
            return rcd_util.check_server_permission("install") and \
                   red_installfiles.can_install_remote()

        bar.add("/%s/%s" % (file_str, _("Install from _URL...")),
                description=_("Install a package from a remote URL"),
                pixbuf=red_pixbuf.get_pixbuf("install-from-url"),
                sensitive_fn=install_url_sensitive_fn,
                callback=lambda x:red_installfiles.install_remote(self))

        bar.add("/%s/sep2" % file_str, is_separator=1)

        ##
        ## Mount command
        ##

        def mount_callback(app):
            app.open_or_raise_window(red_mount.MountWindow)

        def mount_sensitive_fn():
            return rcd_util.check_server_permission("superuser")

        bar.add("/%s/%s" % (file_str, _("_Mount Directory...")),
                description=_("Mount a directory as a catalog"),
                callback=mount_callback,
                sensitive_fn=mount_sensitive_fn,
                accelerator="<Control>M")

        ##
        ## Unmount command
        ##

        def unmount_callback(app):
            app.open_or_raise_window(red_mount.UnmountWindow)

        def unmount_sensitive_fn():
            return rcd_util.check_server_permission("superuser") and \
                   red_mount.has_mounted_channels()

        bar.add("/%s/%s" % (file_str, _("U_nmount Directory...")),
                description=_("Unmount a directory"),
                callback=unmount_callback,
                sensitive_fn=unmount_sensitive_fn,
                accelerator="<Control>N")
        

        bar.add("/%s/sep3" % file_str, is_separator=1)

        ##
        ## Activate
        ##

        def activate_sensitive_fn():
            return rcd_util.check_server_permission("superuser") \
                   and rcd_util.get_all_services()
        
        bar.add("/%s/%s" % (file_str, _("_Register...")),
                description=_("Register daemon"),
                callback=lambda x:self.open_or_raise_window(red_activation.ActivationWindow),
                sensitive_fn=activate_sensitive_fn)

        bar.add("/%s/sep4" % file_str, is_separator=1)
        
        bar.add("/%s/%s" % (file_str, _("Quit")),
                description=_("Quit Red Carpet"),
                stock=gtk.STOCK_QUIT,
                callback=lambda x:self.shutdown())


        ##
        ## Select all/none
        ##

        def select_all_sensitive_cb():
            comp = self.componentbook.get_visible_component()
            if not comp:
                return 0
            return comp.select_all_sensitive()

        bar.add("/%s/%s" % (edit_str, _("Select _All")),
                description=_("Select all items"),
                callback=lambda x:self.select_all_cb(1),
                accelerator="<Control>a",
                sensitive_fn=select_all_sensitive_cb)

        bar.add("/%s/%s" % (edit_str, _("Select _None")),
                description=_("Deselect all items"),
                callback=lambda x:self.select_all_cb(0),
                sensitive_fn=select_all_sensitive_cb,
                accelerator="<Shift><Control>A")

        bar.add("/%s/sep" % edit_str, is_separator=1)

        bar.add("/%s/%s" % (edit_str, _("Services...")),
                description=_("Edit services"),
                callback=lambda x:self.open_or_raise_window(red_services.ServicesWindow),
                accelerator="<Control>E")

        bar.add("/%s/%s" % (edit_str, _("Catalog _Subscriptions...")),
                description=_("Edit your catalog subscriptions"),
                callback=lambda x:self.open_or_raise_window(red_subscriptions.SubscriptionsWindow),
                pixbuf=red_pixbuf.get_pixbuf("channels-16"),
                accelerator="<Control>B")

        bar.add("/%s/%s" % (edit_str, _("_Preferences...")),
                description=_("Edit your Red Carpet preferences"),
                stock=gtk.STOCK_PREFERENCES,
                callback=lambda x:self.open_or_raise_window(red_prefs.PrefsWindow))

        bar.add("/%s/%s" % (edit_str, _("_Users...")),
                description=_("Edit user permissions for this daemon"),
                pixbuf=red_pixbuf.get_pixbuf("users"),
                callback=lambda x:self.open_or_raise_window(red_users.UsersWindow))

        ##
        ## Sidebar
        ##

        def checked_get_cb():
            return self.sidebar.get_property("visible")
        def checked_set_cb(flag):
            self.sidebar.change_visibility()

        bar.add("/%s/%s" % (view_str, _("_Sidebar")),
                description=_("Hide or show the Pending Actions sidebar"),
                checked_get=checked_get_cb,
                checked_set=checked_set_cb)

        bar.add("/%s/%s" % (view_str, _("_Advanced Search Options")),
                description=_("Hide or show advanced search options"),
                checked_get=red_searchbox.show_advanced_get,
                checked_set=red_searchbox.show_advanced_set)

        bar.add("/%s/%s" % (view_str, _("_Catalog Names")),
                description=_("Hide or show catalog names in package lists"),
                checked_get=red_packageview.show_channel_names_get,
                checked_set=red_packageview.show_channel_names_set)

        bar.add("/%s/sep" % view_str, is_separator=1)

        bar.add("/%s/%s" % (view_str, _("Package _Information...")),
                description=_("View information about currently selected packages"),
                pixbuf_name="info",
                callback=lambda x:self.package_info_cb(),
                sensitive_fn=self.info_sensitive_cb,
                accelerator="<Control>I")

        bar.add("/%s/sep1" % view_str, is_separator=1)

        bar.add("/%s/%s" % (view_str, _("_Daemon Information...")),
                description=_("View information about this daemon"),
                callback=red_serverinfo.view_server_info_cb)

        bar.add("/%s/sep2" % view_str, is_separator=1)

        ##
        ## Run Transaction
        ##

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)

        bar.add("/%s/%s" % (actions_str, _("Run _Now")),
                description=_("Run the current transaction"),
                image=image,
                callback=run_transaction_cb,
                sensitive_fn=self.sensitize_run_button,
                accelerator="<Control>X")

        ##
        ## Verify System Dependencies
        ##

        def verify_and_refresh_sensitive_cb():
            comp = self.componentbook.get_visible_component()
            return comp.run_sensitized()
                
        bar.add("/%s/%s" % (actions_str, _("_Verify System Dependencies")),
                description=_("Verify that all system dependencies are met"),
                callback=verify_deps_cb,
                sensitive_fn=verify_and_refresh_sensitive_cb,
                accelerator="<Control>D")

        bar.add("/%s/sep1" % actions_str, is_separator=1)

        ##
        ## Install Package
        ##

        bar.add("/%s/%s" % (actions_str, _("Mark for I_nstallation")),
                description=_("Mark this package for installation"),
                pixbuf_name="to-be-installed",
                callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_INSTALLED),
                sensitive_fn=self.install_sensitive_cb)

        ##
        ## Remove Package
        ##

        bar.add("/%s/%s" % (actions_str, _("Mark for _Removal")),
                description=_("Mark this package for removal"),
                pixbuf_name="to-be-removed",
                callback=lambda x:self.set_package_action_cb(red_pendingops.TO_BE_REMOVED),
                sensitive_fn=self.remove_sensitive_cb)

        ##
        ## Cancel Action
        ##

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)

        bar.add("/%s/%s" % (actions_str, _("_Cancel")),
                description=_("Cancel installation or removal mark"),
                image=image,
                callback=lambda x:self.set_package_action_cb(red_pendingops.NO_ACTION),
                sensitive_fn=self.cancel_sensitive_cb)

        bar.add("/%s/sep2" % actions_str, is_separator=1)

        ##
        ## Refresh Channel Data
        ##

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_MENU)

        bar.add("/%s/%s" % (actions_str, _("Re_fresh Catalog Data")),
                description=_("Download latest catalog data"),
                image=image,
                callback=rcd_util.refresh,
                sensitive_fn=verify_and_refresh_sensitive_cb,
                accelerator="<Control>R")

        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_HELP, gtk.ICON_SIZE_MENU)

        bar.add("/%s/%s" % (help_str, _("_Contents")),
                description=_("View Red Carpet help"),
                image=image,
                callback=help_cb,
                accelerator="F1")

        bar.add("/%s/%s" % (help_str, _("_About...")),
                description=_("About Red Carpet"),
                pixbuf_name="menu-about",
                callback=lambda x:self.open_or_raise_window(red_about.About))


    def register_component(self, comp):

        # We need to make the component menu items checked
        # instead of radio-style, because with a radio group you
        # always have to have exactly one item set: when a non-navigable
        # component is on the screen (like the dep resolution page),
        # the component gets reset if you open any menu.
        def checked_get_cb():
            return id(self.componentbook.get_visible_component()) == id(comp)
        def checked_set_cb(flag):
            if flag:
                self.componentbook.view_component(comp)

        self.menubar.add("/%s/%s" % (_("_View"), comp.menu_name()),
                         description=_("Go to the '%s' page" % comp.name()),
                         checked_get=checked_get_cb,
                         checked_set=checked_set_cb,
                         accelerator=comp.accelerator())

        self.components.append(comp)
        self.componentbook.add_component(comp)

    def busy_start(self):
        self.busy_count += 1
        if self.window:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))

    def busy_stop(self):
        if self.busy_count > 0:
            self.busy_count -= 1
        if self.busy_count == 0 and self.window:
            self.window.set_cursor(None)

    ###
    ### Handlers for PendingOpsListener
    ###

    def pendingops_changed(self, pkg, key, value, old_value):
        def sensitize_run_cb(app):
            have_pending = app.sensitize_run_button()
            app.toolbar.run.set_sensitive(have_pending)
        gtk.idle_add(sensitize_run_cb, self)
        
    ###
    ### Handlers for Component signals (via the ComponentListener API)
    ###

    def do_component_push(self, comp):
        self.componentbook.push_component(comp)

    def do_component_pop(self):
        self.componentbook.pop_component()

    def do_component_message_push(self, msg, context_id):
        self.statusbar.pop(0) # always pop off transient messages
        self.statusbar.push(context_id, msg)

    def do_component_message_pop(self, context_id):
        self.statusbar.pop(context_id)

    def do_component_busy(self, flag):
        if flag:
            self.busy_start()
        else:
            self.busy_stop()
        
    def do_component_packages_selected(self, pkgs):
        self.toolbar.sensitize_toolbar_items()
        self.actionbar.sensitize_actionbar_items()
