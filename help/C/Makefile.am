docname = red-carpet
lang = C
omffile = red-carpet-C.omf
entities = fdl-appendix.xml
include $(top_srcdir)/help/xmldocs.make
dist-hook: app-dist-hook

DOCBOOK_XSL=$(top_srcdir)/help/docbook/html/docbook.xsl

CLEANFILES += html_stamp $(omffile).out red-carpet.html

html_stamp: red-carpet.xml
	xsltproc $(DOCBOOK_XSL) $(top_srcdir)/help/$(lang)/red-carpet.xml > red-carpet.html
	touch html_stamp

all: html_stamp

install-data-hook: html_stamp
	$(INSTALL_DATA) red-carpet.html $(DESTDIR)$(docdir)

uninstall-hook:
	rm -f $(DESTDIR)$(docdir)/red-carpet.html