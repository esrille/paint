# Copyright (c) 2020 Esrille Inc.
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

resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --generate-dependencies $(srcdir)/$(PACKAGE_NAME).gresource.xml)
$(PACKAGE_NAME).gresource: $(PACKAGE_NAME).gresource.xml $(resource_files)
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir) $<

paint_DATA = $(PACKAGE_NAME).gresource
paintdir = $(pkgdatadir)/src

CLEANFILES = \
	$(PACKAGE_NAME).gresource \
	$(NULL)

EXTRA_DIST = \
	$(PACKAGE_NAME).gresource.xml \
	css/esrille-paint.css \
	gtk/menu.ui \
	icons/scalable/actions/1px-symbolic.svg \
	icons/scalable/actions/2px-symbolic.svg \
	icons/scalable/actions/4px-symbolic.svg \
	icons/scalable/actions/8px-symbolic.svg \
	icons/scalable/actions/eraser-symbolic.svg \
	icons/scalable/actions/lasso-symbolic.svg \
	icons/scalable/actions/line-symbolic.svg \
	icons/scalable/actions/oval-symbolic.svg \
	icons/scalable/actions/pencil-symbolic.svg \
	icons/scalable/actions/rectangle-symbolic.svg \
	icons/scalable/actions/selection-symbolic.svg \
	icons/scalable/actions/text-symbolic.svg \
	ui/new-dialog.glade \
	$(NULL)

