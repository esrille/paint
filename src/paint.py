# Paint
#
# Copyright (c) 2020-2022 Esrille Inc.
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
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, GObject, Pango, PangoCairo

import cairo
import copy
import cv2
import gettext
import logging
import math
import numpy
import time


_ = lambda a: gettext.dgettext(package.get_domain(), a)
logger = logging.getLogger(__name__)

DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 600
TEXT_MARGIN = 8
RESIZE_BORDER = 16
MARQUEE_COLOR = (0.8, 0.6, 0.1, 1)


class Tool:
    def __init__(self, view):
        self.antialias = True
        self.color = (0, 0, 0, 1)
        self.line_width = 1

    @classmethod
    def get_name(self):
        return 'tool'

    def constrain(self, width, height, hv=False):
        w = abs(width)
        h = abs(height)
        if 2 * h < w and hv:
            height = 0
        elif h < w:
            width = h if 0 <= width else -h
        elif 2 * w < h and hv:
            width = 0
        elif w < h:
            height = w if 0 <= height else -w
        return width, height

    def get_cursor(self, view, x, y, pressed):
        return Gdk.CursorType.CROSS

    def has_animation(self):
        return self.has_selection()

    def has_selection(self):
        return False

    def in_selection(self, cr, s, t):
        return False

    def is_selection(self):
        return False

    def is_text(self):
        return False

    def on_commit(self, im, str):
        return False

    def on_delete_surrounding(self, im, offset, n_chars):
        return False

    def on_draw(self, cr, buffer):
        cr.set_source_rgba(*self.color)
        cr.set_line_width(self.line_width)
        cr.set_line_cap(cairo.LineCap.ROUND)
        cr.set_line_join(cairo.LineJoin.ROUND)
        if not self.antialias:
            cr.set_antialias(cairo.Antialias.NONE)

    def on_key_press(self, view, im, event):
        return False

    def on_key_release(self, view, im, event):
        return False

    def on_mouse_move(self, view, event, x, y):
        return False

    def on_mouse_press(self, view, event, x, y):
        return False

    def on_mouse_release(self, view, event, x, y):
        return False

    def on_preedit_changed(self, im):
        return False

    def on_preedit_end(self, im):
        return False

    def on_preedit_start(self, im):
        return False

    def on_retrieve_surrounding(self, im):
        return True

    def reflow(self, view):
        pass

    def set_antialias(self, enable):
        self.antialias = enable

    def set_color(self, red, green, blue, alpha=1):
        self.color = (red, green, blue, alpha)

    def set_cursor_location(self, im, dx, dy):
        pass

    def set_font(self, font):
        pass

    def set_line_width(self, width):
        self.line_width = width


class Pencil(Tool):

    def __init__(self, view):
        super().__init__(view)
        self.stroke = []
        self.control_points = []

    @classmethod
    def get_name(cls):
        return 'pencil'

    def get_cursor(self, view, x, y, pressed):
        return Gdk.CursorType.PENCIL

    def on_draw(self, cr, buffer):
        length = len(self.stroke)
        if length <= 0:
            return
        super().on_draw(cr, buffer)
        cr.new_path()
        if length < 3:
            for x, y in self.stroke:
                cr.line_to(x, y)
            if length == 1:
                cr.close_path()     # Draw a point
        else:
            cr.move_to(self.stroke[0][0], self.stroke[0][1])
            # quadratic curve
            cr.curve_to(self.control_points[0][0], self.control_points[0][1],
                        self.control_points[0][0], self.control_points[0][1],
                        self.stroke[1][0], self.stroke[1][1])

            for i in range(2, length - 1):
                # cubic curve
                cr.curve_to(self.control_points[i * 2 - 3][0], self.control_points[i * 2 - 3][1],
                            self.control_points[i * 2 - 2][0], self.control_points[i * 2 - 2][1],
                            self.stroke[i][0], self.stroke[i][1])

            # quadratic curve
            cr.curve_to(self.control_points[-1][0], self.control_points[-1][1],
                        self.control_points[-1][0], self.control_points[-1][1],
                        self.stroke[-1][0], self.stroke[-1][1])
        cr.stroke()

    def on_mouse_move(self, view, event, x, y):
        if self.stroke[-1][0] == x and self.stroke[-1][1] == y:
            return
        self.stroke.append((x, y))
        if len(self.stroke) <= 2:
            return
        # Calculate control points
        dx = (self.stroke[-1][0] - self.stroke[-3][0]) / 6
        dy = (self.stroke[-1][1] - self.stroke[-3][1]) / 6
        self.control_points.append((self.stroke[-2][0] - dx, self.stroke[-2][1] - dy))
        self.control_points.append((self.stroke[-2][0] + dx, self.stroke[-2][1] + dy))

    def on_mouse_press(self, view, event, x, y):
        self.stroke.append((x, y))


class Eraser(Pencil):
    def __init__(self, view):
        super().__init__(view)

    @classmethod
    def get_name(cls):
        return 'eraser'

    def get_cursor(self, view, x, y, pressed):
        return Gdk.CursorType.CROSS

    def on_draw(self, cr, buffer):
        super().on_draw(cr, buffer)
        cr.set_operator(cairo.Operator.SOURCE)
        buffer.set_source_rgba(cr)
        cr.set_line_width(8 * self.line_width)
        cr.set_line_cap(cairo.LineCap.SQUARE)
        cr.new_path()
        for x, y in self.stroke:
            cr.line_to(x, y)
        cr.stroke()
        cr.set_operator(cairo.Operator.OVER)


class Shape(Tool):
    def __init__(self, view):
        super().__init__(view)
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

    @classmethod
    def get_name(cls):
        return 'shape'

    def on_draw(self, cr, buffer):
        super().on_draw(cr, buffer)

    def on_mouse_move(self, view, event, x, y):
        self.width = x - self.x
        self.height = y - self.y

    def on_mouse_press(self, view, event, x, y):
        self.x = x
        self.y = y
        self.width = self.height = 0

    def on_mouse_release(self, view, event, x, y):
        pass


class Line(Shape):
    def __init__(self, view):
        super().__init__(view)

    @classmethod
    def get_name(cls):
        return 'line'

    def on_draw(self, cr, buffer):
        if not self.width and not self.height:
            return
        super().on_draw(cr, buffer)
        cr.new_path()
        cr.move_to(self.x, self.y)
        cr.line_to(self.x + self.width, self.y + self.height)
        cr.stroke()

    def on_mouse_move(self, view, event, x, y):
        super().on_mouse_move(view, event, x, y)
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            self.width, self.height = self.constrain(self.width, self.height, hv=True)


class Rectangle(Shape):
    def __init__(self, view):
        super().__init__(view)

    @classmethod
    def get_name(cls):
        return 'rectangle'

    def on_draw(self, cr, buffer):
        if not self.width or not self.height:
            return
        super().on_draw(cr, buffer)
        cr.new_path()
        cr.rectangle(self.x, self.y, self.width, self.height)
        cr.stroke()

    def on_mouse_move(self, view, event, x, y):
        super().on_mouse_move(view, event, x, y)
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            self.width, self.height = self.constrain(self.width, self.height)


class Oval(Shape):
    def __init__(self, view):
        super().__init__(view)

    @classmethod
    def get_name(cls):
        return 'oval'

    def on_draw(self, cr, buffer):
        if not self.width or not self.height:
            return
        super().on_draw(cr, buffer)
        cr.new_path()
        w = abs(self.width) / 2
        h = abs(self.height) / 2
        r = min(w, h)
        cr.save()
        cr.translate(self.x + self.width / 2, self.y + self.height / 2)
        cr.scale(w / r, h / r)
        cr.arc(0, 0, r, 0, 2 * math.pi)
        cr.restore()
        cr.stroke()

    def on_mouse_move(self, view, event, x, y):
        super().on_mouse_move(view, event, x, y)
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            self.width, self.height = self.constrain(self.width, self.height)


class SelectionBase(Tool):
    def __init__(self, view):
        super().__init__(view)
        self.closed = False
        self.cut = False
        # start and end points of the source rectangle and the destination
        # rectangle.
        self.src = [[0, 0], [0, 0]]
        self.dst = [[0, 0], [0, 0]]
        # for dragging
        self.dragging = False
        self.anchor = [0, 0]
        self.cursor = Gdk.CursorType.CROSS

    @classmethod
    def get_name(cls):
        return 'selecttion-base'

    def _create_path(self, cr):
        pass

    def _transform(self, cr):
        # To understand the transforms, read them bottom to top
        cr.translate(self.dst[0][0], self.dst[0][1])
        scale = self.get_scale()
        cr.scale(scale[0], scale[1])
        cr.translate(-self.src[0][0], -self.src[0][1])

    def _set_marquee(self, cr):
        offset = 20 - int(time.time() * 25) % 20
        cr.set_dash((10, 10), offset)
        if (1, 13) <= cairo.version_info:
            cr.set_operator(cairo.Operator.DIFFERENCE)
            cr.set_source_rgba(*MARQUEE_COLOR)

    def copy_clipboard(self, clipboard: Gtk.Clipboard, buffer):
        surface = buffer.get_surface()
        cr = cairo.Context(surface)
        self._create_path(cr)
        left, top, right, bottom = cr.path_extents()
        left = math.floor(left)
        top = math.floor(top)
        right = math.ceil(right)
        bottom = math.ceil(bottom)
        width = right - left
        height = bottom - top
        assert 0 <= width and 0 <= height
        if width <= 0 or height <= 0:
            return
        copy = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(copy)
        cr.translate(-left, -top)
        self._create_path(cr)
        cr.clip()
        cr.set_source_surface(surface, 0, 0)
        cr.paint()
        pixbuf = Gdk.pixbuf_get_from_surface(copy, 0, 0, width, height)
        clipboard.set_image(pixbuf)

    def cut_clipboard(self, clipboard: Gtk.Clipboard, buffer):
        self.copy_clipboard(clipboard, buffer)
        self.cut = True
        return True

    def get_cursor(self, view, x, y, pressed):
        if self.dragging:
            return self.cursor
        if self.has_selection():
            cr = cairo.Context(view.buffer.get_surface())
            if self.in_selection(cr, x, y):
                return self.in_border(x, y, pressed)
        return Gdk.CursorType.CROSS

    def get_offset(self):
        dx = self.dst[0][0] - self.src[0][0]
        dy = self.dst[0][1] - self.src[0][1]
        return dx, dy

    def get_scale(self):
        src_wh = self.get_size(self.src)
        dst_wh = self.get_size(self.dst)
        if src_wh[0] == 0 or src_wh[1] == 0:
            return (0, 0)
        return (dst_wh[0] / src_wh[0], dst_wh[1] / src_wh[1])

    def get_size(self, r):
        w = r[1][0] - r[0][0]
        h = r[1][1] - r[0][1]
        return (w, h)

    def has_selection(self):
        return self.closed

    def in_border(self, s, t, pressed):
        x, y = self.dst[0]
        w, h = self.get_size(self.dst)
        if w < 3 * RESIZE_BORDER:
            ww = 3 * RESIZE_BORDER
            x -= round((ww - w) / 2)
            w = ww
        if h < 3 * RESIZE_BORDER:
            hh = 3 * RESIZE_BORDER
            y -= round((hh - h) / 2)
            h = hh
        s -= x
        t -= y
        if s < 0 or t < 0 or w < s or h < t:
            return Gdk.CursorType.CROSS
        if t < RESIZE_BORDER:
            if s < RESIZE_BORDER:
                return Gdk.CursorType.TOP_LEFT_CORNER
            if w - RESIZE_BORDER <= s:
                return Gdk.CursorType.TOP_RIGHT_CORNER
            else:
                return Gdk.CursorType.TOP_SIDE
        if h - RESIZE_BORDER <= t:
            if s < RESIZE_BORDER:
                return Gdk.CursorType.BOTTOM_LEFT_CORNER
            if w - RESIZE_BORDER <= s:
                return Gdk.CursorType.BOTTOM_RIGHT_CORNER
            else:
                return Gdk.CursorType.BOTTOM_SIDE
        if s < RESIZE_BORDER:
            return Gdk.CursorType.LEFT_SIDE
        if w - RESIZE_BORDER <= s:
            return Gdk.CursorType.RIGHT_SIDE
        elif pressed:
            return Gdk.CursorType.FLEUR
        else:
            return Gdk.CursorType.HAND1

    def in_selection(self, cr, s, t):
        if not self.has_selection():
            return False
        super().on_draw(cr, None)
        cr.save()
        self._transform(cr)
        self._create_path(cr)
        cr.restore()
        result = cr.in_fill(s, t)
        return result

    def is_selection(self):
        return True

    def on_draw(self, cr, buffer):
        super().on_draw(cr, buffer)
        cr.set_line_width(1)
        self._create_path(cr)
        if not self.has_selection():
            # Draw outline
            self._set_marquee(cr)
            cr.stroke()
            return
        # Clear selection
        cr.set_operator(cairo.Operator.SOURCE)
        buffer.set_source_rgba(cr)
        cr.fill()
        cr.set_operator(cairo.Operator.OVER)
        if self.cut:
            return
        cr.set_source_rgba(*self.color)
        cr.save()
        self._transform(cr)
        self._create_path(cr)
        cr.clip()
        cr.set_source_surface(buffer.get_surface(), 0, 0)
        cr.paint()
        cr.restore()
        # Draw outline
        if not buffer.appending:
            cr.save()
            self._transform(cr)
            self._create_path(cr)
            cr.restore()
            self._set_marquee(cr)
            cr.stroke()

    def on_key_press(self, view, im, event):
        if not self.has_selection():
            return False
        if event.keyval == Gdk.KEY_Escape:
            view.reset()
            return True
        return False

    def on_mouse_move(self, view, event, x, y):
        if not self.dragging:
            return True
        dx = x - self.anchor[0]
        dy = y - self.anchor[1]
        # Drag
        if self.cursor == Gdk.CursorType.FLEUR:
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                self.offset = self.constrain(dx, dy, hv=True)
            self.dst[0][0] = self.base[0][0] + dx
            self.dst[0][1] = self.base[0][1] + dy
            self.dst[1][0] = self.base[1][0] + dx
            self.dst[1][1] = self.base[1][1] + dy
            return False
        # Stretch the selection
        cursor = self.cursor
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            w, h = self.get_size(self.base)
            cursor = {
                Gdk.CursorType.TOP_SIDE: Gdk.CursorType.TOP_RIGHT_CORNER,
                Gdk.CursorType.RIGHT_SIDE: Gdk.CursorType.BOTTOM_RIGHT_CORNER,
                Gdk.CursorType.BOTTOM_SIDE: Gdk.CursorType.BOTTOM_RIGHT_CORNER,
                Gdk.CursorType.LEFT_SIDE: Gdk.CursorType.BOTTOM_LEFT_CORNER,
            }.get(cursor, cursor)
            if cursor in (Gdk.CursorType.TOP_LEFT_CORNER, Gdk.CursorType.BOTTOM_RIGHT_CORNER):
                if abs(dx) < abs(dy):
                    dx = round(w * (dy / h))
                else:
                    dy = round(h * (dx / w))
            elif cursor in (Gdk.CursorType.TOP_RIGHT_CORNER, Gdk.CursorType.BOTTOM_LEFT_CORNER):
                if abs(dx) < abs(dy):
                    dx = -round(w * (dy / h))
                else:
                    dy = -round(h * (dx / w))
        if cursor == Gdk.CursorType.TOP_LEFT_CORNER:
            self.dst[0][0] = min(self.base[0][0] + dx, self.base[1][0] - 1)
            self.dst[0][1] = min(self.base[0][1] + dy, self.base[1][1] - 1)
        elif cursor == Gdk.CursorType.TOP_RIGHT_CORNER:
            self.dst[1][0] = max(self.base[1][0] + dx, self.base[0][0] + 1)
            self.dst[0][1] = min(self.base[0][1] + dy, self.base[1][1] - 1)
        elif cursor == Gdk.CursorType.TOP_SIDE:
            self.dst[0][1] = min(self.base[0][1] + dy, self.base[1][1] - 1)
        elif cursor == Gdk.CursorType.BOTTOM_LEFT_CORNER:
            self.dst[0][0] = min(self.base[0][0] + dx, self.base[1][0] - 1)
            self.dst[1][1] = max(self.base[1][1] + dy, self.base[0][1] + 1)
        elif cursor == Gdk.CursorType.BOTTOM_RIGHT_CORNER:
            self.dst[1][0] = max(self.base[1][0] + dx, self.base[0][0] + 1)
            self.dst[1][1] = max(self.base[1][1] + dy, self.base[0][1] + 1)
        elif cursor == Gdk.CursorType.BOTTOM_SIDE:
            self.dst[1][1] = max(self.base[1][1] + dy, self.base[0][1] + 1)
        elif cursor == Gdk.CursorType.LEFT_SIDE:
            self.dst[0][0] = min(self.base[0][0] + dx, self.base[1][0] - 1)
        elif cursor == Gdk.CursorType.RIGHT_SIDE:
            self.dst[1][0] = max(self.base[1][0] + dx, self.base[0][0] + 1)
        return False

    def on_mouse_press(self, view, event, x, y):
        cr = cairo.Context(view.buffer.get_surface())
        if self.in_selection(cr, x, y):
            self.dragging = True
            self.anchor = [x, y]
            self.cursor = self.in_border(x, y, True)
            self.base = copy.deepcopy(self.dst)
            return False
        return True

    def on_mouse_release(self, view, event, x, y):
        if self.dragging:
            self.dragging = False
            self.base = None
            return False
        return True


class Lasso(SelectionBase):
    def __init__(self, view):
        super().__init__(view)
        self.stroke = []

    def _create_path(self, cr):
        cr.new_path()
        for x, y in self.stroke:
            cr.line_to(x, y)
        if self.has_selection():
            cr.close_path()

    @classmethod
    def get_name(cls):
        return 'lasso'

    def on_mouse_move(self, view, event, x, y):
        if super().on_mouse_move(view, event, x, y):
            if x < self.src[0][0]:
                self.src[0][0] = x
            elif self.src[1][0] < x:
                self.src[1][0] = x
            if y < self.src[0][1]:
                self.src[0][1] = y
            elif self.src[1][1] < y:
                self.src[1][1] = y
            self.stroke.append((x, y))

    def on_mouse_press(self, view, event, x, y):
        if super().on_mouse_press(view, event, x, y):
            self.stroke = []
            self.closed = False
            self.src[0][0] = self.src[1][0] = x
            self.src[0][1] = self.src[1][1] = y
            self.stroke.append((x, y))

    def on_mouse_release(self, view, event, x, y):
        if super().on_mouse_release(view, event, x, y):
            w, h = self.get_size(self.src)
            if 0 < w and 0 < h:
                self.dst = copy.deepcopy(self.src)
                self.closed = True
            else:
                self.stroke = []


# Rectangle Selection Tool
class Selection(SelectionBase):
    def __init__(self, view):
        super().__init__(view)

    def _create_path(self, cr):
        cr.new_path()
        w, h = self.get_size(self.src)
        cr.rectangle(self.src[0][0], self.src[0][1], w, h)

    @classmethod
    def get_name(cls):
        return 'selection'

    def on_mouse_move(self, view, event, x, y):
        if super().on_mouse_move(view, event, x, y):
            self.src[1][0] = x
            self.src[1][1] = y
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                w, h = self.get_size(self.src)
                w, h = self.constrain(w, h, hv=True)
                self.src[1][0] = self.src[0][0] + w
                self.src[1][1] = self.src[0][1] + h

    def on_mouse_press(self, view, event, x, y):
        if super().on_mouse_press(view, event, x, y):
            self.src[0][0] = self.src[1][0] = x
            self.src[0][1] = self.src[1][1] = y

    def on_mouse_release(self, view, event, x, y):
        if super().on_mouse_release(view, event, x, y):
            w, h = self.get_size(self.src)
            if w < 0:
                self.src[0][0], self.src[1][0] = self.src[1][0], self.src[0][0]
                w = -w
            if h < 0:
                self.src[0][1], self.src[1][1] = self.src[1][1], self.src[0][1]
                h = -h
            if 0 < w and 0 < h:
                self.dst = copy.deepcopy(self.src)
                self.closed = True

    def select(self, x, y, width, height):
        self.src[0][0] = self.src[1][0] = x
        self.src[0][1] = self.src[1][1] = y
        self.src[1][0] += width
        self.src[1][1] += height
        if 0 < width and 0 < height:
            self.dst = copy.deepcopy(self.src)
            self.closed = True


class Text(SelectionBase):
    def __init__(self, view):
        super().__init__(view)
        self.text = None    # None while x, y has not been assigned any value
        self.current = 0    # cursor position in text
        self.font = view.get_font()
        self.preedit = ('', None, 0)
        self.caret = Gdk.Rectangle()
        self.ink = [0, 0]

    def _create_path(self, cr):
        cr.new_path()
        w, h = self.get_size(self.src)
        cr.rectangle(self.src[0][0] - TEXT_MARGIN / 2,
                     self.src[0][1] - TEXT_MARGIN / 2,
                     w + TEXT_MARGIN, h + TEXT_MARGIN)

    def _draw_caret(self, cr, layout, text, current):
        offset = int(time.time() * 10) % 10
        if offset < 5:
            return
        st, we = layout.get_cursor_pos(len(text[:current].encode()))
        self.caret.x = st.x / Pango.SCALE - 1
        self.caret.y = st.y / Pango.SCALE
        self.caret.width = st.width / Pango.SCALE + 2
        self.caret.height = st.height / Pango.SCALE
        if (1, 13) <= cairo.version_info:
            cr.set_operator(cairo.Operator.DIFFERENCE)
            cr.set_source_rgb(1, 1, 1)
        cr.rectangle(self.caret.x, self.caret.y, self.caret.width, self.caret.height)
        cr.fill()

    def _has_preedit(self):
        return self.preedit[0]

    def _layout_text(self, cr, buffer):
        attr_list = Pango.AttrList().new()
        text = self.text
        current = self.current
        if self._has_preedit():
            text = text[:current] + self.preedit[0] + text[current:]
            attr_list.splice(self.preedit[1], len(text[:current].encode()), len(self.preedit[0].encode()))
            current += self.preedit[2]
        layout = PangoCairo.create_layout(cr)
        desc = Pango.font_description_from_string(self.font)
        layout.set_font_description(desc)
        layout.set_text(text, -1)
        layout.set_attributes(attr_list)
        PangoCairo.update_layout(cr, layout)
        return layout, text, current

    @classmethod
    def get_name(cls):
        return 'text'

    def copy_clipboard(self, clipboard: Gtk.Clipboard, buffer):
        clipboard.set_text(self.text, -1)

    def cut_clipboard(self, clipboard: Gtk.Clipboard, buffer):
        self.copy_clipboard(clipboard, buffer)
        self.text = ''
        self.current = 0
        return False

    def get_cursor(self, view, x, y, pressed):
        cursor = super().get_cursor(view, x, y, pressed)
        if cursor == Gdk.CursorType.CROSS:
            return Gdk.CursorType.XTERM
        return cursor

    def has_animation(self):
        return self.text is not None

    def has_selection(self):
        return self.text is not None and 0 < len(self.text)

    def insert_text(self, text):
        if self.text is None:
            self.text = text
            self.current = len(text)
        else:
            self.text = self.text[:self.current] + text + self.text[self.current:]
            self.current += len(text)

    def is_text(self):
        return True

    def on_commit(self, im, text):
        if self.text is None:
            return False
        self.insert_text(text)
        return True

    def on_delete_surrounding(self, im, offset, n_chars):
        if self.text is None:
            return False
        begin = self.current + offset
        if begin < 0:
            return False
        end = begin + n_chars
        if len(self.text) < end:
            return False
        self.text = self.text[:begin] + self.text[end:]
        if end <= self.current:
            self.current -= n_chars
        elif begin <= self.current:
            self.current = begin
        return True

    def on_draw(self, cr, buffer):
        if self.text is None:
            return
        cr.set_source_rgba(*self.color)
        cr.save()

        # PangoCairo layout must be created before applying cairo.Context.scale(),
        # which might be a bug in PangoCairo.
        layout, text, current = self._layout_text(cr, buffer)

        # To understand the transforms, read them bottom to top
        cr.translate(self.dst[0][0], self.dst[0][1])
        scale = self.get_scale()
        cr.scale(scale[0], scale[1])
        PangoCairo.show_layout(cr, layout)
        if not buffer.appending:
            self._draw_caret(cr, layout, text, current)
        else:
            self.preedit = ('', None, 0)

        cr.restore()

    def on_key_press(self, view, im, event):
        if self.text is None:
            return False
        if im.filter_keypress(event):
            return True
        if event.keyval == Gdk.KEY_BackSpace:
            if 0 < self.current:
                self.text = self.text[:self.current-1] + self.text[self.current:]
                self.current -= 1
                return True
        elif event.keyval == Gdk.KEY_Delete:
            if self.current < len(self.text):
                self.text = self.text[:self.current] + self.text[self.current+1:]
                return True
        elif event.keyval == Gdk.KEY_Left:
            if 0 < self.current:
                self.current -= 1
                return True
        elif event.keyval == Gdk.KEY_Right:
            if self.current < len(self.text):
                self.current += 1
                return True
        elif event.keyval == Gdk.KEY_Home:
            if 0 < self.current:
                self.current = 0
                return True
        elif event.keyval == Gdk.KEY_End:
            if self.current < len(self.text):
                self.current = len(self.text)
                return True
        elif event.keyval == Gdk.KEY_Return:
            self.text = self.text[:self.current] + '\n' + self.text[self.current:]
            self.current += 1
            return True
        elif event.keyval == Gdk.KEY_Escape:
            view.reset()
            return True
        return False

    def on_key_release(self, view, im, event):
        if self.text is None:
            return False
        if im.filter_keypress(event):
            return True
        return False

    def on_mouse_press(self, view, event, x, y):
        if super().on_mouse_press(view, event, x, y):
            if not self.text:
                self.text = ''
                self.dst[0][0] = self.src[0][0] = x
                self.dst[0][1] = self.src[0][1] = y

    def on_preedit_changed(self, im):
        if self.text is None:
            return False
        self.preedit = im.get_preedit_string()
        return True

    def on_preedit_end(self, im):
        if self.text is None:
            return False
        self.preedit = im.get_preedit_string()
        return True

    def on_preedit_start(self, im):
        if self.text is None:
            return False
        self.preedit = im.get_preedit_string()
        return True

    def on_retrieve_surrounding(self, im):
        if self.text is None:
            return False
        im.set_surrounding(self.text, len(self.text.encode()), len(self.text[:self.current].encode()))
        return True

    def reflow(self, view):
        if not self.has_selection():
            return
        cr = cairo.Context(view.buffer.get_surface())
        layout, text, current = self._layout_text(cr, view.buffer)
        rects = layout.get_pixel_extents()
        width = rects[0].width
        if width == 0:
            width = 1
        scale = self.get_scale()
        self.ink = [rects[0].x, rects[0].y]
        self.src[1][0] = self.src[0][0] + self.ink[0] + width
        self.src[1][1] = self.src[0][1] + self.ink[1] + rects[0].height
        if scale[0] == 0 or scale[1] == 0:
            self.dst = copy.deepcopy(self.src)
        else:
            self.dst[1][0] = self.dst[0][0] + (self.ink[0] + width) * scale[0]
            self.dst[1][1] = self.dst[0][1] + (self.ink[1] + rects[0].height) * scale[1]

    def set_cursor_location(self, im, dx, dy):
        if self.text is not None:
            caret = Gdk.Rectangle()
            caret.x = self.caret.x
            caret.y = self.caret.y
            caret.width = self.caret.width
            caret.height = self.caret.height
            scale = self.get_scale()
            caret.x *= scale[0]
            caret.y *= scale[1]
            caret.width *= scale[0]
            caret.height *= scale[1]
            caret.x += self.dst[0][0] - dx
            caret.y += self.dst[0][1] - dy
            im.set_cursor_location(caret)

    def set_font(self, font):
        self.font = font


class Paste(SelectionBase):
    def __init__(self, view, pixbuf: GdkPixbuf.Pixbuf):
        super().__init__(view)
        self.source = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 0, None)
        self.closed = True
        self.src[1][0] = self.source.get_width()
        self.src[1][1] = self.source.get_height()
        self.dst = copy.deepcopy(self.src)

    def _create_path(self, cr):
        cr.new_path()
        cr.rectangle(0, 0, self.source.get_width(), self.source.get_height())

    @classmethod
    def get_name(cls):
        return 'paste'

    def on_draw(self, cr, buffer):
        cr.set_line_width(1)
        cr.set_source_rgba(*self.color)
        cr.save()
        self._transform(cr)
        self._create_path(cr)
        cr.clip()
        cr.set_source_surface(self.source, 0, 0)
        cr.paint()
        cr.restore()
        # Draw outline
        if not buffer.appending:
            cr.save()
            self._transform(cr)
            self._create_path(cr)
            cr.restore()
            self._set_marquee(cr)
            cr.stroke()


class FloodFill(Tool):
    def __init__(self, view):
        super().__init__(view)
        self.x = 0
        self.y = 0
        self.clicked = False

    @classmethod
    def get_name(cls):
        return 'floodfill'

    def on_draw(self, cr, buffer):
        if not self.clicked:
            return
        surface = buffer.make_opaque(buffer.get_surface())
        buf = surface.get_data()
        array = numpy.ndarray(shape=(surface.get_height(), surface.get_width(), 4),
                              dtype=numpy.uint8, buffer=buf)
        array = cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)
        color = [int(255 * i) for i in self.color[:3]]
        cv2.floodFill(array, None, (self.x, self.y), color)
        array = cv2.cvtColor(array, cv2.COLOR_BGR2RGBA)
        surface = cairo.ImageSurface.create_for_data(array, cairo.FORMAT_ARGB32,
                                                     surface.get_width(), surface.get_height())
        buffer.set_surface(surface)

    def on_mouse_release(self, view, event, x, y):
        self.x = x
        self.y = y
        self.clicked = True


class PaintBuffer(GObject.Object):

    __gsignals__ = {
        'modified-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'redo': (GObject.SIGNAL_RUN_LAST, None, ()),
        'undo': (GObject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, fobj=None):
        super().__init__()
        self.background_color = (1, 1, 1)
        self.transparent_mode = False
        if fobj:
            self.surface = cairo.ImageSurface.create_from_png(fobj)
        else:
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            cr = cairo.Context(self.surface)
            cr.set_source_rgba(*self.background_color, 1)
            cr.paint()
        self.original = self._copy_surface(self.surface)
        self.undo = []
        self.redo = []
        self.appending = False  # True during append()

    @classmethod
    def create_from_png(cls, fobj):
        return cls(None, None, fobj)

    def _copy_surface(self, surface):
        copy = surface.create_similar_image(cairo.FORMAT_ARGB32, surface.get_width(), surface.get_height())
        cr = cairo.Context(copy)
        cr.set_operator(cairo.Operator.SOURCE)
        cr.set_source_surface(surface)
        cr.paint()
        return copy

    def append(self, tool):
        was_modified = self.get_modified()
        self.appending = True
        self.undo.append(tool)
        self.redo.clear()
        if not tool.is_selection():
            cr = cairo.Context(self.surface)
            tool.on_draw(cr, self)
        else:
            alt = self._copy_surface(self.surface)
            cr_alt = cairo.Context(alt)
            tool.on_draw(cr_alt, self)
            self.surface = alt
        self.appending = False
        if not was_modified:
            self.set_modified(True)

    def do_redo(self):
        if not self.redo:
            return
        logger.info("do_redo")
        tool = self.redo.pop()
        self.undo.append(tool)
        redo, self.redo = self.redo, []
        self.surface = self._copy_surface(self.original)
        undo, self.undo = self.undo, []
        for tool in undo:
            self.append(tool)
        self.redo = redo

    def do_undo(self):
        if not self.get_modified():
            return
        logger.info("do_undo")
        tool = self.undo.pop()
        self.redo.append(tool)
        redo, self.redo = self.redo, []
        self.surface = self._copy_surface(self.original)
        undo, self.undo = self.undo, []
        for tool in undo:
            self.append(tool)
        self.redo = redo
        if not self.get_modified():
            self.emit('modified-changed')

    def draw(self, cr):
        cr.rectangle(0, 0, self.get_width(), self.get_height())
        cr.set_source_rgb(*self.background_color)
        cr.fill()
        cr.set_source_surface(self.get_surface())
        cr.paint()

    def get_background_color(self):
        return self.background_color

    def get_height(self):
        return self.surface.get_height()

    def get_modified(self):
        return 0 < len(self.undo)

    def get_surface(self):
        return self.surface

    def get_transparent_mode(self):
        return self.transparent_mode

    def get_width(self):
        return self.surface.get_width()

    def make_opaque(self, surface):
        copy = cairo.ImageSurface(cairo.FORMAT_ARGB32, surface.get_width(), surface.get_height())
        cr = cairo.Context(copy)
        cr.set_source_rgba(*self.background_color, 1)
        cr.paint()
        cr.set_source_surface(surface)
        cr.paint()
        return copy

    def make_transparent(self, surface):
        pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0,
                                             surface.get_width(), surface.get_height())
        rgb = [int(i * 255) for i in self.get_background_color()]
        pixbuf = pixbuf.add_alpha(True, *rgb)
        return Gdk.cairo_surface_create_from_pixbuf(pixbuf, 0, None)

    def set_background_color(self, rgb):
        self.background_color = rgb

    def set_modified(self, modified):
        if self.get_modified() and not modified:
            self.original = self._copy_surface(self.surface)
            self.undo = []
            self.redo = []
        self.emit('modified-changed')
        return self.get_modified()

    def set_transparent_mode(self, mode):
        if self.transparent_mode == mode:
            return
        self.transparent_mode = mode
        if self.transparent_mode:
            self.surface = self.make_transparent(self.surface)
            self.original = self.make_transparent(self.original)
        else:
            self.surface = self.make_opaque(self.surface)
            self.original = self.make_opaque(self.original)

    def set_source_rgba(self, cr):
        if self.transparent_mode and self.appending:
            alpha = 0
        else:
            alpha = 1
        cr.set_source_rgba(*self.get_background_color(), alpha)

    def set_surface(self, surface):
        self.surface = surface
        if self.get_transparent_mode():
            self.surface = self.make_transparent(surface)

    def write_to_png(self, fobj):
        self.surface.write_to_png(fobj)


class PaintView(Gtk.DrawingArea, Gtk.Scrollable):

    __gsignals__ = {
        'cut-clipboard': (GObject.SIGNAL_RUN_LAST, None, ()),
        'copy-clipboard': (GObject.SIGNAL_RUN_LAST, None, ()),
        'paste-clipboard': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'redo': (GObject.SIGNAL_RUN_LAST, None, ()),
        'select-all': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'tool': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'undo': (GObject.SIGNAL_RUN_LAST, None, ()),
        'style-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'tool-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, buffer=None):
        super().__init__()
        self.set_can_focus(True)
        self._init_scrollable()
        self._init_immultiontext()

        self.antialias = True
        self.color = (0, 0, 0, 1)
        self.line_width = 1
        self.tool_cls = Pencil
        self.tool = Pencil(self)
        self.set_buffer(buffer)
        self.caret = Gdk.Rectangle()
        self.set_font(package.get_document_font_name())
        self.last_mouse_point = (-1, -1)
        self.clock = False

        self.connect("draw", self.on_draw)
        self.connect('configure-event', self.on_configure)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect('motion-notify-event', self.on_mouse_move)
        self.connect('button-press-event', self.on_mouse_press)
        self.connect('button-release-event', self.on_mouse_release)
        self.connect('enter-notify-event', self.on_crossing)
        self.connect('leave-notify-event', self.on_crossing)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.SCROLL_MASK |
                        Gdk.EventMask.ENTER_NOTIFY_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK)

    def _change_tool(self, tool_cls):
        self.tool_cls = tool_cls
        self.tool = tool_cls(self)
        self.tool.set_antialias(self.antialias)
        self.tool.set_color(*self.color)
        self.tool.set_line_width(self.line_width)
        self._update_cursor(*self.last_mouse_point, False)
        self.emit('tool-changed')

    def _commit_selection(self):
        if self.tool.has_selection():
            self.im.reset()
            self.buffer.append(self.tool)
            return True
        return False

    def _get_offset(self):
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        dx = 0
        if width < self.width:
            if self._hadjustment:
                dx = self._hadjustment.get_value()
        else:
            dx = (self.width - width) / 2
        dy = 0
        if height < self.height:
            if self._vadjustment:
                dy = self._vadjustment.get_value()
        else:
            dy = (self.height - height) / 2
        return round(dx), round(dy)

    def _has_preedit(self):
        return self.preedit[0]

    def _init_immultiontext(self):
        self.im = Gtk.IMMulticontext()
        self.im.connect("commit", self.on_commit)
        self.im.connect("delete-surrounding", self.on_delete_surrounding)
        self.im.connect("retrieve-surrounding", self.on_retrieve_surrounding)
        self.im.connect("preedit-changed", self.on_preedit_changed)
        self.im.connect("preedit-end", self.on_preedit_end)
        self.im.connect("preedit-start", self.on_preedit_start)
        self.preedit = ('', None, 0)

    def _init_scrollable(self):
        self._hadjustment = self._vadjustment = None
        self._hadjust_signal = self._vadjust_signal = None

    def _timeout(self):
        if self.tool.has_animation():
            self.queue_draw()
            return True
        self.clock = False
        return False

    def _update_cursor(self, x, y, pressed):
        if (x < 0 or y < 0) and not pressed:
            cursor = Gdk.CursorType.TOP_LEFT_ARROW
        else:
            cursor = self.tool.get_cursor(self, x, y, pressed)
        self.get_root_window().set_cursor(Gdk.Cursor.new(cursor))

    def do_copy_clipboard(self):
        if not self.tool.has_selection():
            return
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        self.tool.copy_clipboard(clipboard, self.buffer)

    def do_cut_clipboard(self):
        if not self.tool.has_selection():
            return
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        if self.tool.cut_clipboard(clipboard, self.buffer):
            self.buffer.append(self.tool)
            self._change_tool(self.tool_cls)
        self.queue_draw()

    def do_paste_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        if clipboard.wait_is_image_available():
            image = clipboard.wait_for_image()
            if image is not None:
                self._commit_selection()
                # Temporarily change tool
                self.tool = Paste(self, image)
                self.tool.set_antialias(self.antialias)
                self.tool.set_color(*self.color)
                self.queue_draw()
                return
        text = clipboard.wait_for_text()
        if text is not None:
            if not self.tool.is_text():
                self._commit_selection()
                self._change_tool(Text)
            self.tool.insert_text(text)
            self.reflow()

    def do_redo(self):
        if self.tool.has_selection():
            return
        self.buffer.emit('redo')
        self.queue_draw()

    def do_select_all(self, select):
        self._commit_selection()
        self._change_tool(Selection)
        self.tool.select(0, 0, self.width, self.height)
        self.queue_draw()

    def do_tool(self, tool):
        self._commit_selection()
        cls = {
            "lasso": Lasso,
            "selection": Selection,
            "pencil": Pencil,
            "eraser": Eraser,
            "line": Line,
            "rectangle": Rectangle,
            "oval": Oval,
            "text": Text,
            "floodfill": FloodFill
        }.get(tool, Pencil)
        self._change_tool(cls)
        self.queue_draw()

    def do_undo(self):
        if self._commit_selection():
            self._change_tool(self.tool_cls)
        self.buffer.emit('undo')
        self.queue_draw()

    def get_antialias(self):
        return self.antialias

    def get_buffer(self):
        return self.buffer

    def get_editable(self):
        return True

    def get_font(self):
        return self.font

    def get_hadjustment(self):
        return self._hadjustment

    def get_style(self):
        return str(self.line_width) + 'px'

    def get_tool(self):
        return self.tool_cls.get_name()

    def get_vadjustment(self):
        return self._vadjustment

    def on_commit(self, im, str):
        if self.tool.on_commit(im, str):
            self.reflow()

    def on_configure(self, wid, event):
        if self._hadjustment:
            w = self.width - self.get_allocated_width()
            if w < 0:
                w = 0
            self._hadjustment.set_properties(
                lower=0,
                upper=w,
                page_size=1
            )
        if self._vadjustment:
            h = self.height - self.get_allocated_height()
            if h < 0:
                h = 0
            self._vadjustment.set_properties(
                lower=0,
                upper=h,
                page_size=1
            )
        return True

    def on_crossing(self, wid, event):
        if event.type == Gdk.EventType.LEAVE_NOTIFY:
            self.last_mouse_point = (-1, -1)    # out of the canvas
        else:
            x, y = self._get_offset()
            x += round(event.x)
            y += round(event.y)
            self.last_mouse_point = (x, y)
        self._update_cursor(*self.last_mouse_point, event.state & Gdk.ModifierType.BUTTON1_MASK)

    def on_delete_surrounding(self, im, offset, n_chars):
        if self.tool.on_delete_surrounding(im, offset, n_chars):
            self.reflow()
            return True
        return False

    def on_draw(self, wid, cr):
        if not self.clock and self.tool.has_animation():
            self.clock = True
            GLib.timeout_add(200, self._timeout)
        dx, dy = self._get_offset()
        if dx < 0 or dy < 0:
            cr.rectangle(0, 0, wid.get_allocated_width(), wid.get_allocated_height())
            cr.set_source_rgba(0.5, 0.5, 0.5, 1)
            cr.fill()
        cr.translate(-dx, -dy)
        self.buffer.draw(cr)
        self.tool.on_draw(cr, self.buffer)
        self.tool.set_cursor_location(self.im, dx, dy)

    def on_focus_in(self, wid, event):
        self.im.set_client_window(wid.get_window())
        self.im.focus_in()
        return True

    def on_focus_out(self, wid, event):
        self.im.focus_out()
        return True

    def on_key_press(self, wid, event):
        if self.tool.on_key_press(self, self.im, event):
            self.reflow()
            return True
        return False

    def on_key_release(self, wid, event):
        return self.tool.on_key_release(self, self.im, event)

    def on_mouse_move(self, wid, event):
        x, y = self._get_offset()
        x += round(event.x)
        y += round(event.y)
        self.last_mouse_point = (x, y)
        if event.state & Gdk.EventMask.BUTTON_PRESS_MASK:
            self.tool.on_mouse_move(self, event, x, y)
            self.queue_draw()
        self._update_cursor(x, y, event.state & Gdk.ModifierType.BUTTON1_MASK)
        return True

    def on_mouse_press(self, wid, event):
        x, y = self._get_offset()
        x += round(event.x)
        y += round(event.y)
        if event.button == Gdk.BUTTON_PRIMARY:
            cr = cairo.Context(self.buffer.get_surface())
            if self.tool.has_selection() and not self.tool.in_selection(cr, x, y):
                self._commit_selection()
                self._change_tool(self.tool_cls)
            self.tool.on_mouse_press(self, event, x, y)
            self.queue_draw()
        self._update_cursor(x, y, True)
        return False

    def on_mouse_release(self, wid, event):
        x, y = self._get_offset()
        x += round(event.x)
        y += round(event.y)
        if event.button == Gdk.BUTTON_PRIMARY:
            self.tool.on_mouse_release(self, event, x, y)
            if not self.tool.is_selection():
                self.buffer.append(self.tool)
                self._change_tool(self.tool_cls)
            self.queue_draw()
        self._update_cursor(x, y, False)
        return True

    def on_preedit_changed(self, im):
        if self.tool.on_preedit_changed(im):
            self.reflow()

    def on_preedit_end(self, im):
        if self.tool.on_preedit_end(im):
            self.reflow()

    def on_preedit_start(self, im):
        if self.tool.on_preedit_start(im):
            self.reflow()

    def on_retrieve_surrounding(self, im):
        self.tool.on_retrieve_surrounding(im)
        return True

    def on_value_changed(self, *whatever):
        self.queue_draw()

    def reflow(self):
        self.tool.reflow(self)
        self.queue_draw()

    def reset(self):
        if self._commit_selection():
            self._change_tool(self.tool_cls)
        self.queue_draw()

    def set_antialias(self, enable):
        self.antialias = enable
        self.tool.set_antialias(enable)

    def set_buffer(self, buffer):
        if buffer:
            self.buffer = buffer
        else:
            self.buffer = PaintBuffer()
        self.width = self.buffer.get_width()
        self.height = self.buffer.get_height()

    def set_color(self, red, green, blue, alpha=1):
        self.color = (red, green, blue, alpha)
        self.tool.set_color(*self.color)
        self.queue_draw()

    def set_font(self, font):
        self.font = font
        self.tool.set_font(font)
        self.reflow()

    def set_hadjustment(self, adjustment):
        if self._hadjustment:
            self._hadjustment.disconnect(self._hadjust_signal)
            self._hadjust_signal = None

        self._hadjustment = adjustment
        if adjustment:
            w = self.width - self.get_allocated_width()
            if w < 0:
                w = 0
            adjustment.set_properties(
                lower=0,
                upper=w,
                page_size=1
            )
            self._hadjust_signal = adjustment.connect("value-changed", self.on_value_changed)

    def set_line_width(self, width):
        if self.line_width != width:
            self.line_width = width
            self.tool.set_line_width(width)
            self.emit('style-changed')

    def set_vadjustment(self, adjustment):
        if self._vadjustment:
            self._vadjustment.disconnect(self._vadjust_signal)
            self._vadjust_signal = None

        self._vadjustment = adjustment
        if adjustment:
            h = self.height - self.get_allocated_height()
            if h < 0:
                h = 0
            adjustment.set_properties(
                lower=0,
                upper=h,
                page_size=1
            )
            self._vadjust_signal = adjustment.connect("value-changed", self.on_value_changed)

    hadjustment = GObject.property(
        get_hadjustment, set_hadjustment, type=Gtk.Adjustment
    )
    vadjustment = GObject.property(
        get_vadjustment, set_vadjustment, type=Gtk.Adjustment
    )
    hscroll_policy = GObject.property(
        default=Gtk.ScrollablePolicy.NATURAL, type=Gtk.ScrollablePolicy
    )
    vscroll_policy = GObject.property(
        default=Gtk.ScrollablePolicy.NATURAL, type=Gtk.ScrollablePolicy
    )
