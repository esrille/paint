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

dist_en_DATA = \
	default.css \
	index.html \
	install.html \
	usage.html \
	color.png \
	layout.png \
	screenshot.png \
	style.png \
	tool.png \
	$(NULL)

endir = $(pkgdatadir)/help/en

EXTRA_DIST = \
	hello.png \
	index.md \
	install.md \
	Makefile.am \
	template.html \
	usage.md \
	$(NULL)

uninstall-hook:
	-rmdir $(endir)

