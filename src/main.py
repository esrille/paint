# Paint
#
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

import package

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gio, GLib, Gtk

GLib.set_prgname(package.get_name())

from application import Application

import gettext
import locale
import logging
import os
import signal
import sys

if __name__ == '__main__':
    try:
        locale.bindtextdomain(package.get_domain(), package.get_localedir())
    except Exception:
        pass
    gettext.bindtextdomain(package.get_domain(), package.get_localedir())
    logging.basicConfig(level=logging.DEBUG)

    resource = Gio.Resource.load(os.path.join(os.path.dirname(__file__), 'esrille-paint.gresource'))
    resource._register()

    style_provider = Gtk.CssProvider()
    style_provider.load_from_resource(package.APP_PATH + '/css/esrille-paint.css')
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    icon_theme = Gtk.IconTheme.get_default()
    icon_theme.add_resource_path(package.APP_PATH + '/icons')

    app = Application()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
