

INCLUDES = $(PYTHON_INCLUDES) $(PYGTK_CFLAGS) $(GTK_CFLAGS)

defsdir = $(datadir)/red-carpet/defs
defs_DATA = \
	red_extra.defs

EXTRA_DIST = $(defs_DATA)

pythondir=$(PYGTK_PREFIX)/lib/python2.2
pkgpythondir = $(pythondir)/gtk-2.0
pkgpyexecdir = $(pythondir)/gtk-2.0

red_extraexecdir = $(libdir)/red-carpet/red_extra
red_extraexec_DATA = __init__.py
EXTRA_DIST += __init__.py

red_extraexec_LTLIBRARIES = xxx_red_extra.la
xxx_red_extra_la_CFLAGS = $(GTK_CFLAGS)
xxx_red_extra_la_LDFLAGS = -module -avoid-version -export-symbols-regex initxxx_red_extra
xxx_red_extra_la_LIBADD = $(GTK_LIBS)
xxx_red_extra_la_SOURCES =	\
	module.c		\
	red_extra.c		\
	redlistmodel.c		\
	redlistmodel.h		\
	redlistview.c		\
	redlistview.h

CLEANFILES = red_extra.c
EXTRA_DIST += red_extra.override

red_extra.c: red_extra.defs red_extra.override
	(cd $(srcdir) \
	&& $(PYGTK_CODEGEN) \
		--register $(PYGTK_DEFSDIR)/gtk-types.defs \
		--register $(PYGTK_DEFSDIR)/gdk.defs \
		--register $(PYGTK_DEFSDIR)/gdk-types.defs \
		--override red_extra.override \
		--prefix red \
		red_extra.defs) > gen-red_extra.c \
	&& cp gen-red_extra.c red_extra.c \
	&& rm -f gen-red_extra.c

