import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from model.configuration import Configuration


class TestConfiguration(unittest.TestCase):

    def mock_report_path(self, exists: bool, is_dir: bool) -> Path:
        report_path = MagicMock()
        report_path.exists = MagicMock(return_value=exists)
        report_path.is_dir = MagicMock(return_value=is_dir)

        return report_path

    def mock_logs_path(self, exists: bool, is_dir: bool) -> Path:
        logs_path = MagicMock()
        logs_path.exists = MagicMock(return_value=exists)
        logs_path.is_dir = MagicMock(return_value=is_dir)

        return logs_path
    
    def test_validate_with_success(self) -> None:
        reports_path = self.mock_report_path(True, True)
        logs_path = self.mock_logs_path(True, True)
        configuration = Configuration(
            process_name='pycharm',
            duration=3,
            sampling=1,
            reports_directory=reports_path,
            logs_directory=logs_path
        )
        
        configuration.validate()
        
        reports_path.exists.assert_called_once()
        reports_path.is_dir.assert_called_once()
        logs_path.exists.assert_called_once()
        logs_path.is_dir.assert_called_once()
    
    def test_validate_with_greater_sampling(self) -> None:
        reports_path = self.mock_report_path(True, True)
        logs_path = self.mock_logs_path(True, True)

        configuration = Configuration(
            process_name='pycharm',
            duration=3,
            sampling=4,
            reports_directory=reports_path,
            logs_directory=logs_path
        )

        with self.assertRaises(RuntimeError):
            configuration.validate()
    
    def test_validate_with_invalid_logs_directory(self) -> None:
        reports_path = self.mock_report_path(True, True)
        logs_path = self.mock_logs_path(False, False)

        configuration = Configuration(
            process_name='pycharm',
            duration=3,
            sampling=1,
            reports_directory=reports_path,
            logs_directory=logs_path
        )

        with self.assertRaises(RuntimeError):
            configuration.validate()
    
    # def test_validate_with_invalid_reports_directory(self) -> None:
    #     reports_path = self.mock_report_path(False, False)
    #     logs_path = self.mock_logs_path(True, True)
    #
    #     configuration = Configuration(
    #         process_name='pycharm',
    #         duration=3,
    #         sampling=1,
    #         reports_directory=reports_path,
    #         logs_directory=logs_path
    #     )
    #
    #     with self.assertRaises(RuntimeError):
    #         configuration.validate()

    def test_validate_with_invalid_reports_directory(self) -> None:
        reports_path = self.mock_report_path(False, False)
        logs_path = self.mock_logs_path(True, True)

        configuration = Configuration(
            process_name='pycharm',
            duration=3,
            sampling=1,
            reports_directory=reports_path,
            logs_directory=logs_path
        )

        with self.assertRaises(RuntimeError):
            configuration.validate()

    def test_log_path_property(self) -> None:
        path = 'dir/subfolder'

        configuration = Configuration(
            process_name='pycharm',
            duration=None,
            sampling=None,
            reports_directory=None,
            logs_directory=Path(path),
            reference_datetime=datetime(2024, 2, 9, 16, 0)
        )

        self.assertEqual(Path('dir/subfolder/pycharm_20240209160000.log'), configuration.log_path)

    def test_csv_report_path(self) -> None:
        path = 'dir/subfolder'

        configuration = Configuration(
            process_name='pycharm',
            duration=None,
            sampling=None,
            reports_directory=Path(path),
            logs_directory=None,
            reference_datetime=datetime(2024, 2, 9, 16, 0)
        )

        self.assertEqual(Path('dir/subfolder/pycharm_20240209160000.csv'), configuration.csv_report_path)