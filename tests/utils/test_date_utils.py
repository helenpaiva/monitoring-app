import unittest
from datetime import datetime

from utils.date_utils import serialize_datetime_to_file_format, serialize_time


class TestDateUtils(unittest.TestCase):
    
    def test_serialize_datetime_to_file_format(self) -> None:
        value = datetime(2024, 2, 9, 1, 2, 3)
        self.assertEqual('20240209010203', serialize_datetime_to_file_format(value))
        
    def test_serialize_time(self) -> None:
        value = datetime(2024, 2, 9, 21, 12, 3)
        self.assertEqual('21:12:03', serialize_time(value))
