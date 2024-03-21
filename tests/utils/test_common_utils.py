import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from model.configuration import Configuration
from utils import common_utils
from utils.common_utils import is_running_on_windows, pretty_print_bytes


class TestCommonUtils(unittest.TestCase):
    
    # region parse_configuration
    @patch('model.configuration.datetime', wrapper=datetime)
    def test_parse_configuration_with_success(self, mock_datetime) -> None:
        reference_datetime = datetime(2024, 2, 9, 1, 2, 3)
        mock_datetime.now = MagicMock(return_value=reference_datetime)

        expected_configuration = Configuration(
            process_name='pycharm',
            duration=3,
            sampling=1,
            reports_directory=Path('.'),
            logs_directory=Path('.'),
            reference_datetime=reference_datetime
        )
        
        argv = ['main.py', '-p', 'pycharm', '-d', '3', '-s', '1', '-r', '.', '-l', '.']
    
        with patch.object(sys, 'argv', argv):
            configuration = common_utils.parse_configuration()
            self.assertEqual(expected_configuration, configuration)

    @patch('model.configuration.datetime', wrapper=datetime)
    def test_parse_configuration_optional_sampling_with_success(self, mock_datetime) -> None:
        reference_datetime = datetime(2024, 2, 9, 1, 2, 3)
        mock_datetime.now = MagicMock(return_value=reference_datetime)
    
        expected_configuration = Configuration(
            process_name='pycharm',
            duration=60,
            sampling=5,
            reports_directory=Path('.'),
            logs_directory=Path('.'),
            reference_datetime=reference_datetime
        )
    
        argv = ['main.py', '-p', 'pycharm', '-d', '60', '-r', '.', '-l', '.']
    
        with patch.object(sys, 'argv', argv):
            configuration = common_utils.parse_configuration()
            self.assertEqual(expected_configuration, configuration)

    def test_parse_configuration_with_invalid_duration(self) -> None:
        argv = ['main.py', '-p', 'pycharm', '-d', 'invalid', '-r', '.', '-l', '.']
    
        with patch.object(sys, 'argv', argv):
            with self.assertRaises(SystemExit):
                common_utils.parse_configuration()
            
    def test_parse_configuration_with_invalid_sampling(self) -> None:
        argv = ['main.py', '-p', 'pycharm', '-d', '60', '-s', 'invalid', '-r', '.', '-l', '.']
    
        with patch.object(sys, 'argv', argv):
            with self.assertRaises(SystemExit):
                common_utils.parse_configuration()
    #endregion

    # region is_running_on_windows
    @patch('utils.common_utils.os', wrapper=os)
    def test_is_running_on_windows(self, mock_os) -> None:
        mock_os.name = 'nt'
        self.assertTrue(is_running_on_windows())

    @patch('utils.common_utils.os', wrapper=os)
    def test_is_running_on_linux(self, mock_os) -> None:
        mock_os.name = 'posix'
        self.assertFalse(is_running_on_windows())
    # endregion
    
    def test_pretty_print_bytes(self) -> None:
        self.assertEqual('10 Bytes', pretty_print_bytes(10))
        self.assertEqual('1.0 KB', pretty_print_bytes(1024))
        self.assertEqual('1.0 MB', pretty_print_bytes(1048576))
        self.assertEqual('1.0 GB', pretty_print_bytes(1073741824))
        self.assertEqual('1.0 TB', pretty_print_bytes(1099511627776))
        self.assertEqual('123.4 MB', pretty_print_bytes(129394278))



