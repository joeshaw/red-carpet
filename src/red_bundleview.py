import gobject, gtk
import red_thrashingtreeview
import red_packageview
import red_bundlearray

from red_catalog import Catalog

from red_gettext import _

class BundleView(red_packageview.PackageView):
	def __init__(self, model):
		red_packageview.PackageView.__init__(self, model)

	def append_name_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Name"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_NAME)

		self.add_column(col, title="Name", initially_visible=1,
						sort_id=red_bundlearray.COLUMN_NAME)

	def append_status_column(self,
							 column_title=_("Status"),
							 show_status_icon=1,
							 show_status_name=1):
		col = gtk.TreeViewColumn()
		col.set_title(column_title)

		if show_status_icon:
			render_icon = gtk.CellRendererPixbuf()
			expand = not show_status_name
			col.pack_start(render_icon, expand)
			col.set_attributes(render_icon,
							   pixbuf=red_bundlearray.COLUMN_STATUS_ICON)
			render_icon.set_property("xalign", 0.5)

		if show_status_name:
			render_text = gtk.CellRendererText()
			col.pack_start(render_text, 0)
			col.set_attributes(render_text,
							   markup=red_bundlearray.COLUMN_STATUS)

		self.add_column(col,
						title=column_title,
						initially_visible=1,
						sort_id=red_bundlearray.COLUMN_STATUS)
		return col

	def append_version_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Version"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_VERSION)

		self.add_column(col, title="Version", initially_visible=1)

	def append_installed_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Installed"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_INSTALLED)

		self.add_column(col, title="Installed", initially_visible=1)

	def append_type_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Type"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_TYPE)

		self.add_column(col, title="Type", initially_visible=1,
						sort_id=red_bundlearray.COLUMN_TYPE)

	

class BundleView2(red_thrashingtreeview.TreeView):
	def __init__(self, model):
		gobject.GObject.__init__(self)
		red_thrashingtreeview.TreeView.__init__(self)

		self.set_model(model)
		self.add_columns()

	def add_columns(self):
		self.add_status_column()
		self.add_name_column()
		self.add_version_column()
		self.add_type_column()

	def add_status_column(self,
						  column_title=_("Status"),
						  show_status_icon=1,
						  show_status_name=1):
		col = gtk.TreeViewColumn()
		col.set_title(column_title)

		if show_status_icon:
			render_icon = gtk.CellRendererPixbuf()
			expand = not show_status_name
			col.pack_start(render_icon, expand)
			col.set_attributes(render_icon,
							   pixbuf=red_bundlearray.COLUMN_STATUS_ICON)
			render_icon.set_property("xalign", 0.5)

		if show_status_name:
			render_text = gtk.CellRendererText()
			col.pack_start(render_text, 0)
			col.set_attributes(render_text,
							   markup=red_bundlearray.COLUMN_STATUS)

		self.add_column(col,
						title=column_title,
						initially_visible=1,
						sort_id=red_bundlearray.COLUMN_STATUS)
		return col

	def add_name_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Name"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_NAME)

		self.add_column(col, title="Name", initially_visible=1,
						sort_id=red_bundlearray.COLUMN_NAME)

	def add_version_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Version"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_VERSION)

		self.add_column(col, title="Version", initially_visible=1)

	def add_installed_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Installed"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_INSTALLED)

		self.add_column(col, title="Installed", initially_visible=1)

	def add_type_column(self):
		col = gtk.TreeViewColumn()
		col.set_title(_("Type"))

		render_text = gtk.CellRendererText()
		col.pack_start(render_text, 1)
		col.set_attributes(render_text, text=red_bundlearray.COLUMN_TYPE)

		self.add_column(col, title="Type", initially_visible=1,
						sort_id=red_bundlearray.COLUMN_TYPE)


	def set_model(self, model):
		red_thrashingtreeview.TreeView.set_model(self, model)


gobject.type_register(BundleView2)

gobject.signal_new("selected",
                   BundleView2,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

gobject.signal_new("activated",
                   BundleView2,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT,
                    gobject.TYPE_PYOBJECT,))

gobject.signal_new("popup",
                   BundleView2,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT, # button,
                    gobject.TYPE_INT, # time
                    gobject.TYPE_INT, # x coordinate
                    gobject.TYPE_INT, # y coordinate
                    )
                   )
