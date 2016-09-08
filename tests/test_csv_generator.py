from dmutils.csv_generator import iter_csv


class TestIterCsv():
    def test_it_creates_csv_lines_from_list_of_rows(self):
        rows = [
            ['a', 'b', 'c', 'd'],
            ['e', u'\u00a3', 'g', 'h']
        ]

        result = iter_csv(rows)
        lines = [line for line in result]

        assert lines[0] == b'a,b,c,d\r\n'
        # NOTE this assertion relies on our encoding being utf8
        assert lines[1] == b'e,\xc2\xa3,g,h\r\n'
