PYTHON_INCLUDES=-I/usr/include/python2.2
PYGTK_CODEGEN=/opt/pygtk/bin/pygtk-codegen-2.0
pythondir=/opt/pygtk/lib/python2.2

INCLUDES = $(PYTHON_INCLUDES) $(PYGTK_CFLAGS) $(GTK_CFLAGS)

defsdir = $(datadir)/pygtk/2.0/defs
defs_DATA = \
	red_extra.defs

EXTRA_DIST = $(defs_DATA)

pkgpythondir = $(pythondir)/gtk-2.0
pkgpyexecdir = $(pythondir)/gtk-2.0

red_extradir = $(pkgpythondir)/red_extra
red_extra_PYTHON = __init__.py

red_extraexecdir = $(pkgpyexecdir)/red_extra

red_extraexec_LTLIBRARIES = xxx_red_extra.la
xxx_red_extra_la_CFLAGS = $(GTK_CFLAGS)
xxx_red_extra_la_LDFLAGS = -module -avoid-version -export-symbols-regex initxxx_red_extra
xxx_red_extra_la_LIBADD = $(GTK_LIBS)
xxx_red_extra_la_SOURCES =		\
	module.c		\
	red_extra.c		\
	redlistmodel.c	\
	redlistmodel.h

CLEANFILES = red_extra.c
EXTRA_DIST += red_extra.override

red_extra.c: red_extra.defs red_extra.override
	(cd $(srcdir) \
	&& $(PYGTK_CODEGEN) \
		--register $(PYGTK_DEFSDIR)/gtk-types.defs \
		--override red_extra.override \
		--prefix red \
		red_extra.defs) > gen-red_extra.c \
	&& cp gen-red_extra.c red_extra.c \
	&& rm -f gen-red_extra.c

