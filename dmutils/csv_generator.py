import unicodecsv


class _StringPipe(object):
    """
    A trivial implementation of something a bit like StringIO but acts more like a pipe than a file,
    flushing its output buffer when read. This way it can be used in lazy iteration for incremental output.
    """
    def __init__(self, initial_value=b""):
        self._contents = initial_value

    def write(self, line):
        self._contents += line

    def read(self):
        retval = self._contents
        self._contents = b""
        return retval


def iter_csv(row_iter, **kwargs):
    pipe = _StringPipe()
    writer = unicodecsv.writer(pipe, **kwargs)
    for row in row_iter:
        writer.writerow(row)
        yield pipe.read()
