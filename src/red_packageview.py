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

import gobject, gtk
import rcd_util
import red_pendingops, red_packagearray
import red_pixbuf, red_settings
import red_packagebook
import red_thrashingtreeview
import red_locks

from red_gettext import _

class CellRendererActivatablePixbuf(gtk.GenericCellRenderer):

    __gproperties__ = {
        "pixbuf" : (gtk.gdk.Pixbuf, "pixbuf property",
                    "the pixbuf", gobject.PARAM_READWRITE)
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.set_property("mode", gtk.CELL_RENDERER_MODE_ACTIVATABLE)
        self.pixbuf_renderer = gtk.CellRendererPixbuf()

    def do_set_property(self, pspec, value):
        return self.pixbuf_renderer.set_property(pspec.name, value)

    def do_get_property(self, pspec):
        return self.pixbuf_renderer.get_property(pspec.name)

    def on_get_size(self, widget, cell_area):
        return self.pixbuf_renderer.get_size(widget, cell_area)

    def on_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):
        return self.pixbuf_renderer.render(window, widget,
                                           background_area,
                                           cell_area, expose_area,
                                           flags)

    def on_activate(self, event, widget, path,
                    background_area, cell_area, flags):
        self.emit("activated", path)
        return 1

gobject.type_register(CellRendererActivatablePixbuf)

gobject.signal_new("activated",
                   CellRendererActivatablePixbuf,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

###############################################################################

class _ShowChannelNames(gobject.GObject):

    conf_str = "UI/show_channel_names"

    def __init__(self):
        gobject.GObject.__init__(self)
        config = red_settings.get_config()
        self.__show = int(config.get(self.conf_str + "=0"))

    def set(self, x):
        if self.__show ^ x:
            self.__show = x
            config = red_settings.get_config()
            config.set(self.conf_str, x)
            config.sync()
            self.emit("changed", x)

    def get(self):
        return self.__show

gobject.type_register(_ShowChannelNames)
gobject.signal_new("changed",
                   _ShowChannelNames,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT,))

_showchnames = _ShowChannelNames()

def show_channel_names_get():
    return _showchnames.get()

def show_channel_names_set(x):
    _showchnames.set(x)

###############################################################################

class PackageView(red_thrashingtreeview.TreeView):

    def __init__(self, model):
        gobject.GObject.__init__(self)
        red_thrashingtreeview.TreeView.__init__(self)

        self.set_rules_hint(1)

        self.__activated_fn = None

        self.set_model(model)

        select = self.get_selection()
        select.set_mode(gtk.SELECTION_MULTIPLE)

        self.__ch_icon_col = None
        self.__ch_name_and_icon_col = None

        def channel_names_cb(showchnames, flag, view):
            if view.__ch_icon_col and view.__ch_name_and_icon_col:
                view.__ch_name_and_icon_col.set_visible(flag)
                view.__ch_icon_col.set_visible(not flag)
                view.columns_autosize()
        _showchnames.connect("changed", channel_names_cb, self)

        def selection_changed_cb(select, view):
            pkgs = view.get_selected_packages()
            view.emit("selected", pkgs)

        # This callback gets invoked before the selection has
        # been updated, which causes get_selected to return
        # out-of-date information unless we do the query in an
        # idle callback.
        def button_clicked_for_popup_cb(view, ev, select):
            if ev.button == 2:
                return 1

            if ev.button == 3:
                def clicked_idle_cb(view, ev, select, b, t, x, y):
                    view.emit("popup", ev, b, t, x, y)

                gtk.idle_add(clicked_idle_cb,
                             view, ev, select,
                             ev.button, ev.time,
                             ev.x, ev.y)
                return 1

            return 0

        def row_activated_cb(view, path, col):
            model = view.get_model()
            pkg = model.get_list_item(path[0])
            self.emit("activated", path[0], pkg)

        select.connect("changed",
                       selection_changed_cb,
                       self)

        self.connect("row-activated",
                     row_activated_cb)

        self.connect("button-press-event",
                     button_clicked_for_popup_cb,
                     select)

    def get_selected_packages(self):
        def selected_cb(model, path, iter, list):
            if iter:
                pkg = model.get_list_item(path[0])
                list.append(pkg)

        pkgs = []
        select = self.get_selection()
        select.selected_foreach(selected_cb, pkgs)
        return pkgs

    ## This 'activated_fn' business is just a hack to get a call to
    ## toggle_action to be the default behavior.
    def set_activated_fn(self, fn):
        self.__activated_fn = fn

    def do_selected(self, pkgs):
        pass
        #print "selected %s (%d)" % (pkg["name"], i)

    def do_activated(self, i, pkg):
        if self.__activated_fn:
            self.__activated_fn(self, i, pkg)
        else:
            red_pendingops.toggle_action(pkg)
        #print "activated %s (%d)" % (pkg["name"], i)

    def do_popup(self, ev, ev_button, ev_time, ev_x, ev_y):
        menu = gtk.Menu()
        menu.attach_to_widget(self, None)

        pkgs = self.get_selected_packages()

        path, column, cell_x, cell_y = self.get_path_at_pos(ev_x, ev_y)
        model = self.get_model()
        clicked_pkg = model.get_list_item(path[0])

        if not clicked_pkg in pkgs:
            pkgs = [clicked_pkg]
            self.set_cursor(path, column)

        def set_package_action(pkgs, action):
            for pkg in pkgs:
                if red_pendingops.can_perform_action_single(pkg, action):
                    red_pendingops.set_action(pkg, action)

        # Install
        item = gtk.ImageMenuItem(_("Mark for Installation"))
        image = red_pixbuf.get_widget("to-be-installed")
        item.set_image(image)
        if not red_pendingops.can_perform_action_multiple(pkgs,
                                                          red_pendingops.TO_BE_INSTALLED):
            item.set_sensitive(0)
        item.show_all()
        menu.append(item)

        item.connect("activate",
                     lambda x:set_package_action(pkgs, red_pendingops.TO_BE_INSTALLED))

        # Remove
        item = gtk.ImageMenuItem(_("Mark for Removal"))
        image = red_pixbuf.get_widget("to-be-removed")
        item.set_image(image)
        if not red_pendingops.can_perform_action_multiple(pkgs,
                                                          red_pendingops.TO_BE_REMOVED):
            item.set_sensitive(0)
        item.show_all()
        menu.append(item)

        item.connect("activate",
                     lambda x:set_package_action(pkgs, red_pendingops.TO_BE_REMOVED))

        # Cancel
        item = gtk.ImageMenuItem(_("Cancel"))
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        item.set_image(image)
        item.show_all()
        if not red_pendingops.can_perform_action_multiple(pkgs,
                                                          red_pendingops.NO_ACTION):
            item.set_sensitive(0)
        menu.append(item)

        item.connect("activate",
                     lambda x:set_package_action(pkgs, red_pendingops.NO_ACTION))

        item = gtk.SeparatorMenuItem()
        item.show_all()
        menu.append(item)

        # Info
        item = gtk.ImageMenuItem(_("Information"))
        image = red_pixbuf.get_widget("info")
        item.set_image(image)
        item.show_all()
        if len(pkgs) != 1:
            item.set_sensitive(0)
        menu.append(item)

        item.connect("activate",
                     lambda x:red_packagebook.show_package_info(pkgs[0]))


        menu.popup(None, None, None, ev_button, ev_time)

    def set_model(self, model):
        assert isinstance(model, red_packagearray.PackageArray)

        red_thrashingtreeview.TreeView.set_model(self, model)

    def append_status_column(self,
                             column_title=_("Status"),
                             show_status_icon=0,
                             show_status_name=1):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        if show_status_icon:
            render_icon = gtk.CellRendererPixbuf()
            expand = not show_status_name
            col.pack_start(render_icon, expand)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_STATUS_ICON)
            render_icon.set_property("xalign", 0.5)

        if show_status_name:
            render_text = gtk.CellRendererText()
            col.pack_start(render_text, 0)
            col.set_attributes(render_text,
                               markup=red_packagearray.COLUMN_STATUS)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_id=red_packagearray.COLUMN_STATUS
                        )

        return col

    def append_action_column(self,
                             column_title=_("Action"),
                             show_action_icon=1,
                             show_action_name=0,
                             activatable=1):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        def activated_cb(r, p, t):
            model = t.get_model()
            pkg = model.get_list_item(int(p))
            t.emit("activated", int(p), pkg)

        if show_action_icon:
            render_icon = CellRendererActivatablePixbuf()
            if activatable:
                render_icon.connect("activated", activated_cb, self)
            expand = not show_action_name
            col.pack_start(render_icon, expand)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_ACTION_ICON)
            render_icon.set_property("xalign", 0.5)

        if show_action_name:
            render_text = gtk.CellRendererText()
            col.pack_start(render_text, 0)
            col.set_attributes(render_text,
                               markup=red_packagearray.COLUMN_ACTION)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_id=red_packagearray.COLUMN_ACTION
                        )

        return col

    def append_channel_column(self,
                              column_title=_("Channel"),
                              show_channel_icon=1,
                              show_channel_name=1,
                              optionally_show_channel_name=0):

        def assemble_column(with_icon, with_name):
            col = gtk.TreeViewColumn()
            col.set_title(column_title)

            if with_icon:
                render_icon = gtk.CellRendererPixbuf()
                col.pack_start(render_icon, not with_name)
                col.set_attributes(render_icon,
                                   pixbuf=red_packagearray.COLUMN_CH_ICON)
                render_icon.set_property("xalign", 0.5)

            if with_name:
                render_text = gtk.CellRendererText()
                col.pack_start(render_text, 1)
                col.set_attributes(render_text,
                                   text=red_packagearray.COLUMN_CH_NAME)

            return col


        if optionally_show_channel_name:

            col1 = assemble_column(1, 0)
            col2 = assemble_column(1, 1)
            show_name = show_channel_names_get()

            self.add_column(col1,
                            title=column_title,
                            initially_visible=not show_name,
                            sort_id=red_packagearray.COLUMN_CH_NAME)

            self.add_column(col2,
                            title=column_title,
                            initially_visible=show_name,
                            sort_id=red_packagearray.COLUMN_CH_NAME)

            self.__ch_icon_col = col1
            self.__ch_name_and_icon_col = col2

        else:

            col = assemble_column(show_channel_icon, show_channel_name)

            self.add_column(col,
                            title=column_title,
                            initially_visible=1,
                            sort_id=red_packagearray.COLUMN_CH_NAME
                            )


    def append_name_column(self,
                           column_title=_("Package"),
                           show_channel_icon=0,
                           show_section_icon=0):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        if show_channel_icon:
            render_icon = gtk.CellRendererPixbuf()
            col.pack_start(render_icon, 0)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_CH_ICON)

        if show_section_icon:
            render_icon = gtk.CellRendererPixbuf()
            col.pack_start(render_icon, 0)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_SEC_ICON)

        render_text = gtk.CellRendererText()
        col.pack_start(render_text, 1)
        col.set_attributes(render_text, text=red_packagearray.COLUMN_NAME)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_id=red_packagearray.COLUMN_NAME
                        )
        return col

    def append_version_column(self, column_title=_("Version")):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_EVR)
        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        )
        return col

    def append_current_version_column(self, column_title=_("Current Version")):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_OLD_EVR)
        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        )
        return col

    def append_importance_column(self, column_title=_("Importance")):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_IMPORTANCE)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_id=red_packagearray.COLUMN_IMPORTANCE
                        )
        return col

    def append_locked_column(self):
        col = gtk.TreeViewColumn(None,
                                 gtk.CellRendererPixbuf(),
                                 pixbuf=red_packagearray.COLUMN_LOCKED_ICON)
        widget = red_pixbuf.get_widget("lock")
        widget.show()

        self.add_column(col,
                        widget=widget,
                        initially_visible=1,
                        sort_id=red_packagearray.COLUMN_LOCKED
                        )
        return col

    def append_size_column(self, column_title=_("Size")):
        render = gtk.CellRendererText()
        render.set_property("xalign", 1.0)
        col = gtk.TreeViewColumn(column_title,
                                 render,
                                 text=red_packagearray.COLUMN_SIZE)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_id=red_packagearray.COLUMN_SIZE
                        )
        return col


gobject.type_register(PackageView)

gobject.signal_new("selected",
                   PackageView,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

gobject.signal_new("activated",
                   PackageView,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT,
                    gobject.TYPE_PYOBJECT,))

gobject.signal_new("popup",
                   PackageView,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gtk.gdk.Event.__gtype__,
                    gobject.TYPE_INT, # button,
                    gobject.TYPE_INT, # time
                    gobject.TYPE_INT, # x coordinate
                    gobject.TYPE_INT, # y coordinate
                    )
                   )
