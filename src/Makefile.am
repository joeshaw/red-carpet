red_carpetexecdir = $(bindir)
red_carpetexec_DATA = red-carpet

red_carpetsupportdir = $(datadir)/red-carpet
red_carpetsupport_DATA = 		\
	ximian_xmlrpclib.py		\
	red_main.py

EXTRA_DIST = $(red_carpetsupport_DATA)

install-exec-hook:
	chmod 0755 $(DESTDIR)$(red_carpetexecdir)/$(red_carpetexec_DATA)
