import string
import gobject
import gtk
import red_catalogoption

from red_gettext import _

class BundleSearchBox(gtk.VBox):

    def __init__(self,
				 installed_bundles_only=0,
				 uninstalled_bundles_only=0):
        gobject.GObject.__init__(self)

        # installed and uninstalled bundles are mutually exclusive
        assert (installed_bundles_only and uninstalled_bundles_only) == 0

        self.__installed_bundles_only = installed_bundles_only
        self.__uninstalled_bundles_only = uninstalled_bundles_only

        self.__pending_change = 0

        self.__last_query = None

        self.__assemble()

    def set_widget(self, w):
        self.__widget_box.add(w)

    def __emit(self):
        query = self.get_query()
        filter_fn = self.get_filter
        cid = self.__catalog_opt.get_catalog_id()

        if query != self.__last_query \
               or self.__status_filter != self.__last_status_filter \
               or self.__last_cid != cid:
            self.__last_query = query
            self.__last_status_filter = self.__status_filter
            self.__last_cid = cid
            self.emit("search", query, filter_fn)

        self.__pending_change = 0
        return 0

    def __changed(self, lag=0):
        
        if self.__pending_change:
            gtk.timeout_remove(self.__pending_change)
            self.__pending_change = 0
            
        if lag <= 0:
            self.__emit()
        else:
            self.__pending_change = gtk.timeout_add(lag,
                                                    lambda x: x.__emit(),
                                                    self)


    def __assemble_status_option(self):

        def uninstalled_cb():
            return ("installed", "is", "false")

        def installed_cb():
            return ("installed", "is", "true")

        def all_cb():
            return None

        status_types = (
            (_("All Bundles"),          all_cb),
            (_("Uninstalled Bundles"),  uninstalled_cb),
            (_("Installed Bundles"),    installed_cb),
            )


        menu = gtk.Menu()
        for name, filter_fn in status_types:
            mi = gtk.MenuItem(name)
            def set_cb(x, sbox, fn):
                sbox.__status_filter = fn
                sbox.__changed()
            mi.connect("activate", set_cb, self, filter_fn)
            mi.show()
            menu.append(mi)
        menu.show()

        opt = gtk.OptionMenu()
        opt.set_menu(menu)

        self.__status_filter = all_cb

        return opt

    def __assemble(self):
        top_row = gtk.HBox(0, 0)

        catalog_label = gtk.Label("")
        catalog_label.set_markup(_("Catalog:"))
        top_row.pack_start(catalog_label, expand=0, fill=0, padding=2)

        self.__catalog_opt = red_catalogoption.CatalogOption()
        self.__catalog_opt.connect("selected", lambda x,y,z: z.__changed(),
                                  self)
        top_row.pack_start(self.__catalog_opt, expand=1, fill=1, padding=0)
        top_row.show_all()

        entry_row = gtk.HBox(0, 6)
        stat_opt = self.__assemble_status_option()
        entry_row.pack_start(stat_opt, expand=0, fill=0, padding=0)

        self.__entry = gtk.Entry()
        def entry_changed_cb(e, x):
            lag = 500
            # Make the lag longer if we haven't typed much yet.
            if len(e.get_text()) < 3:
                lag *= 2
            x.__changed(lag=lag)
        self.__entry.connect("changed", entry_changed_cb, self)
        self.__entry.connect("activate",
                             lambda e, x: x.__changed(),
                             self)
        entry_row.pack_end(self.__entry, expand=1, fill=1, padding=2)
        entry_row.show_all()


        ###
        ### Create a box for our 'view' widget.
        ###

        self.__widget_box = gtk.VBox(0, 0)
        self.__widget_box.show_all()


        ###
        ### Assemble all of these pieces into our VBox.
        ###

        self.pack_start(top_row, expand=0, fill=0, padding=2)
        self.pack_start(entry_row, expand=0, fill=0, padding=2)
        self.pack_start(self.__widget_box, expand=1, fill=1, padding=2)

    def try_to_grab_focus(self):
        pass
##		FIXME
##         if self.__allow_entry:
##             w = self.__entry
##         else:
##             w = self.__ch_opt
##         gtk.idle_add(lambda x: x.grab_focus(), w)

    def get_query(self):

        query = []

        search_key = "name"
        search_match = "contains"

        search_text = self.__entry.get_text()
        if search_text:
            for t in string.split(search_text):
                query.append([search_key, search_match, t])

        query.insert(0, ["", "begin-or", ""])
        query.append(["", "end-or", ""])

        status_filter = self.__status_filter()
        if status_filter:
            query.append(status_filter)

        catalog = self.__catalog_opt.get_catalog()
        if catalog != None and not catalog.is_wildcard():
            query.append(["catalog", "is", catalog.name])

        return query

    def get_filter(self):
        def filter_fn(p,
                      n,
                      status_fn=self.__status_filter,
                      subd_dict=None):
            print "filter_fn"
            return 1

        return filter_fn


gobject.type_register(BundleSearchBox)
gobject.signal_new("search",
                   BundleSearchBox,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,  # query
                    gobject.TYPE_PYOBJECT,  # filter fn
                    ))
