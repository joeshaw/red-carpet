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
	red_activation.py			\
	red_appwindow.py			\
	red_channelmodel.py			\
	red_channeloption.py			\
	red_component.py			\
	red_console.py				\
	red_deaddaemon.py			\
	red_depcomponent.py			\
	red_depview.py				\
	red_dirselection.py			\
	red_gettext.py				\
	red_history.py				\
	red_installfiles.py			\
	red_listmodel.py			\
	red_locks.py				\
	red_main.py				\
	red_menubar.py				\
	red_mount.py				\
	red_news.py				\
	red_option.py				\
	red_packagearray.py			\
	red_packagebook.py			\
	red_packagepage.py			\
	red_packagepage_deps.py			\
	red_packagepage_info.py			\
	red_packageview.py			\
	red_pendingops.py			\
	red_pendingview.py			\
	red_pixbuf.py				\
	red_prefs.py				\
	red_search.py				\
	red_searchbar.py			\
	red_sectionoption.py			\
	red_serverinfo.py			\
	red_serverlistener.py			\
	red_serverproxy.py			\
	red_settings.py				\
	red_sidebar.py				\
	red_statusoption.py			\
	red_subscriptions.py			\
	red_summary.py				\
	red_system.py				\
	red_thrashingtreeview.py		\
	red_throbber.py				\
	red_toolbar.py				\
	red_transaction.py			\
	red_users.py				\
	ximian_xmlrpclib.py

EXTRA_DIST = $(red_carpetsupport_DATA)

install-exec-hook:
	chmod 0755 $(DESTDIR)$(red_carpetexecdir)/$(red_carpetexec_DATA)
