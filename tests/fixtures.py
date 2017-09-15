def get_file_data_and_column_styles():
    return ([{'cells': ['head 1', 'head 2'], 'meta': {'name': 'header'}},
             {'cells': ['data 1.1', 'data 1.2'], 'meta': {'name': 'row-1'}},
             {'cells': ['data 2.1', 'data 2.2'], 'meta': {'name': 'row-2',
                                                          'row_styles': 'row-default'}},
             {'cells': ['data 3.1', 'data 3.2'], 'meta': {'name': 'row-3', 'row_styles': 'row-default',
                                                          'cell_styles': 'cell-default'}}],
            [{'stylename': 'col-default'}, {'stylename': 'col-wide'}])


def get_expected_csv_response_for_download_file_view():
    return '"Heading 1","Heading 2"\r\n"Row 1, Column 1","Row 1, Column 2"\r\n'
