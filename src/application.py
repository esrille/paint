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
from gi.repository import Gdk, Gio, Gtk

from window import Window

import logging


logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         application_id="com.esrille.paint",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN,
                         **kwargs)
        self.cursor = None

    def do_activate(self):
        win = Window(self)
        win.show_all()

    def do_open(self, files, *hint):
        for file in files:
            win = self.is_opened(file)
            if win:
                win.present()
            else:
                win = Window(self, file=file)
                win.show_all()
            if not self.cursor:
                self.cursor = Gdk.Cursor.new_from_name(win.get_display(), "default")

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.set_accels_for_action("win.close", ["<Primary>W"])
        self.set_accels_for_action("win.closeall", ["<Primary>Q"])
        self.set_accels_for_action("win.copy", ["<Primary>C"])
        self.set_accels_for_action("win.cut", ["<Primary>X"])
        self.set_accels_for_action("win.new", ["<Primary>N"])
        self.set_accels_for_action("win.paste", ["<Primary>V"])
        self.set_accels_for_action("win.redo", ["<Shift><Primary>Z"])
        self.set_accels_for_action("win.save", ["<Primary>S"])
        self.set_accels_for_action("win.selectall", ["<Primary>A"])
        self.set_accels_for_action("win.undo", ["<Primary>Z"])

    def get_default_cursor(self):
        return self.cursor

    def is_opened(self, file):
        windows = self.get_windows()
        for window in windows:
            if window.get_file() and window.get_file().equal(file):
                return window
        return None
