import types
import rcd_util

from red_gettext import _


MATCH_ANY_CATALOG = "ANY"

class Catalog:

	def __init__(self, dict):
		self.id = dict.get("id", "")
		self.name = dict.get("name", "")
		self.description = dict.get("description", "")
		self.is_visible = dict.get("is_visible", False)
		self.is_explorable = dict.get("is_explorable", False)
		self.is_default = dict.get("is_default", False)

	def is_wildcard(self):
		return self.id == "ANY"

	def has_bundle(self, needle):
		return False

	def lookup_bundle(self, name, version=0):
		pass

	def get_public_bundles(self):
		pass

def all_catalogs():
	return Catalog({"name": _("All Catalogs"),
					"id" : MATCH_ANY_CATALOG})

have_catalogs = 0
cached_catalogs = {}

def reset_catalogs():
	global have_catalogs, cached_catalogs
	have_catalogs = 0
	cached_catalogs = 0

def fetch_catalogs():
	global have_catalogs, cached_catalogs

	if have_catalogs:
		return

	catalog_list = rcd_util.server.rcd.bundles.get_catalogs()
	for c in catalog_list:
		if not c["is_hidden"]:
			cached_catalogs[c["id"]] = Catalog(c)

	have_catalogs = 1

def get_all_catalogs():
	fetch_catalogs()
	return cached_catalogs.values()

def get_catalog(id):
	try:
		assert type(id) is types.StringType
	except AssertionError:
		print id
		raise

	fetch_catalogs()
	if cached_catalogs.has_key(id):
		return cached_catalogs[id]
	return None
