from abc import ABCMeta, abstractmethod
import csv
import enum
from flask import abort, request, Response
from flask.views import View
from io import BytesIO
from odf.style import TextProperties, TableRowProperties, TableColumnProperties, TableCellProperties, FontFace

from dmutils import csv_generator
from dmutils import ods


class DownloadFileView(View, metaclass=ABCMeta):
    """An abstract base class appropriate for subclassing in the frontend apps when the user needs to be able to
    download some data as a CSV or ODS file. All abstract methods must be implemented on the subclass (although example
    implementations are included here with the kind of return value expected); all other methods should be able to
    be left alone to support handling and dispatching the request."""

    FILETYPES = enum.Enum('Filetypes', ['CSV', 'ODS'])

    def __init__(self, **kwargs):
        self.request = request

        self.data_api_client = None
        self.search_api_client = None
        self.content_loader = None

        super(View, self).__init__(**kwargs)

    @abstractmethod
    def _init_hook(self, **kwargs):
        """Hook into the start of the request to associate required clients/loaders with the instance and perform any
        other logic required for the start of the request."""
        self.data_api_client = None
        self.search_api_client = None
        self.content_loader = None

    def _post_request_hook(self, response=None, file_context=None, **kwargs):
        """A hook that can be used to implement any logic that should be run after the main download file process,
        and immediately before sending the response to the user."""
        pass

    @abstractmethod
    def get_file_context(self, **kwargs):
        """Must return a dictionary containing any data required by the generation routines.

        Required keys:
         * `filename`: without a file extension
         * `sheetname`: the name of the first sheet in the ODS file (assumption: single sheeted spreadsheet)"""
        return {'filename': 'my-download', 'sheetname': 'Sheet 1'}

    @abstractmethod
    def determine_filetype(self, file_context=None, **kwargs):
        """Logic to tell the View which filetype to generate; must return a choice from DownloadFileView.FILETYPES"""
        return DownloadFileView.FILETYPES.ODS

    @abstractmethod
    def generate_csv_rows(self, file_context):
        """Must return a nested iterable of rows+cells, eg [[heading1, heading2], [data1, data2], ...]"""
        return [['Heading 1', 'Heading 2'], ['Row 1, Column 1', 'Row 1, Column 2']]

    @abstractmethod
    def populate_styled_ods_with_data(self, spreadsheet, file_context):
        """Takes an empty dmutils.ods.SpreadSheet (with required fonts/styles already added) and populates the required
        data into it."""
        sheet = spreadsheet.sheet(file_context['sheetname'])
        sheet.write_row(name='header', cells=['Heading 1', 'Heading 2'])
        sheet.write_row(name='row1', cells=['Row 1, Column 1', 'Row 1, Column 2'])

    @staticmethod
    def create_blank_ods_with_styles():
        """Create a dmutils.ods.SpreadSheet pre-configured with some default styles, ready for population with data
        appropriate for the subclass View. Modifications here (except adding styles) are likely breaking changes."""
        spreadsheet = ods.SpreadSheet()

        # Add the font we will use for the entire spreadsheet.
        spreadsheet.add_font(FontFace(name="Arial", fontfamily="Arial"))

        # Add some default styles for columns.
        spreadsheet.add_style("col-default", "table-column", (
            TableColumnProperties(breakbefore="auto"),
        ), parentstylename="Default")

        spreadsheet.add_style("col-wide", "table-column", (
            TableColumnProperties(columnwidth="150pt", breakbefore="auto"),
        ), parentstylename="Default")

        spreadsheet.add_style("col-extra-wide", "table-column", (
            TableColumnProperties(columnwidth="300pt", breakbefore="auto"),
        ), parentstylename="Default")

        # Add some default styles for rows.
        spreadsheet.add_style("row-default", "table-row", (
            TableRowProperties(breakbefore="auto", useoptimalrowheight="false"),
        ), parentstylename="Default")

        spreadsheet.add_style("row-tall", "table-row", (
            TableRowProperties(breakbefore="auto", rowheight="30pt", useoptimalrowheight="false"),
        ), parentstylename="Default")

        spreadsheet.add_style("row-tall-optimal", "table-row", (
            TableRowProperties(breakbefore="auto", rowheight="30pt", useoptimalrowheight="true"),
        ), parentstylename="Default")

        # Add some default styles for cells.
        spreadsheet.add_style("cell-default", "table-cell", (
            TableCellProperties(wrapoption="wrap", verticalalign="top"),
            TextProperties(fontfamily="Arial", fontnameasian="Arial", fontnamecomplex="Arial", fontsize="11pt"),
        ), parentstylename="Default")

        spreadsheet.add_style("cell-header", "table-cell", (
            TableCellProperties(wrapoption="wrap", verticalalign="top"),
            TextProperties(fontfamily="Arial", fontnameasian="Arial", fontnamecomplex="Arial", fontsize="11pt",
                           fontweight="bold"),
        ), parentstylename="Default")

        return spreadsheet

    def create_response(self, file_context, file_type):
        if file_type == DownloadFileView.FILETYPES.CSV:
            body = csv_generator.iter_csv(self.generate_csv_rows(file_context), quoting=csv.QUOTE_ALL)

            mimetype = 'text/csv; header=present'

        elif file_type == DownloadFileView.FILETYPES.ODS:
            buffer = BytesIO()

            ods = self.create_blank_ods_with_styles()
            self.populate_styled_ods_with_data(ods, file_context)
            ods.save(buffer)

            body = buffer.getvalue()

            mimetype = 'application/vnd.oasis.opendocument.spreadsheet'

        else:
            abort(400)

        content_disposition = 'attachment;filename={}.{}'.format(file_context['filename'], file_type.name.lower())

        return Response(
            body,
            mimetype=mimetype,
            headers={
                "Content-Disposition": content_disposition,
                "Content-Type": mimetype
            }
        ), 200

    def dispatch_request(self, **kwargs):
        self._init_hook(**kwargs)

        file_context = self.get_file_context(**kwargs)
        file_type = self.determine_filetype(file_context, **kwargs)

        if not isinstance(file_type, enum.Enum) or file_type.name not in DownloadFileView.FILETYPES.__members__:
            abort(400)

        response = self.create_response(file_context, file_type)

        self._post_request_hook(response, **kwargs)
        return response


class SimpleDownloadFileView(DownloadFileView, metaclass=ABCMeta):
    """A slightly simplier version of the DownloadFileView where it is possible to have a single source of data
    for all download filetypes. If you want a fairly simple structure to your spreadsheet (in effect, a single sheet,
    with self-contained rows where cells don't span rows or columns), you can implement only `get_file_data_and_styles`
    to work with all supported filetypes."""
    @abstractmethod
    def get_file_data_and_column_styles(self, file_context):
        """Example implementation with basic styling"""
        file_rows = []

        # Assign the column styles
        column_styles = [
            {'stylename': 'col-default', 'defaultcellstylename': 'cell-default'},  # Header 1
            {'stylename': 'col-default', 'defaultcellstylename': 'cell-default'},  # Header 2
        ]

        # Headers
        file_rows.append({
            'cells': ['Header 1', 'Header 2'],
            'meta': {'name': 'header',
                     'row_styles': {'stylename': 'row-default'},
                     'cell_styles': {'stylename': 'cell-header'}},
        })

        # Data
        rows = [['Row 1, Column 1', 'Row 1, Column 2'], ['Row 2, Column 1', 'Row 2, Column 2']]
        for i, row in enumerate(rows):
            file_rows.append({
                'cells': row,
                'meta': {'name': 'row-{}'.format(i),
                         'row_styles': {'stylename': 'row-default'},
                         'cell_styles': {'stylename': 'cell-default'}},
            })

        return file_rows, column_styles

    def generate_csv_rows(self, file_context):
        """Must return a nested iterable of iterables containing the data to be written out to csv"""
        file_rows, _ = self.get_file_data_and_column_styles(file_context)

        return [row['cells'] for row in file_rows]

    def populate_styled_ods_with_data(self, spreadsheet, file_context):
        """Must return an instance of dmutils.ods.SpreadSheet populated with the required data."""
        file_rows, column_styles = self.get_file_data_and_column_styles(file_context)
        sheet = spreadsheet.sheet(file_context.get('sheetname', 'Sheet 1'))

        # Add the column styles
        for column_style in column_styles:
            sheet.create_column(**column_style)

        # Add the data
        for file_row in file_rows:
            row_name = file_row['meta'].get('name')
            write_row_kwargs = file_row['meta'].copy()
            del write_row_kwargs['name']

            sheet.write_row(name=row_name, cells=file_row['cells'], **write_row_kwargs)
