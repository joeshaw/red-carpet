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

import gobject, gtk
import rcd_util
import red_pendingops, red_packagearray
import red_pixbuf
import red_packagebook
import red_thrashingtreeview

class PackageView(red_thrashingtreeview.TreeView):

    def __init__(self):
        gobject.GObject.__init__(self)
        red_thrashingtreeview.TreeView.__init__(self)

        self.set_rules_hint(1)

        self.__column_info = {}
        self.__column_order = []
        self.__sorted_by = None
        self.__reverse_sort = 0
        self.__activated_fn = None

        select = self.get_selection()
        select.set_mode(gtk.SELECTION_SINGLE)

        def selection_changed_cb(select, view):
            model, iter = select.get_selected()
            if iter:
                path = model.get_path(iter)
                pkg = model.get_list_item(path[0])
                self.emit("selected", path[0], pkg)

        # This callback gets invoked before the selection has
        # been updated, which causes get_selected to return
        # out-of-date information unless we do the query in an
        # idle callback.
        def button_clicked_for_popup_cb(view, ev, select):
            if ev.button == 3:
                def clicked_idle_cb(view, ev, select, b, t):
                    model, iter = select.get_selected()
                    if iter:
                        path = model.get_path(iter)
                        pkg = model.get_list_item(path[0])
                        view.emit("popup", ev, path[0], b, t, pkg)
                    return 0
                gtk.idle_add(clicked_idle_cb,
                             view, ev, select,
                             ev.button, ev.time)

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

    ## This 'activated_fn' business is just a hack to get a call to
    ## toggle_action to be the default behavior.
    def set_activated_fn(self, fn):
        self.__activated_fn = fn

    def do_selected(self, i, pkg):
        pass
        #print "selected %s (%d)" % (pkg["name"], i)

    def do_activated(self, i, pkg):
        if self.__activated_fn:
            self.__activated_fn(self, i, pkg)
        else:
            red_pendingops.toggle_action(pkg)
        #print "activated %s (%d)" % (pkg["name"], i)

    def do_popup(self, ev, i, ev_button, ev_time, pkg):
        menu = gtk.Menu()
        menu.attach_to_widget(self, None)

        item = gtk.ImageMenuItem("Package Info")
        image = red_pixbuf.get_widget("info")
        item.set_image(image)
        item.show_all()
        menu.append(item)

        item.connect("activate",
                     lambda x:red_packagebook.show_package_info(pkg))

        item = gtk.SeparatorMenuItem()
        item.show_all()
        menu.append(item)

        registered_action = red_pendingops.package_action(pkg)

        if registered_action != red_pendingops.NO_ACTION:
            item = gtk.ImageMenuItem("Cancel action")
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
            item.show_all()
            menu.append(item)

            item.connect("activate",
                         lambda x:red_pendingops.set_action(pkg, red_pendingops.NO_ACTION))

        if red_packagearray.pkg_is_name_installed(pkg):
            if registered_action != red_pendingops.TO_BE_REMOVED:
                item = gtk.ImageMenuItem("Remove this package")
                image = red_pixbuf.get_widget("to-be-removed")
                item.set_image(image)
                if not rcd_util.check_server_permission("remove"):
                    item.set_sensitive(0)
                item.show_all()
                menu.append(item)

                item.connect("activate",
                             lambda x:red_pendingops.set_action(pkg, red_pendingops.TO_BE_REMOVED))
        else:
            if registered_action != red_pendingops.TO_BE_INSTALLED:
                item = gtk.ImageMenuItem("Install this package")
                image = red_pixbuf.get_widget("to-be-installed")
                item.set_image(image)
                if not rcd_util.check_server_permission("install"):
                    item.set_sensitive(0)
                item.show_all()
                menu.append(item)

                item.connect("activate",
                             lambda x:red_pendingops.set_action(pkg, red_pendingops.TO_BE_INSTALLED))

        if red_packagearray.pkg_is_upgrade(pkg) and \
           registered_action != red_pendingops.TO_BE_INSTALLED:
            item = gtk.ImageMenuItem("Upgrade")
            image = red_pixbuf.get_widget("update")
            item.set_image(image)
            if not rcd_util.check_server_permission("upgrade"):
                item.set_sensitive(0)
            item.show_all()
            menu.append(item)

            item.connect("activate",
                         lambda x:red_pendingops.set_action(pkg, red_pendingops.TO_BE_INSTALLED))
        elif red_packagearray.pkg_is_downgrade(pkg) and \
             registered_action != red_pendingops.TO_BE_INSTALLED:
            item = gtk.ImageMenuItem("Downgrade")
            image = red_pixbuf.get_widget("warning", width=24, height=24)
            item.set_image(image)
            if not rcd_util.check_server_permission("upgrade"):
                item.set_sensitive(0)
            item.show_all()
            menu.append(item)

            item.connect("activate",
                         lambda x:red_pendingops.set_action(pkg, red_pendingops.TO_BE_INSTALLED))

        menu.popup(None, None, None, ev_button, ev_time)
        #print "popup on %s (%d)" % (pkg["name"], i)

    def set_model(self, model):
        assert isinstance(model, red_packagearray.PackageArray)

        red_thrashingtreeview.TreeView.set_model(self, model)
        
        #if model:
        #    self.set_headers_clickable(1)

    def add_column(self, column,
                   title=None,
                   widget=None,
                   initially_visible=0,
                   sort_fn=None,
                   sort_callback=None):

        if not title and not widget:
            title = "Untitled"

        self.__column_info[column] = { "title":title,
                                       "widget":widget,
                                       "visible":initially_visible,
                                       "sort_fn":sort_fn,
                                       "sort_callback":sort_callback,
                                     }

        self.__column_order.append(column)

        if title:
            column.set_title(title)
            column.set_alignment(0.0)
            
        if widget:
            column.set_widget(widget)
            column.set_alignment(0.5)
            
        column.set_visible(initially_visible)
        self.append_column(column)

        def sort_cb(column, view):
            if view.__sorted_by == column:
                view.sort_by(column, not self.__reverse_sort)
            else:
                view.sort_by(column, 0)
        if sort_fn or sort_callback:
            column.connect("clicked", sort_cb, self)
            column.set_clickable(1)
            

    def sort_by(self, column, reverse=0):

        if self.__sorted_by == column and not reverse ^ self.__reverse_sort:
            return

        # Fix the old column header
        if self.__sorted_by:
            self.__sorted_by.set_sort_indicator(0)

        info = self.__column_info[column]
        if not info:
            return # FIXME: probably should throw an exception
        
        if info.has_key("sort_callback"):
            info["sort_callback"](self.get_model(), reverse)
        elif info.has_key("sort_fn"):
            self.get_model().changed_sort_fn(info["sort_fn"], reverse)
        else:
            pass # FIXME: probably should throw an exception

        column.set_sort_indicator(1)
        if reverse:
            order = gtk.SORT_DESCENDING
        else:
            order = gtk.SORT_ASCENDING
        column.set_sort_order(order)
                              
        self.__sorted_by = column
        self.__reverse_sort = reverse
        

    def append_status_column(self,
                             column_title="Status",
                             show_status_icon=1,
                             show_status_name=1):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        if show_status_icon:
            render_icon = gtk.CellRendererPixbuf()
            col.pack_start(render_icon, 0)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_STATUS_ICON)

        if show_status_name:
            render_text = gtk.CellRendererText()
            col.pack_start(render_text, 0)
            col.set_attributes(render_text,
                               markup=red_packagearray.COLUMN_STATUS)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_callback=lambda a, r: a.changed_sort_by_status(r)
                        )

        return col

    def append_action_column(self,
                             column_title="Action",
                             show_action_icon=1,
                             show_action_name=0):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        if show_action_icon:
            render_icon = gtk.CellRendererPixbuf()
            col.pack_start(render_icon, 0)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_ACTION_ICON)

        if show_action_name:
            render_text = gtk.CellRendererText()
            col.pack_start(render_text, 0)
            col.set_attributes(render_text,
                               markup=red_packagearray.COLUMN_ACTION)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_callback=lambda a, r: a.changed_sort_by_action(r)
                        )

        return col

    def append_channel_column(self,
                              column_title="Channel",
                              show_channel_icon=1,
                              show_channel_name=1):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        if show_channel_icon:
            render_icon = gtk.CellRendererPixbuf()
            col.pack_start(render_icon, 0)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_CH_ICON)

        if show_channel_name:
            render_text = gtk.CellRendererText()
            col.pack_start(render_text, 1)
            col.set_attributes(render_text,
                               text=red_packagearray.COLUMN_CH_NAME)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_callback=lambda a, r: a.changed_sort_by_channel(r),
                        )
        return col

    def append_name_column(self,
                           column_title="Package",
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
                        sort_callback=lambda a, r: a.changed_sort_by_name(r),
                        )
        return col

    def append_version_column(self, column_title="Version"):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_EVR)
        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        )
        return col

    def append_current_version_column(self, column_title="Current Version"):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_OLD_EVR)
        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        )
        return col

    def append_importance_column(self, column_title="Importance"):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_IMPORTANCE)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_callback=lambda a,r: a.changed_sort_by_importance(r),
                        )
        return col

    def append_locked_column(self):
        col = gtk.TreeViewColumn(None,
                                 gtk.CellRendererPixbuf(),
                                 pixbuf=red_packagearray.COLUMN_LOCKED_ICON)
        widget = red_pixbuf.get_widget("lock");
        widget.show()
        self.add_column(col,
                        widget=widget,
                        initially_visible=1)
        return col

    def append_size_column(self, column_title="Size"):
        render = gtk.CellRendererText()
        render.set_property("xalign", 1.0)
        col = gtk.TreeViewColumn(column_title,
                                 render,
                                 text=red_packagearray.COLUMN_SIZE)

        self.add_column(col,
                        title=column_title,
                        initially_visible=1,
                        sort_callback=lambda a,r: a.changed_sort_by_size(r),
                        )
        return col
        

        

gobject.type_register(PackageView)

gobject.signal_new("selected",
                   PackageView,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT,
                    gobject.TYPE_PYOBJECT))

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
                    gobject.TYPE_INT, # item number,
                    gobject.TYPE_INT, # button,
                    gobject.TYPE_INT, # time
                    gobject.TYPE_PYOBJECT))


