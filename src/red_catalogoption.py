import gobject
import gtk
import red_serverlistener
import string
import red_catalog
from red_gettext import _

class CatalogOption(gtk.OptionMenu, red_serverlistener.ServerListener):

	def __init__(self):
		gobject.GObject.__init__(self)
		red_serverlistener.ServerListener.__init__(self)

		self.__assemble()
		self.__last_id = None

	def __assemble(self):
		self.item_id_list = []
		menu = gtk.Menu()

		catalogs = red_catalog.get_all_catalogs()
		catalogs.sort(lambda x,y:cmp(string.lower(x.name),
									 string.lower(y.name)))

		catalogs.insert(0, red_catalog.all_catalogs ())

		for c in catalogs:
			hbox = gtk.HBox(0, 0)

			label = gtk.Label(c.name)
			hbox.pack_start(label, 0, 0, 4)

			item = gtk.MenuItem()
			item.add(hbox)
			item.show_all()

			self.item_id_list.append(c.id)

			def activate_cb(item, id, opt):
				if id != self.__last_id:
					opt.__last_id = id
					opt.emit("selected", id)
			item.connect("activate", activate_cb, c.id, self)

			menu.append(item)

		menu.show()
		self.set_menu(menu)

	def get_catalog(self):
		h = self.get_history()

		if h < 0:
			return None

		id = self.item_id_list[h]
		return red_catalog.get_catalog(id)
				
	def get_catalog_id(self):
		h = self.get_history()

		if h < 0:
			return None
		return self.item_id_list[h]

	def set_catalog_by_id(self, id):
		if not id in self.item_id_list:
			print "Unknown catalog '%s'" % id
			assert 0

		i = self.item_id_list.index(id)
		self.set_history(i)

	def catalogs_changed(self):
		id = self.get_catalog_id()
		self.__assemble()
		if id is not None and id in self.item_id_list:
			self.set_catalog_by_id(id)


gobject.type_register(CatalogOption)

gobject.signal_new("selected",
                   CatalogOption,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, ))
