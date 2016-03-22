'''
Grid Layout
===========

.. only:: html

    .. image:: images/gridlayout.gif
        :align: right

.. only:: latex

    .. image:: images/gridlayout.png
        :align: right

.. versionadded:: 1.0.4

The :class:`GridLayout` arranges children in a matrix. It takes the available
space and divides it into columns and rows, then adds widgets to the resulting
"cells".

.. versionchanged:: 1.0.7
    The implementation has changed to use the widget size_hint for calculating
    column/row sizes. `uniform_width` and `uniform_height` have been removed
    and other properties have added to give you more control.

Background
----------

Unlike many other toolkits, you cannot explicitly place a widget in a specific
column/row. Each child is automatically assigned a position determined by the
layout configuration and the child's index in the children list.

A GridLayout must always have at least one input constraint:
:attr:`GridLayout.cols` or :attr:`GridLayout.rows`. If you do not specify cols
or rows, the Layout will throw an exception.

Column Width and Row Height
---------------------------

The column width/row height are determined in 3 steps:

    - The initial size is given by the :attr:`col_default_width` and
      :attr:`row_default_height` properties. To customize the size of a single
      column or row, use :attr:`cols_minimum` or :attr:`rows_minimum`.
    - The `size_hint_x`/`size_hint_y` of the children are taken into account.
      If no widgets have a size hint, the maximum size is used for all
      children.
    - You can force the default size by setting the :attr:`col_force_default`
      or :attr:`row_force_default` property. This will force the layout to
      ignore the `width` and `size_hint` properties of children and use the
      default size.

Using a GridLayout
------------------

In the example below, all widgets will have an equal size. By default, the
`size_hint` is (1, 1), so a Widget will take the full size of the parent::

    layout = GridLayout(cols=2)
    layout.add_widget(Button(text='Hello 1'))
    layout.add_widget(Button(text='World 1'))
    layout.add_widget(Button(text='Hello 2'))
    layout.add_widget(Button(text='World 2'))

.. image:: images/gridlayout_1.jpg

Now, let's fix the size of Hello buttons to 100px instead of using
size_hint_x=1::

    layout = GridLayout(cols=2)
    layout.add_widget(Button(text='Hello 1', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 1'))
    layout.add_widget(Button(text='Hello 2', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 2'))

.. image:: images/gridlayout_2.jpg

Next, let's fix the row height to a specific size::

    layout = GridLayout(cols=2, row_force_default=True, row_default_height=40)
    layout.add_widget(Button(text='Hello 1', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 1'))
    layout.add_widget(Button(text='Hello 2', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 2'))

.. image:: images/gridlayout_3.jpg

'''

__all__ = ('GridLayout', 'GridLayoutException')

from kivy.logger import Logger
from kivy.uix.layout import Layout, RecycleLayout
from kivy.properties import NumericProperty, BooleanProperty, DictProperty, \
    BoundedNumericProperty, ReferenceListProperty, VariableListProperty, \
    ObjectProperty, StringProperty
from math import ceil
from collections import defaultdict


def nmax(*args):
    '''(internal) Implementation of a max() function that supports None.
    '''
    # merge into one list
    args = [x for x in args if x is not None]
    return max(args)


class GridLayoutException(Exception):
    '''Exception for errors if the grid layout manipulation fails.
    '''
    pass


class GridLayout(Layout):
    '''Grid layout class. See module documentation for more information.
    '''

    spacing = VariableListProperty([0, 0], length=2)
    '''Spacing between children: [spacing_horizontal, spacing_vertical].

    spacing also accepts a one argument form [spacing].

    :attr:`spacing` is a
    :class:`~kivy.properties.VariableListProperty` and defaults to [0, 0].
    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between the layout box and it's children: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionchanged:: 1.7.0
        Replaced NumericProperty with VariableListProperty.

    :attr:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0, 0, 0].
    '''

    cols = BoundedNumericProperty(None, min=0, allownone=True)
    '''Number of columns in the grid.

    .. versionchanged:: 1.0.8
        Changed from a NumericProperty to BoundedNumericProperty. You can no
        longer set this to a negative value.

    :attr:`cols` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    '''

    rows = BoundedNumericProperty(None, min=0, allownone=True)
    '''Number of rows in the grid.

    .. versionchanged:: 1.0.8
        Changed from a NumericProperty to a BoundedNumericProperty. You can no
        longer set this to a negative value.

    :attr:`rows` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    '''

    col_default_width = NumericProperty(0)
    '''Default minimum size to use for a column.

    .. versionadded:: 1.0.7

    :attr:`col_default_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    row_default_height = NumericProperty(0)
    '''Default minimum size to use for row.

    .. versionadded:: 1.0.7

    :attr:`row_default_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    col_force_default = BooleanProperty(False)
    '''If True, ignore the width and size_hint_x of the child and use the
    default column width.

    .. versionadded:: 1.0.7

    :attr:`col_force_default` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    row_force_default = BooleanProperty(False)
    '''If True, ignore the height and size_hint_y of the child and use the
    default row height.

    .. versionadded:: 1.0.7

    :attr:`row_force_default` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    cols_minimum = DictProperty({})
    '''Dict of minimum width for each column. The dictionary keys are the
    column numbers, e.g. 0, 1, 2...

    .. versionadded:: 1.0.7

    :attr:`cols_minimum` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    rows_minimum = DictProperty({})
    '''Dict of minimum height for each row. The dictionary keys are the
    row numbers, e.g. 0, 1, 2...

    .. versionadded:: 1.0.7

    :attr:`rows_minimum` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    minimum_width = NumericProperty(0)
    '''Automatically computed minimum width needed to contain all children.

    .. versionadded:: 1.0.8

    :attr:`minimum_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0. It is read only.
    '''

    minimum_height = NumericProperty(0)
    '''Automatically computed minimum height needed to contain all children.

    .. versionadded:: 1.0.8

    :attr:`minimum_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0. It is read only.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Automatically computed minimum size needed to contain all children.

    .. versionadded:: 1.0.8

    :attr:`minimum_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`minimum_width`, :attr:`minimum_height`) properties. It is read
    only.
    '''

    def __init__(self, **kwargs):
        self._cols = self._rows = None
        super(GridLayout, self).__init__(**kwargs)
        fbind = self.fbind
        update = self._trigger_layout
        fbind('col_default_width', update)
        fbind('row_default_height', update)
        fbind('col_force_default', update)
        fbind('row_force_default', update)
        fbind('cols', update)
        fbind('rows', update)
        fbind('parent', update)
        fbind('spacing', update)
        fbind('padding', update)
        fbind('children', update)
        fbind('size', update)
        fbind('pos', update)

    def get_max_widgets(self):
        if self.cols and self.rows:
            return self.rows * self.cols
        else:
            return None

    def on_children(self, instance, value):
        # if that makes impossible to construct things with deffered method,
        # migrate this test in do_layout, and/or issue a warning.
        smax = self.get_max_widgets()
        if smax and len(value) > smax:
            raise GridLayoutException(
                'Too many children in GridLayout. Increase rows/cols!')

    def _init_rows_cols_sizes(self, count):
        # the goal here is to calculate the minimum size of every cols/rows
        # and determine if they have stretch or not
        current_cols = self.cols
        current_rows = self.rows

        # if no cols or rows are set, we can't calculate minimum size.
        # the grid must be contrained at least on one side
        if not current_cols and not current_rows:
            Logger.warning('%r have no cols or rows set, '
                           'layout is not triggered.' % self)
            return
        if current_cols is None:
            current_cols = int(ceil(count / float(current_rows)))
        elif current_rows is None:
            current_rows = int(ceil(count / float(current_cols)))

        current_cols = max(1, current_cols)
        current_rows = max(1, current_rows)

        self._cols = cols = [self.col_default_width] * current_cols
        self._cols_sh = cols_sh = [None] * current_cols
        self._rows = rows = [self.row_default_height] * current_rows
        self._rows_sh = rows_sh = [None] * current_rows

        # update minimum size from the dicts
        # FIXME index might be outside the bounds ?
        for index, value in self.cols_minimum.items():
            cols[index] = value
        for index, value in self.rows_minimum.items():
            rows[index] = value
        return True

    def _fill_rows_cols_sizes(self):
        cols, rows = self._cols, self._rows
        cols_sh, rows_sh = self._cols_sh, self._rows_sh

        # calculate minimum size for each columns and rows
        n_cols = len(cols)
        for i, child in enumerate(reversed(self.children)):
            (shw, shh), (w, h) = child.size_hint, child.size
            row, col = divmod(i, n_cols)

            # compute minimum size / maximum stretch needed
            if shw is None:
                cols[col] = nmax(cols[col], w)
            else:
                cols_sh[col] = nmax(cols_sh[col], shw)

            if shh is None:
                rows[row] = nmax(rows[row], h)
            else:
                rows_sh[row] = nmax(rows_sh[row], shh)

    def _update_minimum_size(self):
        # calculate minimum width/height needed, starting from padding +
        # spacing
        l, t, r, b = self.padding
        spacing_x, spacing_y = self.spacing
        cols, rows = self._cols, self._rows
        width = l + r + spacing_x * (len(cols) - 1)
        height = t + b + spacing_y * (len(rows) - 1)
        # then add the cell size
        width += sum(cols)
        height += sum(rows)

        # finally, set the minimum size
        self.minimum_size = (width, height)

    def _finalize_rows_cols_sizes(self):
        selfw = self.width
        selfh = self.height

        # resolve size for each column
        if self.col_force_default:
            cols = [self.col_default_width] * len(self._cols)
            for index, value in self.cols_minimum.items():
                cols[index] = value
            self._cols = cols
        else:
            cols = self._cols
            cols_sh = self._cols_sh
            cols_weigth = sum([x for x in cols_sh if x])
            strech_w = max(0, selfw - self.minimum_width)
            for index, col_stretch in enumerate(cols_sh):
                # if the col don't have strech information, nothing to do
                if not col_stretch:
                    continue
                # add to the min width whatever remains from size_hint
                cols[index] += strech_w * col_stretch / cols_weigth

        # same algo for rows
        if self.row_force_default:
            rows = [self.row_default_height] * len(self._rows)
            for index, value in self.rows_minimum.items():
                rows[index] = value
            self._rows = rows
        else:
            rows = self._rows
            rows_sh = self._rows_sh
            rows_weigth = sum([x for x in rows_sh if x])
            strech_h = max(0, selfh - self.minimum_height)
            for index in range(len(rows)):
                # if the row don't have strech information, nothing to do
                row_stretch = rows_sh[index]
                if not row_stretch:
                    continue
                # add to the min height whatever remains from size_hint
                rows[index] += strech_h * row_stretch / rows_weigth

    def _iterate_layout(self, count):
        selfx = self.x
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        spacing_x, spacing_y = self.spacing

        i = count - 1
        y = self.top - padding_top
        cols = self._cols
        for row_height in self._rows:
            x = selfx + padding_left
            for col_width in cols:
                if i < 0:
                    break

                yield i, (x, y - row_height), (col_width, row_height)
                i = i - 1
                x = x + col_width + spacing_x
            y -= row_height + spacing_y

    def do_layout(self, *largs):
        children = self.children
        if not children or not self._init_rows_cols_sizes(len(children)):
            l, t, r, b = self.padding
            self.minimum_size = l + r, t + b
        self._fill_rows_cols_sizes()
        self._update_minimum_size()
        self._finalize_rows_cols_sizes()

        for i, pos, (w, h) in self._iterate_layout(len(children)):
            c = children[i]
            c.pos = pos
            shw, shh = c.size_hint
            if shw is None:
                if shh is not None:
                    c.height = h
            else:
                if shh is None:
                    c.width = w
                else:
                    c.size = (w, h)


class RecycleGridLayout(RecycleLayout, GridLayout):

    _cols_pos = None
    _rows_pos = None

    def __init__(self, **kwargs):
        super(RecycleGridLayout, self).__init__(**kwargs)
        self.funbind('children', self._trigger_layout)

    def on_children(self, instance, value):
        pass

    def _fill_rows_cols_sizes(self):
        cols, rows = self._cols, self._rows
        cols_sh, rows_sh = self._cols_sh, self._rows_sh
        self._cols_count = cols_count = [defaultdict(int) for _ in cols]
        self._rows_count = rows_count = [defaultdict(int) for _ in rows]

        # calculate minimum size for each columns and rows
        n_cols = len(cols)
        for i, opt in enumerate(self.view_opts):
            (shw, shh), (w, h) = opt['size_hint'], opt['size']
            row, col = divmod(i, n_cols)
            if shw is None:
                cols_count[col][w] += 1
            if shh is None:
                rows_count[row][h] += 1

            # compute minimum size / maximum stretch needed
            if shw is None:
                cols[col] = nmax(cols[col], w)
            else:
                cols_sh[col] = nmax(cols_sh[col], shw)

            if shh is None:
                rows[row] = nmax(rows[row], h)
            else:
                rows_sh[row] = nmax(rows_sh[row], shh)

    def _update_rows_cols_sizes(self, changed):
        cols_count, rows_count = self._cols_count, self._rows_count
        cols, rows = self._cols, self._rows
        remove_view = self.remove_view
        n_cols = len(cols_count)

        # this can be further improved to reduce re-comp, but whatever...
        for index, widget, (w, h), (wn, hn), sh, shn, _, _ in changed:
            if sh != shn:
                return True
            elif (sh[0] is not None and w != wn or
                  sh[1] is not None and h != hn):
                remove_view(widget, index)
            else:
                row, col = divmod(index, n_cols)

                if w != wn:
                    col_w = cols[col]
                    cols_count[col][w] -= 1
                    cols_count[col][wn] += 1
                    was_last_w = cols_count[col][w] <= 0
                    if was_last_w and col_w == w or wn > col_w:
                        return True
                    if was_last_w:
                        del cols_count[col][w]

                if h != hn:
                    row_h = rows[row]
                    rows_count[row][h] -= 1
                    rows_count[row][hn] += 1
                    was_last_h = rows_count[row][h] <= 0
                    if was_last_h and row_h == h or hn > row_h:
                        return True
                    if was_last_h:
                        del rows_count[row][h]

        return False

    def compute_layout(self, data, flags):
        super(RecycleGridLayout, self).compute_layout(data, flags)

        n = len(data)
        smax = self.get_max_widgets()
        if smax and n > smax:
            raise GridLayoutException(
                'Too many children ({}) in GridLayout. Increase rows/cols!'.
                format(n))

        changed = self._changed_views
        if (changed is None or
                changed and not self._update_rows_cols_sizes(changed)):
            return

        self.clear_layout()
        if not self._init_rows_cols_sizes(n):
            self._cols = None
            l, t, r, b = self.padding
            self.minimum_size = l + r, t + b
            return
        self._fill_rows_cols_sizes()
        self._update_minimum_size()
        self._finalize_rows_cols_sizes()

        view_opts = self.view_opts
        for widget, p, (w, h) in self._iterate_layout(n):
            opt = view_opts[n - widget - 1]
            shw, shh = opt['size_hint']
            opt['pos'] = p
            wo, ho = opt['size']
            # layout won't/shouldn't change previous size if size_hint is None
            # which is what w/h being None means.
            opt['size'] = [(wo if shw is None else w),
                           (ho if shh is None else h)]

        spacing_x, spacing_y = self.spacing
        cols, rows = self._cols, self._rows

        cols_pos = self._cols_pos = [None, ] * len(cols)
        rows_pos = self._rows_pos = [None, ] * len(rows)

        cols_pos[0] = self.x
        last = cols_pos[0] + self.padding[0] + cols[0] + spacing_x / 2.
        for i, val in enumerate(cols[1:], 1):
            cols_pos[i] = last
            last += val + spacing_x

        last = rows_pos[-1] = \
            self.y + self.height - self.padding[1] - rows[0] - spacing_y / 2.
        n = len(rows)
        for i, val in enumerate(rows[1:], 1):
            last -= spacing_y + val
            rows_pos[n - 1 - i] = last

    def get_view_index_at(self, pos):
        if self._cols_pos is None:
            return 0

        x, y = pos
        col_pos = self._cols_pos
        row_pos = self._rows_pos
        cols, rows = self._cols, self._rows
        if not col_pos or not row_pos:
            return 0

        if x >= col_pos[-1]:
            ix = len(cols) - 1
        else:
            ix = 0
            for val in col_pos[1:]:
                if x < val:
                    break
                ix += 1

        if y >= row_pos[-1]:
            iy = len(rows) - 1
        else:
            iy = 0
            for val in row_pos[1:]:
                if y < val:
                    break
                iy += 1

        # gridlayout counts from left to right, top to down
        iy = len(rows) - iy - 1
        return iy * len(cols) + ix

    def compute_visible_views(self, data, viewport):
        if self._cols_pos is None:
            return []
        x, y, w, h = viewport
        # gridlayout counts from left to right, top to down
        at_idx = self.get_view_index_at
        bl = at_idx((x, y))
        br = at_idx((x + w, y))
        tl = at_idx((x, y + h))
        n = len(data)

        indices = []
        row = len(self._cols)
        if row:
            x_slice = br - bl + 1
            for s in range(tl, bl + 1, row):
                indices.extend(range(min(s, n), min(n, s + x_slice)))

        return indices
