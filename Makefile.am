# require automake-1.6
AUTOMAKE_OPTIONS = 1.6

if FAST_UNMARSHALLER
UNMARSHALLER_DIR = ximian_unmarshaller
else
UNMARSHALLER_DIR =
endif

if STANDALONE
SRCDIR = 
else
SRCDIR = src
endif

SUBDIRS = $(UNMARSHALLER_DIR)	\
	  $(SRCDIR)		\
          trayicon		\
          red_extra		\
	  art			\
          help			\
	  po

#man_MANS = red-carpet.1
#EXTRA_DIST = red-carpet.1

desktopdir = $(datadir)/applications
desktop_DATA = red-carpet.desktop

kdemimedir = `kde-config --prefix`/share/applnk/.hidden
kdemime_DATA = red-carpet-mime.desktop

gnomemimedir = $(datadir)/application-registry
gnomemime_DATA = red-carpet.applications

EXTRA_DIST = red-carpet.console.in red-carpet.pam.rh7 red-carpet.pam.rh8 \
	     $(desktop_DATA) $(gnomemime_DATA) $(kdemime_DATA)

if USERMODE
consoledir = $(sysconfdir)/security/console.apps
console_file = red-carpet.console

pamdir = $(sysconfdir)/pam.d

if USERMODE_REDHAT7
pam_file = red-carpet.pam.rh7
endif

if USERMODE_REDHAT8
pam_file = red-carpet.pam.rh8
endif
endif

install-data-hook:
if USERMODE

	if test '!' -d $(DESTDIR)$(pamdir); then \
		$(mkinstalldirs) $(DESTDIR)$(pamdir); \
		chmod 0755 $(DESTDIR)$(pamdir); \
	fi

	$(INSTALL_DATA) $(srcdir)/$(pam_file) $(DESTDIR)$(pamdir)/red-carpet

	if test '!' -d $(DESTDIR)$(consoledir); then \
		$(mkinstalldirs) $(DESTDIR)$(consoledir); \
		chmod 0755 $(DESTDIR)$(consoledir); \
	fi

	$(INSTALL_DATA) $(srcdir)/$(console_file) $(DESTDIR)$(consoledir)/red-carpet

	if test '!' -d $(DESTDIR)$(bindir); then \
		$(mkinstalldirs) $(DESTDIR)$(bindir); \
		chmod 0755 $(DESTDIR)$(bindir); \
	fi

	ln -sf /usr/bin/consolehelper $(DESTDIR)$(bindir)/red-carpet

endif

uninstall-hook:
if USERMODE

	rm -f $(DESTDIR)$(pamdir)/red-carpet
	rm -f $(DESTDIR)$(consoledir)/red-carpet
	rm -f $(DESTDIR)$(bindir)/red-carpet

endif
