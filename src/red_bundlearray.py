import gobject
import gtk
import red_listmodel
import red_serverlistener
import rcd_util
import red_pixbuf
import time
import string
import ximian_xmlrpclib

from red_gettext import _

# ListModel callbacks

def bundle(bundle):
    return bundle

def bundle_name(bundle):
    return bundle["name"]

def bundle_version(bundle):
	return bundle["version"]

def bundle_installed(bundle):
	return bundle["is_installed"]

def bundle_type(bundle):
	return bundle["type"]

def bundle_status(bundle):
	if bundle_installed(bundle):
		return _("installed")
	else:
		return _("not installed")


__installed_icon   = red_pixbuf.get_pixbuf("status-installed")
__uninstalled_icon = red_pixbuf.get_pixbuf("status-not-installed")

def bundle_status_icon(bundle):
	if bundle_installed(bundle):
		return __installed_icon
	else:
		return __uninstalled_icon

def bundle_action(bundle):
	pass

def bundle_action_icon(bundle):
	pass


# Sort functions

def sort_bundles_by_name(a, b):
    xa = a.get("_lower_name")
    if not xa:
        a["_lower_name"] = xa = string.lower(a["name"])
    xb = b.get("_lower_name")
    if not xb:
        b["_lower_name"] = xb = string.lower(b["name"])
    return cmp(xa, xb)

def sort_bundles_by_status(a, b):
	return cmp(bundle_installed(a), bundle_installed(b))

def sort_bundles_by_type(a, b):
	return cmp(bundle_type(a), bundle_type(b))

def sort_bundles_by_action(a,b):
	return cmp(a, b)

COLUMN_BUNDLE      = 0
COLUMN_NAME        = 1
COLUMN_VERSION     = 2
COLUMN_INSTALLED   = 3
COLUMN_TYPE        = 4
COLUMN_STATUS      = 5
COLUMN_STATUS_ICON = 6
COLUMN_ACTION      = 7
COLUMN_ACTION_ICON = 8

COLUMNS = (
    (COLUMN_BUNDLE,
     bundle,
     None,
     gobject.TYPE_PYOBJECT),

    (COLUMN_NAME,
     bundle_name,
     sort_bundles_by_name,
     gobject.TYPE_STRING),

	(COLUMN_VERSION,
     bundle_version,
     None,
     gobject.TYPE_STRING),

	(COLUMN_INSTALLED,
     bundle_installed,
     None,
     gobject.TYPE_BOOLEAN),

	(COLUMN_TYPE,
     bundle_type,
     sort_bundles_by_type,
     gobject.TYPE_STRING),

	(COLUMN_STATUS,
     bundle_status,
     sort_bundles_by_status,
     gobject.TYPE_STRING),

	(COLUMN_STATUS_ICON,
     bundle_status_icon,
     None,
     gtk.gdk.Pixbuf),

	(COLUMN_ACTION,
     bundle_action,
     sort_bundles_by_action,
     gobject.TYPE_STRING),

	(COLUMN_ACTION_ICON,
     bundle_action_icon,
     None,
     gtk.gdk.Pixbuf),
    )

class BundleArray(red_listmodel.ListModel):
    def __init__(self):
        red_listmodel.ListModel.__init__(self)
        self.add_columns(COLUMNS)


class BundlesFromDaemon(BundleArray, red_serverlistener.ServerListener):
    def __init__(self):
        BundleArray.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.__bundles = []
        self.pending_refresh = 0
        self.refresh_id = 0
        self.__length = 0

    # This is the method that derived classes need to implement
    def get_bundles_from_daemon(self):
        return []

    # The derived class should use this function to report the bundles
    # it received from the daemon.
    def set_bundles(self, bundles):
        self.__length = len(bundles)
        def set_bundle_cb(me, b):
            me.__bundles = b
        self.changed(set_bundle_cb, bundles)

    def refresh_start(self):
        self.busy(1)
        self.pending_refresh = 1

    def refresh_end(self):
        self.pending_refresh = 0
        gtk.idle_add(lambda x:x.busy(0), self)

    def refresh_pending(self):
        return self.pending_refresh

    def refresh(self):
        self.get_bundles_from_daemon()

    def schedule_refresh(self):
        if not self.refresh_id:
            def schedule_cb(s):
                s.refresh()
                self.refresh_id = 0
                return 0
            self.refresh_id = gtk.idle_add(schedule_cb, self)
            self.refresh_start()

    def bundles_changed(self):
        self.schedule_refresh()

    def channels_changed(self):
        self.schedule_refresh()

    def len(self):
        return self.__length

    def get(self, i):
        assert 0 <= i < self.len()
        return self.__bundles[i]

    def get_all(self):
        return self.__bundles

###############################################################################

_query_cache = {}

def _query_to_key(query):
    key = str(query)
    return key

def _get_query_from_cache(query):
    key = _query_to_key(query)
    return _query_cache.get(key)

def _cache_query_results(query, results):
    key = _query_to_key(query)
    _query_cache[key] = results

def _reset_query_cache():
    _query_cache.clear()


class BundlesFromQuery(BundlesFromDaemon):
    def __init__(self, query=None):
        BundlesFromDaemon.__init__(self)
        self.__worker = None
        self.__worker_handler_id = 0
        self.__query_msg = None
        self.__query_filter = None
        self.query = None
        if query:
            self.set_query(query)

    def set_bundles(self, bundles, quiet=0):
        if not quiet:
            if len(bundles) > 1:
                msg = _("Found %d matching bundles") % len(bundles)
            elif len(bundles) == 1:
                msg = _("Found 1 matching bundle")
            else:
                msg = _("No matching bundles found")
            self.message_push(msg, transient=1)

        BundlesFromDaemon.set_bundles(self, bundles)

    def get_bundles_from_daemon(self):

        if self.query is None:
            self.set_bundles([], quiet=1)
            self.refresh_end()
            print "query is empty"
            return

        cached = _get_query_from_cache(self.query)
        if cached is not None:
            if self.__query_filter:
                filter_fn = self.__query_filter()
                cached = filter(filter_fn, cached)
            self.set_bundles(cached)
            self.refresh_end()
            return

        server = rcd_util.get_server_proxy()
            
        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_id = 0
            self.__worker.cancel()

        def query_finished_cb(worker, array):
            array.message_pop()

            if not worker.is_cancelled():
                try:
                    bundles = worker.get_result()
                    bundles = fix_bundles(map(lambda x:x["bundle"], bundles))
                except ximian_xmlrpclib.Fault, f:
                    rcd_util.dialog_from_fault(f)
                    bundles = []
                else:
                    elapsed = time.time() - worker.t1

##                     bundles = self.filter_duplicates(packages)
##                     _cache_query_results(self.query, packages)

##                     if self.__query_filter:
##                         filter_fn = self.__query_filter()
##                         packages = filter(filter_fn, packages)

                array.set_bundles(bundles or [])
            array.refresh_end()
            array.__worker = None

        if self.__query_msg:
            self.message_push(self.__query_msg)

        self.__worker = server.rcd.bundles.search(self.query)
        self.__worker.t1 = time.time()
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         query_finished_cb,
                                                         self)

    def set_query(self, query, query_msg=None, query_filter=None):
        self.query = query
        self.__query_msg = query_msg
        self.__query_filter = query_filter

        if self.__worker and self.__worker_handler_id:
            self.__worker.disconnect(self.__worker_handler_id)
            self.__worker.cancel()
            self.__worker = None
            self.__worker_handler_id = 0

        self.schedule_refresh()

    def bundles_changed(self):
        _reset_query_cache()
        BundlesFromDaemon.bundles_changed(self)

    def channels_changed(self):
        _reset_query_cache()
        BundlesFromDaemon.channels_changed(self)

def fix_bundles(bundles):
	def fix_cb(b):
		# Make it look more like a package
		b["installed"] = b["is_installed"]
		b["name_installed"] = 0
		b["release"] = 0
		b["has_epoch"] = 0

		# Yes, this is a bundle
		b["is_bundle"] = 1

		return b

	return map(fix_cb, bundles)

