from dmutils.csv_generator import iter_csv


class TestIterCsv():
    def test_it_creates_csv_lines_from_lit_of_rows(self):
        rows = [
            ['a', 'b', 'c', 'd'],
            ['e', 'f', 'g', 'h']
        ]

        result = iter_csv(rows)
        lines = [line for line in result]

        assert lines[0] == b'a,b,c,d\r\n'
        assert lines[1] == b'e,f,g,h\r\n'
