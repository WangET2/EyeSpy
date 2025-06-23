import csv
from datetime import datetime
from pathlib import Path

class OutputWriter:
    def __init__(self, direc: Path, header: list[str]):
        name = self._create_name()
        self._header = header
        self._filepath = direc / f'{name}.csv'
        self._file = None
        self._writer = None

    def __enter__(self):
        self._file = open(self._filepath, 'w', newline='')
        self._writer = csv.writer(self._file)
        self._writer.writerow(self._header)
        return self

    def write_row(self, data: list):
        self._writer.writerow(data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()

    def _create_name(self):
        current_time = datetime.now()
        return current_time.strftime('%m%d%y_%H%M%S')
