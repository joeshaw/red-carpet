if USERMODE
red_carpetexecdir = $(sbindir)
else
red_carpetexecdir = $(bindir)
endif

red_carpetexec_DATA = red-carpet

red_carpetsupportdir = $(datadir)/red-carpet
red_carpetsupport_DATA =	\
	rcd_util.py				\
	red_about.py				\
	red_actionbar.py			\
	red_activation.py			\
	red_appwindow.py			\
	red_bundlearray.py			\
	red_bundlecomponent.py			\
	red_bundlesearchbox.py			\
	red_bundleview.py			\
	red_catalog.py				\
	red_catalogoption.py			\
	red_channelmodel.py			\
	red_channeloption.py			\
	red_component.py			\
	red_componentbook.py			\
	red_connection.py			\
	red_console.py				\
	red_deaddaemon.py			\
	red_depcomponent.py			\
	red_depview.py				\
	red_dirselection.py			\
	red_emptypage.py			\
	red_gettext.py				\
	red_history.py				\
	red_installfiles.py			\
	red_listmodel.py			\
	red_locks.py				\
	red_main.py				\
	red_menubar.py				\
	red_mirrors.py				\
	red_mount.py				\
	red_news.py				\
	red_option.py				\
	red_packagearray.py			\
	red_packagebook.py			\
	red_packagepage.py			\
	red_packagepage_deps.py			\
	red_packagepage_info.py			\
	red_packageview.py			\
	red_patches.py				\
	red_pendingops.py			\
	red_pendingview.py			\
	red_pixbuf.py				\
	red_prefs.py				\
	red_search.py				\
	red_searchbox.py			\
	red_serverinfo.py			\
	red_serverlistener.py			\
	red_serverproxy.py			\
	red_services.py				\
	red_settings.py				\
	red_sidebar.py				\
	red_software.py				\
	red_statusbar.py			\
	red_subscriptions.py			\
	red_thrashingtreeview.py		\
	red_toolbar.py				\
	red_transaction.py			\
	red_updates.py				\
	red_users.py				\
	ximian_xmlrpclib.py

EXTRA_DIST = $(red_carpetsupport_DATA) red-carpet.in kdesu-wrapper.in

install-hook:

install-exec-hook:
if USE_KDESU
	$(INSTALL_DATA) -m 0755 $(top_builddir)/src/kdesu-wrapper $(DESTDIR)$(bindir)/red-carpet

	$(mkinstalldirs) $(DESTDIR)$(libexecdir)
	$(INSTALL_DATA) -m 0755 $(top_builddir)/src/red-carpet $(DESTDIR)$(libexecdir)/red-carpet
else
	$(INSTALL_DATA) -m 0755 $(top_builddir)/src/red-carpet $(DESTDIR)$(bindir)/red-carpet
endif
