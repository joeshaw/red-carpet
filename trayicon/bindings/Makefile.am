

INCLUDES = $(PYTHON_INCLUDES) $(PYGTK_CFLAGS) $(GTK_CFLAGS) -DEGG_COMPILATION

pkgpythondir = $(pythondir)/gtk-2.0
pkgpyexecdir = $(pythondir)/gtk-2.0

red_trayexecdir = $(libdir)/red-carpet/red_tray
red_trayexec_DATA = __init__.py
EXTRA_DIST =			\
	__init__.py		\
	red_tray.defs		\
	red_tray.override

red_trayexec_LTLIBRARIES = xxx_red_tray.la
xxx_red_tray_la_CFLAGS = $(GTK_CFLAGS)
xxx_red_tray_la_LDFLAGS = -module -avoid-version -export-symbols-regex initxxx_red_tray
xxx_red_tray_la_LIBADD = $(GTK_LIBS)
xxx_red_tray_la_SOURCES =	\
	module.c		\
	red_tray.c		\
	eggtrayicon.c		\
	eggtrayicon.h	

red_tray.c: red_tray.defs red_tray.override
	(cd $(srcdir) \
	&& $(PYGTK_CODEGEN) \
		--register $(PYGTK_DEFSDIR)/gtk-types.defs \
		--register $(PYGTK_DEFSDIR)/gdk.defs \
		--register $(PYGTK_DEFSDIR)/gdk-types.defs \
		--override red_tray.override \
		--prefix redtray \
		red_tray.defs) > gen-red_tray.c \
	&& cp gen-red_tray.c red_tray.c \
	&& rm -f gen-red_tray.c

