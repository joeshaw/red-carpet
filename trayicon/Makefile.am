SUBDIRS = bindings

if USERMODE
red_carpetexecdir = $(sbindir)
else
red_carpetexecdir = $(bindir)
endif

red_carpetexec_DATA = red-carpet-icon

red_carpetsupportdir = $(datadir)/red-carpet
red_carpetsupport_DATA =	\
	red_icon_main.py

EXTRA_DIST = $(red_carpetsupport_DATA)

install-exec-hook:
	chmod 0755 $(DESTDIR)$(red_carpetexecdir)/$(red_carpetexec_DATA)

