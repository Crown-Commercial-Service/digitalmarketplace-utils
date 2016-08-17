import unicodecsv


def iter_csv(rows):

    class Line(object):
        def __init__(self):
            self._line = None

        def write(self, line):
            self._line = line

        def read(self):
            return self._line

    line = Line()
    writer = unicodecsv.writer(line)
    for row in rows:
        writer.writerow(row)
        yield line.read()
