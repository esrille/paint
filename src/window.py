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
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, Gtk, Gdk, GObject

from paint import PaintBuffer, PaintView

import gettext
import logging
import os


_ = lambda a : gettext.dgettext(package.get_domain(), a)
logger = logging.getLogger(__name__)

DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 600


def parse_int(s):
    digits = ''
    for c in str(s).strip():
        if not c.isdigit():
            break
        digits += c
    return int(digits) if digits else None


# Treat a Gio.File as a Python file like object
class GioStream:
    def __init__(self, file, writable=False):
        self.file = file
        if not writable:
            self.stream = file.read(None)
        else:
            self.stream = file.replace(None, False, Gio.FileCreateFlags.NONE, None)

    def read(self, size):
        b = self.stream.read_bytes(size)
        if b:
            return b.get_data()
        return bytes()

    def write(self, b):
        return self.stream.write(b, None)


class PalletDialog(Gtk.Dialog):
    def __init__(self, title, icons, active):
        super().__init__(title=title, use_header_bar=True)
        box = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        box.set_layout(Gtk.ButtonBoxStyle.CENTER)
        group = None
        self.active = active
        for icon, tooltip in icons.items():
            button = Gtk.RadioButton.new_from_widget(group)
            if not group:
                group = button
            if active == icon:
                button.set_active(True)
            button.set_mode(False)
            button.set_size_request(48, 48)
            image = Gtk.Image.new_from_icon_name(icon + '-symbolic', Gtk.IconSize.BUTTON)
            button.add(image)
            context = button.get_style_context()
            context.add_class('tool_button')
            button.connect("toggled", self.on_button_toggled, icon)
            button.connect("clicked", self.on_button_clicked, icon)
            button.set_tooltip_text(tooltip)
            box.pack_start(button, False, False, 0)
            box.set_child_non_homogeneous(button, True)
        self.get_content_area().add(box)
        self.add_button(button_text="OK", response_id=Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

    def get_active(self):
        return self.active

    def on_button_toggled(self, button, name):
        if button.get_active():
            self.active = name

    def on_button_clicked(self, button, name):
        if button.get_active():
            self.response(Gtk.ResponseType.OK)


class Window(Gtk.ApplicationWindow):

    __gsignals__ = {
        'tool': (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    def __init__(self, app, file=None, buffer=None, transparent_mode=True):
        self.title = _("Paint")
        super().__init__(application=app, title=self.title)
        self.set_default_size(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        self.headerbar = Gtk.HeaderBar(title=self.title, show_close_button=True)
        self.set_titlebar(self.headerbar)

        common_buttons = {
            "edit-undo-symbolic": (self.undo_callback, _('Undo')),
            "edit-redo-symbolic": (self.redo_callback, _('Redo')),
            "edit-cut-symbolic": (self.cut_callback, _('Cut')),
            "edit-copy-symbolic": (self.copy_callback, _('Copy')),
            "edit-paste-symbolic": (self.paste_callback, _('Paste'))
        }
        for name, (method, tooltip) in common_buttons.items():
            button = Gtk.Button().new()
            icon = Gio.ThemedIcon(name=name)
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            button.add(image)
            button.connect("clicked", method)
            button.set_tooltip_text(tooltip)
            button.set_can_focus(False)
            self.headerbar.pack_start(button)

        # See https://gitlab.gnome.org/GNOME/Initiatives/-/wikis/App-Menu-Retirement
        self.menu_button = Gtk.MenuButton()
        hamburger_icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(hamburger_icon, Gtk.IconSize.BUTTON)
        self.menu_button.add(image)
        builder = Gtk.Builder()
        builder.set_translation_domain(package.get_name())
        builder.add_from_resource(package.APP_PATH + '/gtk/menu.ui')
        self.menu_button.set_menu_model(builder.get_object('app-menu'))
        self.menu_button.set_can_focus(False)
        self.headerbar.pack_end(self.menu_button)

        self.save_button = Gtk.Button.new_with_mnemonic(_("_Save"))
        self.save_button.connect("clicked", self.save_callback)
        self.save_button.set_tooltip_text(_('Save the current file'))
        self.save_button.set_can_focus(False)
        self.headerbar.pack_end(self.save_button)

        color_button = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(0, 0, 0, 1))
        color_button.connect('color-set', self.color_set_callback)
        color_button.set_tooltip_text(_('Select the current color'))
        color_button.set_can_focus(False)
        self.headerbar.pack_end(color_button)

        self.tool_button = Gtk.Button.new()
        image = Gtk.Image.new_from_icon_name('pencil-symbolic', Gtk.IconSize.BUTTON)
        self.tool_button.add(image)
        self.tool_button.connect("clicked", self.tool_set_callback)
        self.tool_button.set_tooltip_text(_('Select the current tool'))
        self.tool_button.set_can_focus(False)
        self.headerbar.pack_end(self.tool_button)

        self.style_button = Gtk.Button.new()
        image = Gtk.Image.new_from_icon_name('1px-symbolic-symbolic', Gtk.IconSize.BUTTON)
        self.style_button.add(image)
        self.style_button.connect("clicked", self.style_set_callback)
        self.style_button.set_tooltip_text(_('Select the current line width'))
        self.style_button.set_can_focus(False)
        self.headerbar.pack_end(self.style_button)

        overlay = Gtk.Overlay()
        self.add(overlay)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.buffer = None
        if file:
            buffer = self._load_file(file)
        else:
            self.file = None
        self.paintview = PaintView(buffer)
        self.buffer = self.paintview.get_buffer()
        self.buffer.set_transparent_mode(transparent_mode)
        self.buffer.connect_after("modified-changed", self.on_modified_changed)

        scrolled_window.add(self.paintview)
        overlay.add(scrolled_window)

        self.connect_after("key-press-event", self.on_key_press_event)
        self.connect_after('button-press-event', self.on_mouse_press)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        actions = {
            "menu": self.menu_callback,
            "new": self.new_callback,
            "open": self.open_callback,
            "save": self.save_callback,
            "saveas": self.save_as_callback,
            "close": self.close_callback,
            "closeall": self.close_all_callback,
            "undo": self.undo_callback,
            "redo": self.redo_callback,
            "cut": self.cut_callback,
            "copy": self.copy_callback,
            "paste": self.paste_callback,
            "selectall": self.select_all_callback,
            "font": self.font_callback,
            "background-color": self.background_color_callback,
            "help": self.help_callback,
            "about": self.about_callback,
        }
        for name, method in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", method)
            self.add_action(action)
        self.connect("delete-event", self.on_delete_event)

        action = Gio.SimpleAction.new_stateful(
            "antialias", None, GLib.Variant.new_boolean(False))
        action.connect("activate", self.antialias_callback)
        self.add_action(action)

        action = Gio.SimpleAction.new_stateful(
            "transparent-selection-mode", None, GLib.Variant.new_boolean(transparent_mode))
        action.connect("activate", self.transparent_selection_mode_callback)
        self.add_action(action)

        self.paintview.grab_focus()

    def _load_file(self, file):
        buffer = None
        if file:
            try:
                stream = GioStream(file)
                buffer = PaintBuffer.create_from_png(stream)
            except GObject.GError as e:
                file = None
                logger.error(e.message)
        self.set_file(file)
        return buffer

    def _replace_button_icon(self, button, icon):
        image = Gtk.Image.new_from_icon_name(icon + '-symbolic', Gtk.IconSize.BUTTON)
        button.remove(button.get_child())
        button.add(image)
        button.show_all()

    def _update_tool_button(self, tool):
        self._replace_button_icon(self.tool_button, tool)

    def about_callback(self, action, parameter):
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_program_name(self.title)
        dialog.set_copyright("Copyright 2020 Esrille Inc.")
        dialog.set_authors(["Esrille Inc."])
        dialog.set_documenters(["Esrille Inc."])
        dialog.set_website("http://www.esrille.com/")
        dialog.set_website_label("Esrille Inc.")
        dialog.set_logo_icon_name(package.get_name())
        dialog.set_version(package.get_version())
        # To close the dialog when "close" is clicked, e.g. on Raspberry Pi OS,
        # the "response" signal needs to be connected about_response_callback
        dialog.connect("response", self.about_response_callback)
        dialog.show()

    def about_response_callback(self, dialog, response):
        dialog.destroy()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name(_("PNG images"))
        filter_text.add_mime_type("image/png")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("Any files"))
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def antialias_callback(self, action, parameter):
        enable = not action.get_state()
        action.set_state(GLib.Variant.new_boolean(enable))
        self.paintview.set_antialias(enable)

    def background_color_callback(self, *whatever):
        dialog = Gtk.ColorChooserDialog(_("Background Color"), self)
        color = self.buffer.get_background_color()
        rgba = Gdk.RGBA(color[0], color[1], color[2])
        dialog.set_rgba(rgba)
        if dialog.run() == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            self.buffer.set_background_color((rgba.red, rgba.green, rgba.blue))
            self.paintview.queue_draw()
        dialog.destroy()

    def close_all_callback(self, *whatever):
        windows = self.get_application().get_windows()
        for window in windows:
            window.lookup_action("close").activate()

    def close_callback(self, *whatever):
        if not self.confirm_save_changes():
            self.destroy()

    def color_set_callback(self, color_button):
        color = color_button.get_color()
        self.paintview.set_color(color.red / 65535, color.green / 65535, color.blue / 65535)

    def confirm_save_changes(self):
        self.paintview.reset()
        if not self.buffer.get_modified():
            return False
        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.NONE, _("Save changes to this image?"))
        dialog.format_secondary_text(_("If you don't, changes will be lost."))
        dialog.add_button(_("Close _Without Saving"), Gtk.ResponseType.NO)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.YES)
        dialog.set_default_response(Gtk.ResponseType.YES)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.NO:
            return False
        elif response == Gtk.ResponseType.YES:
            # Close the window after saving changes
            self.close_after_save = True
            if self.file is not None:
                return self.save()
            else:
                return self.save_as()
        else:
            return True

    def copy_callback(self, *whatever):
        self.paintview.emit('copy-clipboard')

    def cut_callback(self, *whatever):
        self.paintview.emit('cut-clipboard')

    def font_callback(self, *whatever):
        dialog = Gtk.FontChooserDialog(_("Font"), self)
        dialog.props.preview_text = _("The quick brown fox jumps over the lazy dog.")
        font = self.paintview.get_font()
        dialog.set_font(font)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            font = dialog.get_font()
            if font:
                self.paintview.set_font(font)
                logger.info(font)
        dialog.destroy()

    def get_file(self):
        return self.file

    def help_callback(self, *whatever):
        url = "file://" + os.path.join(package.get_datadir(), _("help/en/index.html"))
        Gtk.show_uri_on_window(self, url, Gdk.CURRENT_TIME)

    def menu_callback(self, *whatever):
        self.menu_button.set_active(not self.menu_button.get_active())

    def new_callback(self, *whatever):
        builder = Gtk.Builder()
        builder.set_translation_domain(package.get_name())
        builder.add_from_resource(package.APP_PATH + '/ui/new-dialog.glade')
        dialog = builder.get_object('NewDialog')
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        width = builder.get_object('width')
        width.set_text('1024')
        height = builder.get_object('height')
        height.set_text('600')
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            width = parse_int(width.get_text())
            height = parse_int(height.get_text())
            buffer = PaintBuffer(width, height)
            win = Window(self.get_application(),
                         buffer=buffer,
                         transparent_mode=self.buffer.get_transparent_mode())
            win.show_all()
            win.present()
        dialog.destroy()

    def on_delete_event(self, wid, event):
        return self.confirm_save_changes()

    def on_key_press_event(self, wid, event):
        logger.info("on_key_press: '%s', %08x", Gdk.keyval_name(event.keyval), event.state)
        if event.keyval in (Gdk.KEY_E, Gdk.KEY_e):
            self.do_tool('eraser')
            return True
        elif event.keyval in (Gdk.KEY_P, Gdk.KEY_p):
            self.do_tool('pencil')
            return True
        elif event.keyval in (Gdk.KEY_S, Gdk.KEY_s):
            self.do_tool('selection')
            return True
        elif event.keyval in (Gdk.KEY_T, Gdk.KEY_t):
            self.do_tool('text')
            return True
        elif event.keyval == Gdk.KEY_Menu:
            self.tool_set_callback(self.tool_button)
            return True
        return False

    def on_modified_changed(self, buffer):
        title = self.title
        if self.file:
            title = self.file.get_basename() + " – " + title
        if self.buffer.get_modified():
            title = '*' + title
        self.set_title(title)

    def on_mouse_press(self, wid, event):
        if event.button == Gdk.BUTTON_SECONDARY:
            self.tool_set_callback(self.tool_button)

    def do_tool(self, tool):
        self.paintview.emit('tool', tool)
        tool = self.paintview.get_tool()
        self._update_tool_button(tool)

    def open_callback(self, *whatever):
        open_dialog = Gtk.FileChooserDialog(
            _("Open File"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        self.add_filters(open_dialog)
        open_dialog.set_modal(True)
        open_dialog.connect("response", self.open_response_callback)
        open_dialog.show()

    def open_response_callback(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                win = self.get_application().is_opened(file)
                if not win:
                    win = Window(self.get_application(),
                                 file=file,
                                 transparent_mode=self.buffer.get_transparent_mode())
                    win.show_all()
                win.present()
        dialog.destroy()

    def paste_callback(self, *whatever):
        self.paintview.emit('paste-clipboard')
        self._update_tool_button(self.paintview.get_tool())

    def redo_callback(self, *whatever):
        self.paintview.emit('redo')

    def save(self):
        message = ''
        try:
            stream = GioStream(self.file, True)
            self.paintview.reset()
            self.buffer.write_to_png(stream)
        except GLib.Error as e:
            message = e.message
        except Exception as e:
            message = str(e)
        else:
            return self.set_file(self.file)

        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK, _("Failed to save image."))
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        return True

    def save_as(self):
        dialog = Gtk.FileChooserDialog(
            _("Save File"), self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_modal(True)
        if self.file is not None:
            try:
                dialog.set_file(self.file)
            except GObject.GError as e:
                logger.error(e.message)
        dirty = True
        while dirty:
            dialog.hide()
            dialog.show_all()
            response = dialog.run()
            if response == Gtk.ResponseType.ACCEPT:
                self.file = dialog.get_file()
                dirty = self.save()
            else:
                break
        dialog.destroy()
        return dirty

    def save_as_callback(self, *whatever):
        self.save_as()

    def save_callback(self, *whatever):
        if self.file is not None:
            self.save()
        else:
            self.save_as()

    def select_all_callback(self, *whatever):
        self.paintview.emit('select-all', True)
        self._update_tool_button('selection')

    def set_file(self, file):
        self.file = file
        if self.buffer:
            return self.buffer.set_modified(not file)
        else:
            return False

    def style_set_callback(self, style_button):
        style_icons = {
            "1px": _("1 px"),
            "2px": _("2 px"),
            "4px": _("4 px"),
            "8px": _("8 px")
        }
        dialog = PalletDialog(_("Style"), style_icons, self.paintview.get_style())
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.connect("response", self.style_response)
        dialog.show_all()

    def style_response(self, widget, response_id):
        style = widget.get_active()
        width = int(style[0:-2])
        self.paintview.set_line_width(width)
        self._replace_button_icon(self.style_button, style)
        widget.destroy()

    def tool_set_callback(self, tool_button):
        tool_icons = {
            "lasso": _("Select a non-rectangular area"),
            "selection": _("Select a rectangular area"),
            "pencil": _("Draw lines"),
            "eraser": _("Erase where you drag"),
            "line": _("Draw straight lines"),
            "rectangle": _("Draw rectangles"),
            "oval": _("Draw ovals"),
            "text": _("Type text"),
            "floodfill": _("Fill an outlined area")
        }
        dialog = PalletDialog(_("Tool"), tool_icons, self.paintview.get_tool())
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.connect("response", self.tool_response)
        dialog.show_all()

    def tool_response(self, widget, response_id):
        tool = widget.get_active()
        self.emit('tool', tool)
        widget.destroy()

    def transparent_selection_mode_callback(self, action, parameter):
        mode = not action.get_state()
        action.set_state(GLib.Variant.new_boolean(mode))
        self.buffer.set_transparent_mode(mode)

    def undo_callback(self, *whatever):
        self.paintview.emit('undo')
