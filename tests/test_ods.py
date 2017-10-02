import mock
import functools

import dmutils.ods as ods

from hypothesis import strategies as st
from hypothesis import given, example

po = functools.partial(mock.patch.object, autospec=True)


class TestRow(object):

    @given(st.dictionaries(st.text(), st.text()))
    def test___init__(self, kwargs):
        with po(ods, 'TableRow') as TableRow:
            instance = ods.Row(**kwargs)

        TableRow.assert_called_once_with(**kwargs)

        assert instance._row == TableRow.return_value

    @given(st.text(), st.dictionaries(st.text(), st.text()))
    @example("", {"numberrowsspanned": '1'})
    @example("", {"numbercolumnsspanned": '1'})
    def test_write_cell(self, value, kwargs):
        instance = ods.Row()

        instance._row = mock.MagicMock(spec_set=instance._row)

        expected = dict(**kwargs)

        if "numbercolumnsspanned" in kwargs:
            expected.setdefault("numberrowsspanned", "1")

        if "numberrowsspanned" in kwargs:
            expected.setdefault("numbercolumnsspanned", "1")

        ps = [mock.Mock() for v in value.split("\n")]

        with po(ods, 'TableCell') as TableCell:
            with po(ods, 'P') as P:
                P.side_effect = iter(ps)
                instance.write_cell(value, **kwargs)

        TableCell.assert_called_once_with(**expected)

        cell = TableCell.return_value
        cell.setAttrNS.assert_called_once_with(ods.OFFICENS, 'value-type',
                                               'string')

        P.assert_has_calls([mock.call(text=line) for line in value.split("\n")])

        cell.addElement.assert_has_calls([mock.call(e) for e in ps], True)

        instance._row.addElement.assert_called_once_with(cell)

    def test_write_covered_cell(self):
        instance = ods.Row()

        instance._row = mock.MagicMock(spec_set=instance._row)

        with po(ods, 'CoveredTableCell') as CoveredTableCell:
            instance.write_covered_cell()

        cell = CoveredTableCell.return_value

        instance._row.addElement.assert_called_once_with(cell)


class TestSheet(object):
    @given(st.text())
    def test___init__(self, name):
        with po(ods, 'Table') as Table:
            instance = ods.Sheet(name)

        Table.assert_called_once_with(name=name)

        assert instance._table == Table.return_value

        assert instance._rows == {}

    @given(st.text().map(ods.Sheet), st.text(),
           st.dictionaries(st.text(), st.text()))
    def test_create_row(self, instance, name, kwargs):
        instance._table = mock.MagicMock(spec_set=instance._table)

        with mock.patch.object(ods, 'Row') as Row:
            result = instance.create_row(name, **kwargs)

        Row.assert_called_once_with(**kwargs)

        assert instance._rows[name] == Row.return_value

        assert result == Row.return_value

        instance._table.addElement\
                .assert_called_once_with(Row.return_value._row)

    @given(st.text().map(ods.Sheet), st.text())
    def test_get_row(self, instance, name):
        instance._rows[name] = expected = mock.Mock()

        with po(ods, 'Row'):
            assert expected == instance.get_row(name)

    @given(st.text().map(ods.Sheet), st.dictionaries(st.text(), st.text()))
    def test_create_column(self, instance, kwargs):
        instance._table = mock.MagicMock(spec_set=instance._table)

        with po(ods, 'TableColumn') as TableColumn:
            instance.create_column(**kwargs)

        TableColumn.assert_called_once_with(**kwargs)

        instance._table.addElement\
                .assert_called_once_with(TableColumn.return_value)

    @given(st.text().map(ods.Sheet),
           st.tuples(st.integers(min_value=0, max_value=15),
                     st.integers(min_value=0, max_value=15))
             .flatmap(lambda x: st.lists(st.lists(st.one_of(st.text(),
                                                            st.none()),
                                                  min_size=x[0], max_size=x[0]),
                                         min_size=x[0], max_size=x[0])),
           st.integers(min_value=-5, max_value=20),
           st.integers(min_value=-5, max_value=20))
    def test_read_cell(self, instance, data, x, y):
        for i, values in enumerate(data):
            instance.create_column()
            row = instance.create_row('row{}'.format(i))

            for value in values:
                if value is None:
                    row.write_covered_cell()
                else:
                    row.write_cell(value)

        try:
            expect = data[y][x]
        except IndexError:
            expect = ''

        assert instance.read_cell(x, y) == (expect or '')


class TestSpreadSheet(object):
    def test___init__(self):
        with po(ods, 'OpenDocumentSpreadsheet') as OpenDocumentSpreadsheet:
            instance = ods.SpreadSheet()

        OpenDocumentSpreadsheet.assert_called_once_with()

        assert instance._document == OpenDocumentSpreadsheet.return_value
        assert instance._sheets == {}

    @given(st.text())
    def test_sheet(self, name):
        instance = ods.SpreadSheet()
        instance._document = mock.MagicMock(spec_set=instance._document)

        with mock.patch.object(ods, 'Sheet') as Sheet:
            result1 = instance.sheet(name)
            result2 = instance.sheet(name)

        assert result1 == Sheet.return_value
        assert result2 == Sheet.return_value
        assert instance._sheets[name] == Sheet.return_value

        Sheet.assert_called_once_with(name)

        instance._document.spreadsheet.addElement\
                .assert_called_once_with(Sheet.return_value._table)

    @given(st.text(), st.text(), st.integers(min_value=0, max_value=10),
           st.dictionaries(st.text(), st.text()))
    def test_add_style(self, name, family, count, kwargs):
        styles = [mock.Mock() for v in range(count)]

        instance = ods.SpreadSheet()
        instance._document = mock.MagicMock(spec_set=instance._document)

        with po(ods, 'Style') as Style:
            instance.add_style(name, family, styles, **kwargs)

        Style.assert_called_once_with(name=name, family=family, **kwargs)

        Style.return_value.addElement\
             .assert_has_calls([mock.call(style) for style in styles], True)

        instance._document.automaticstyles.addElement\
                .assert_called_once_with(Style.return_value)

    def test_add_font(self):
        instance = ods.SpreadSheet()
        instance._document = mock.MagicMock(spec_set=instance._document)

        fontface = mock.Mock()

        instance.add_font(fontface)

        instance._document.fontfacedecls.addElement\
                .assert_called_once_with(fontface)

    def save(self):
        instance = ods.SpreadSheet()
        instance._document = mock.MagicMock(spec_set=instance._document)

        buf = mock.Mock()
        fontface = mock.Mock()

        instance.add_font(fontface)

        instance._document.save.assert_called_once_with(buf)
