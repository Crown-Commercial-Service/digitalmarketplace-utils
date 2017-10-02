from odf.element import Element
from odf.namespaces import OFFICENS
from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style
from odf.table import Table, TableColumn, TableRow, TableCell, CoveredTableCell
from odf.text import P, A  # noqa (used by frontend apps)


class Row(object):
    def __init__(self, **kwargs):
        self._row = TableRow(**kwargs)

    def write_cell(self, value, **kwargs):
        if "numbercolumnsspanned" in kwargs or "numberrowsspanned" in kwargs:
            kwargs.setdefault("numberrowsspanned", "1")
            kwargs.setdefault("numbercolumnsspanned", "1")

        cell = TableCell(**kwargs)
        cell.setAttrNS(OFFICENS, "value-type", "string")

        if isinstance(value, Element):
            para = P()
            para.addElement(value)
            cell.addElement(para)
        else:
            for line in value.split("\n"):
                cell.addElement(P(text=line))

        self._row.addElement(cell)

    def write_cells(self, cells, **kwargs):
        for cell in cells:
            self.write_cell(value=cell, **kwargs)

    def write_covered_cell(self):
        self._row.addElement(CoveredTableCell())


class Sheet(object):
    def __init__(self, name):
        self._table = Table(name=name)
        self._rows = {}

    def create_row(self, name, **kwargs):
        """Create an empty row to manually insert cells"""
        self._rows[name] = Row(**kwargs)
        self._table.addElement(self._rows[name]._row)

        return self._rows[name]

    def write_row(self, name, cells, row_styles={}, cell_styles={}):
        """Create a new row and populate it with the given cells"""
        row = self.create_row(name, **row_styles)
        row.write_cells(cells, **cell_styles)

    def get_row(self, name):
        return self._rows[name]

    def create_column(self, **kwargs):
        column = TableColumn(**kwargs)

        self._table.addElement(column)

    def read_cell(self, x, y):
        try:
            cell = self._table.getElementsByType(TableRow)[y].childNodes[x]
        except IndexError:
            return ''

        result = []

        for element in cell.childNodes:
            result.append("".join([v.data for v in element.childNodes]))

        return "\n".join(result)


class SpreadSheet(object):
    def __init__(self):
        self._document = OpenDocumentSpreadsheet()
        self._sheets = {}

    def sheet(self, name):
        if name not in self._sheets:
            self._sheets[name] = Sheet(name)
            self._document.spreadsheet.addElement(self._sheets[name]._table)

        return self._sheets[name]

    def add_style(self, name, family, styles, **kwargs):
        style = Style(name=name, family=family, **kwargs)

        for v in styles:
            style.addElement(v)

        self._document.automaticstyles.addElement(style)

    def add_font(self, fontface):
        self._document.fontfacedecls.addElement(fontface)

    def save(self, buf):
        return self._document.save(buf)
