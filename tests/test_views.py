from flask import Response
from werkzeug.exceptions import BadRequest

import mock
import pytest

from dmutils.views import DownloadFileView, SimpleDownloadFileView

import fixtures


class TestDownloadFileView():
    def setup(self):
        self._saved__abstract_methods__ = DownloadFileView.__abstractmethods__
        DownloadFileView.__abstractmethods__ = set()

        self.kwargs = {'arg1': 'foo', 'arg2': 'bar'}
        self.view = DownloadFileView()

        self._patch_determine_filetype = mock.patch.object(self.view, 'determine_filetype', autospec=True)
        self._patch_determine_filetype.start()
        self.view.determine_filetype.return_value = DownloadFileView.FILETYPES.ODS

        self._patch_get_file_context = mock.patch.object(self.view, 'get_file_context', autospec=True)
        self._patch_get_file_context.start()

        self._patch_create_response = mock.patch.object(self.view, 'create_response', autospec=True)
        self._patch_create_response.start()
        self.view.create_response.return_value = (Response(), 200)

        self._patch_init_hook = mock.patch.object(self.view, '_init_hook', autospec=True)
        self._patch_init_hook.start()

        self._patch_post_request_hook = mock.patch.object(self.view, '_post_request_hook', autospec=True)
        self._patch_post_request_hook.start()

    def teardown(self):
        DownloadFileView.__abstractmethods__ = DownloadFileView.__abstractmethods__

        for patch in [self._patch_determine_filetype, self._patch_get_file_context, self._patch_create_response,
                      self._patch_init_hook, self._patch_post_request_hook]:
            try:
                patch.stop()
            except RuntimeError:
                pass

    def test_abstract_methods_required_for_instantiation(self):
        DownloadFileView.__abstractmethods__ = self._saved__abstract_methods__

        with pytest.raises(TypeError) as e:
            DownloadFileView()

        assert str(e.value) == "Can't instantiate abstract class DownloadFileView with abstract methods " \
                               "_init_hook, determine_filetype, generate_csv_rows, get_file_context, " \
                               "populate_styled_ods_with_data"

    def test_create_blank_ods_with_styles(self):
        """Assert that, at a minimum, the styles exist."""
        spreadsheet = self.view.create_blank_ods_with_styles()

        style_names = ['col-default', 'col-wide', 'col-extra-wide',
                       'row-default', 'row-tall', 'row-tall-optimal',
                       'cell-default', 'cell-header']
        for style_name in style_names:
            assert spreadsheet._document.getStyleByName(str(style_name)) is not None

    def test_create_response_csv(self):
        kwargs = {'filename': 'test'}
        mimetype = "text/csv"
        content_type = "text/csv; header=present; charset=utf-8"

        self._patch_create_response.stop()

        res, status_code = self.view.create_response(kwargs, DownloadFileView.FILETYPES['CSV'])

        assert res.get_data(as_text=True) == fixtures.get_expected_csv_response_for_download_file_view()
        assert res.mimetype == mimetype
        assert res.headers['Content-Type'] == content_type
        assert res.headers['Content-Disposition'] == 'attachment;filename={}.csv'.format(kwargs['filename'])
        assert status_code == 200

    def test_create_response_ods(self):
        spreadsheet = self.view.create_blank_ods_with_styles()
        self._patch_create_blank_ods_with_styles = mock.patch.object(self.view, 'create_blank_ods_with_styles',
                                                                     autospec=True)
        self._patch_create_blank_ods_with_styles.start()
        self.view.create_blank_ods_with_styles.return_value = spreadsheet

        kwargs = {'filename': 'test', 'sheetname': 'sheet'}
        mimetype = "application/vnd.oasis.opendocument.spreadsheet"
        content_type = mimetype

        self._patch_create_response.stop()

        res, status_code = self.view.create_response(kwargs, DownloadFileView.FILETYPES['ODS'])

        # Can't test res.get_data() directly because the result is not fixed (i.e. some aspect of the file changes
        # based on creation time, so let's test the cells themselves.
        assert type(res) == Response
        assert bytes(mimetype, encoding='utf-8') in res.get_data()
        assert 1700 <= len(res.get_data()) <= 1800

        sheet = spreadsheet._sheets['sheet']
        assert sheet.read_cell(0, 0) == 'Heading 1'
        assert sheet.read_cell(1, 0) == 'Heading 2'
        assert sheet.read_cell(0, 1) == 'Row 1, Column 1'
        assert sheet.read_cell(1, 1) == 'Row 1, Column 2'

        assert res.mimetype == mimetype
        assert res.headers['Content-Type'] == content_type
        assert res.headers['Content-Disposition'] == 'attachment;filename={}.ods'.format(kwargs['filename'])
        assert status_code == 200

    def test_dispatch_request(self):
        result = self.view.dispatch_request(**self.kwargs)
        assert result is self.view.create_response.return_value

        assert self.view._init_hook.call_args_list == [mock.call(**self.kwargs)]
        assert self.view._post_request_hook.call_args_list == [mock.call(result, **self.kwargs)]

        assert self.view.get_file_context.call_args_list == [mock.call(**self.kwargs)]
        assert self.view.determine_filetype.call_args_list == [mock.call(self.view.get_file_context.return_value,
                                                                         **self.kwargs)]

    def test_dispatch_request_400s_on_unknown_filetype(self):
        self.view.determine_filetype.return_value = 'DOCX'

        with pytest.raises(BadRequest) as e:
            self.view.dispatch_request(**self.kwargs)

        assert e.value.code == 400


class TestSimpleDownloadFileView:
    def setup(self):
        self.fixture_data_styles = fixtures.get_file_data_and_column_styles()

        self._saved__abstract_methods__ = SimpleDownloadFileView.__abstractmethods__
        SimpleDownloadFileView.__abstractmethods__ = set()

        self.view = SimpleDownloadFileView()

        self._patch_get_file_data_and_column_styles = mock.patch.object(self.view, 'get_file_data_and_column_styles',
                                                                        autospec=True)
        self._patch_get_file_data_and_column_styles.start()
        self.view.get_file_data_and_column_styles.return_value = self.fixture_data_styles

    def teardown(self):
        SimpleDownloadFileView.__abstractmethods__ = SimpleDownloadFileView.__abstractmethods__

        for patch in [self._patch_get_file_data_and_column_styles]:
            try:
                patch.stop()
            except RuntimeError:
                pass

    def test_abstract_methods_required_for_instantiation(self):
        SimpleDownloadFileView.__abstractmethods__ = self._saved__abstract_methods__

        with pytest.raises(TypeError) as e:
            SimpleDownloadFileView()

        assert str(e.value) == "Can't instantiate abstract class SimpleDownloadFileView with abstract methods " \
                               "_init_hook, determine_filetype, get_file_context, get_file_data_and_column_styles"

    def test_generate_csv_rows(self):

        csv_rows = self.view.generate_csv_rows({})
        assert csv_rows == [row['cells'] for row in self.fixture_data_styles[0]]

    def test_populate_styled_ods_with_data(self):
        spreadsheet_mock = mock.Mock()
        spreadsheet_mock.sheet.return_value = sheet_mock = mock.Mock()

        self.view.populate_styled_ods_with_data(spreadsheet_mock, {})

        call_args_list = [mock.call(**styles) for styles in self.fixture_data_styles[1]]
        assert sheet_mock.create_column.call_count == len(self.fixture_data_styles[1])
        assert sheet_mock.create_column.call_args_list == call_args_list

        call_args_list = [mock.call(cells=row['cells'], **row.get('meta', {})) for row in self.fixture_data_styles[0]]
        assert sheet_mock.write_row.call_count == len(self.fixture_data_styles[0])
        assert sheet_mock.write_row.call_args_list == call_args_list
