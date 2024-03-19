# Copyright (c) 2020-2024 Esrille Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SUBDIRS = \
	resources\
	$(NULL)

paint_PYTHON = \
	application.py \
	main.py \
	paint.py \
	window.py \
	$(NULL)
BUILT_SOURCES = package.py
nodist_paint_PYTHON = package.py
paintdir = $(pkgdatadir)/src

bin_SCRIPTS = esrille-paint

desktop_DATA = esrille-paint.desktop
desktopdir = $(datadir)/applications

CLEANFILES = \
	esrille-paint \
	esrille-paint.desktop \
	esrille-paint.in \
	package.py \
	package.py.in \
	$(NULL)

EXTRA_DIST = \
	esrille-paint.desktop.in \
	esrille-paint.in.in \
	package.py.in.in \
	$(NULL)

package.py: package.py.in
	$(AM_V_GEN) \
	( \
		pkgdatadir=${pkgdatadir}; \
		localedir=${localedir}; \
		s=`cat $<`; \
		eval "echo \"$${s}\""; \
	) > $@

esrille-paint: esrille-paint.in
	$(AM_V_GEN) \
	( \
		pkgdatadir=${pkgdatadir}; \
		s=`cat $<`; \
		eval "echo \"$${s}\""; \
	) > $@
	chmod +x $@

esrille-paint.desktop: esrille-paint.desktop.in
	$(AM_V_GEN)$(MSGFMT) --desktop --template $< -d $(top_srcdir)/po -o $@

uninstall-hook:
	-rmdir $(paintdir)/__pycache__
	-rmdir $(paintdir)
