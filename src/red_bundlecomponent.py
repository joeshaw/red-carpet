import gtk
import red_bundlearray
import red_bundleview
import red_packageview
import red_component
import red_bundlesearchbox

class BundleComponent(red_component.Component):
    def __init__(self):
        red_component.Component.__init__(self)
        self.__sbox = None

    def name(self):
        return "Bundles"

    def menu_name(self):
        return "ZENworks bundles"

    def stock(self):
        return gtk.STOCK_FIND

    def accelerator(self):
        return "<Control>z"

    def show_in_shortcuts(self):
        return 1

    def build(self):
        self.array = red_bundlearray.BundlesFromQuery()
        self.connect_array(self.array)

        self.__sbox = red_bundlesearchbox.BundleSearchBox()

        def search_cb(sbox, query, filter):
            self.array.set_query(query,
                                 query_msg="Searching for matching bundles...",
                                 query_filter=filter)
        self.__sbox.connect("search", search_cb)
        gtk.idle_add(lambda sbox: search_cb(sbox,
                                            sbox.get_query(),
                                            sbox.get_filter), self.__sbox)

        view = red_bundleview.BundleView(self.array)
        ## view = red_packageview.PackageView(self.array)
        self.connect_view(view)
        self.view = view

##         view.append_action_column()
        view.append_status_column()
        view.append_name_column()
        view.append_version_column()
        view.append_type_column()

        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        scrolled.add(view)
        scrolled.show_all()

        self.__sbox.set_widget(scrolled)

        self.__sbox.show()
        self.__sbox.try_to_grab_focus()

        return self.__sbox
