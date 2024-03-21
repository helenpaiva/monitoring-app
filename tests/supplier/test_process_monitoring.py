import copy
import unittest
from datetime import timedelta, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, call, PropertyMock

import numpy as np
import pandas as pd
import psutil
from pandas._testing import assert_frame_equal
from psutil import NoSuchProcess

from model.configuration import Configuration
from supplier.process_monitoring import ProcessMonitoring


class TestProcessMonitoring(unittest.TestCase):
    
    def setUp(self) -> None:
        self._configuration = Configuration(
            process_name='pycharm',
            duration=3,
            sampling=1,
            reports_directory=Path('output/reports'),
            logs_directory=Path('output/logs'),
            reference_datetime=datetime(2024, 2, 10, 17, 1, 2)
        )
        self._process_monitoring = ProcessMonitoring(configuration=self._configuration)
    
    # region run
    def test_run(self) -> None:
        # Mock
        self._configuration.sampling = 2
        self._configuration.duration = 7
        
        self._process_monitoring._init = MagicMock()
        self._process_monitoring._process_metrics = MagicMock()
        self._process_monitoring._persist = MagicMock()
 
        # Run
        self._process_monitoring.run()
        
        # Assert
        self._process_monitoring._init.assert_called_once()
        self._process_monitoring._process_metrics.assert_has_calls(calls=[
            call(),
            call(),
            call()
        ])
        self._process_monitoring._persist.assert_called_once()

    def test_run_with_exception(self) -> None:
        # Mock
        self._configuration.sampling = 2
        self._configuration.duration = 7
    
        self._process_monitoring._init = MagicMock()
        self._process_monitoring._process_metrics = MagicMock(side_effect=[None, RuntimeError('An error occurred')])
        self._process_monitoring._persist = MagicMock()
    
        # Run
        with self.assertRaisesRegex(RuntimeError, 'An error occurred'):
            self._process_monitoring.run()
    
        # Assert
        self._process_monitoring._init.assert_called_once()
        self._process_monitoring._process_metrics.assert_has_calls(calls=[
            call(),
            call()
        ])
        self._process_monitoring._persist.assert_called_once()
    # endregion run

    # region _init
    @patch('supplier.process_monitoring.psutil', wrapper=psutil)
    def test_init(self, mock_psutil) -> None:
        # Mock
        process_a_mock = MagicMock()
        process_a_mock.name = MagicMock(return_value='process_a')

        process_b_mock = MagicMock()
        process_b_mock.name = MagicMock(return_value='process_b')
        
        process_pycharm_mock = MagicMock()
        process_pycharm_mock.name = MagicMock(return_value='pycharm')
        process_pycharm_mock.pid = 1234
        
        process_mock = MagicMock()
        process_mock.cpu_percent = MagicMock()
        
        mock_psutil.process_iter = MagicMock(return_value=[process_a_mock, process_b_mock, process_pycharm_mock])
        mock_psutil.Process = MagicMock(return_value=process_mock)
        
        # Run
        self._process_monitoring._init()
        
        # Assert
        self.assertEqual(process_mock, self._process_monitoring._process)
        mock_psutil.process_iter.assert_called_once()
        mock_psutil.Process.assert_called_once_with(process_pycharm_mock.pid)
        process_mock.cpu_percent.assert_called_once()

    @patch('supplier.process_monitoring.psutil', wrapper=psutil)
    def test_init_with_process_not_found(self, mock_psutil) -> None:
        # Mock
        process_a_mock = MagicMock()
        process_a_mock.name = MagicMock(return_value='process_a')
    
        process_b_mock = MagicMock()
        process_b_mock.name = MagicMock(return_value='process_b')
    
        mock_psutil.process_iter = MagicMock(return_value=[process_a_mock, process_b_mock])
        mock_psutil.Process = MagicMock()
    
        # Run
        with self.assertRaisesRegex(RuntimeError, 'No running process pycharm was found'):
            self._process_monitoring._init()
    
        # Assert
        self.assertIsNone(self._process_monitoring._process)
        mock_psutil.process_iter.assert_called_once()
        mock_psutil.Process.assert_not_called()
    # endregion _init

    # region _process_metrics
    @patch('supplier.process_monitoring.datetime', wrapper=datetime)
    @patch('builtins.print')
    def test_process_metrics_first_call(self, mock_print, mock_datetime) -> None:
        # Mock
        now = datetime(2024, 2, 10, 17, 20, 40)
        mock_datetime.now = MagicMock(return_value=now)
        
        self._process_monitoring._is_running_on_windows = False
        
        self._process_monitoring._process = MagicMock()
        self._process_monitoring._process.cpu_percent = MagicMock(return_value=10.551)
        self._process_monitoring._process.memory_full_info = MagicMock()
        type(self._process_monitoring._process.memory_full_info.return_value).uss = PropertyMock(return_value=20971520.00)
        self._process_monitoring._process.num_fds = MagicMock(return_value=30.0)
        self._process_monitoring._process.num_handles = MagicMock()
        
        # Run
        self._process_monitoring._process_metrics()
        
        # Assert
        dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([(now, 10.55, 20971520, 30)])  # 20971520 is 20 MB
        )
        assert_frame_equal(dataframe, self._process_monitoring._dataframe, check_dtype=False)
        
        mock_print.assert_has_calls(calls=[
            call('+----------+-------------------------+-------------------------+-------------------------+'),
            call('+          |          CPU %          |          Memory         |       Handle / FDS      |'),
            call('+   Time   +------------+------------+------------+------------+------------+------------+'),
            call('+          |    AVG     |    CUR     |    AVG     |    CUR     |    AVG     |    CUR     |'),
            call('+----------+------------+------------+------------+------------+------------+------------+'),
            call('| 17:20:40 |      10.55 |      10.55 |    20.0 MB |    20.0 MB |         30 |         30 |')
        ])

        self._process_monitoring._process.cpu_percent.assert_called_once_with()
        self._process_monitoring._process.memory_full_info.assert_called_once_with()
        self._process_monitoring._process.num_fds.assert_called_once_with()
        self._process_monitoring._process.num_handles.assert_not_called()
        
    @patch('supplier.process_monitoring.datetime', wrapper=datetime)
    @patch('builtins.print')
    def test_process_metrics_n_call(self, mock_print, mock_datetime) -> None:
        # Mock
        now = datetime(2024, 2, 10, 17, 20, 40)
        mock_datetime.now = MagicMock(return_value=now)
        
        dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([
                (now - timedelta(seconds=10), 10.00, 10485760, 100),  # 10485760 is 10 MB
                (now - timedelta(seconds=5), 20.00, 20971520, 200),  # 20971520 is 20 MB
            ])
        )
    
        self._process_monitoring._is_running_on_windows = False
        self._process_monitoring._dataframe = copy.deepcopy(dataframe)
    
        self._process_monitoring._process = MagicMock()
        self._process_monitoring._process.cpu_percent = MagicMock(return_value=30.00)
        self._process_monitoring._process.memory_full_info = MagicMock()
        type(self._process_monitoring._process.memory_full_info.return_value).uss = PropertyMock(return_value=31457280.00)
        self._process_monitoring._process.num_fds = MagicMock(return_value=300.0)
        self._process_monitoring._process.num_handles = MagicMock()
    
        # Run
        self._process_monitoring._process_metrics()
    
        # Assert
        dataframe.loc[2] = [now, 30.00, 31457280, 300]  # 31457280 is 30 MB
        assert_frame_equal(dataframe, self._process_monitoring._dataframe, check_dtype=False)
        
        mock_print.assert_called_once_with(
            '| 17:20:40 |       20.0 |       30.0 |    20.0 MB |    30.0 MB |        200 |        300 |'
        )

        self._process_monitoring._process.cpu_percent.assert_called_once_with()
        self._process_monitoring._process.memory_full_info.assert_called_once_with()
        self._process_monitoring._process.num_fds.assert_called_once_with()
        self._process_monitoring._process.num_handles.assert_not_called()

    @patch('supplier.process_monitoring.datetime', wrapper=datetime)
    @patch('builtins.print')
    def test_process_metrics_on_windows(self, mock_print, mock_datetime) -> None:
        # Mock
        now = datetime(2024, 2, 10, 17, 20, 40)
        mock_datetime.now = MagicMock(return_value=now)
    
        self._process_monitoring._is_running_on_windows = True
    
        self._process_monitoring._process = MagicMock()
        self._process_monitoring._process.cpu_percent = MagicMock(return_value=10.551)
        self._process_monitoring._process.memory_full_info = MagicMock()
        type(self._process_monitoring._process.memory_full_info.return_value).uss = PropertyMock(return_value=20971520.00)
        self._process_monitoring._process.num_fds = MagicMock()
        self._process_monitoring._process.num_handles = MagicMock(return_value=30.0)
    
        # Run
        self._process_monitoring._process_metrics()
    
        # Assert
        dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([(now, 10.55, 20971520, 30)])  # 20971520 is 20 MB
        )
        assert_frame_equal(dataframe, self._process_monitoring._dataframe, check_dtype=False)
    
        mock_print.assert_has_calls(calls=[
            call('+----------+-------------------------+-------------------------+-------------------------+'),
            call('+          |          CPU %          |          Memory         |       Handle / FDS      |'),
            call('+   Time   +------------+------------+------------+------------+------------+------------+'),
            call('+          |    AVG     |    CUR     |    AVG     |    CUR     |    AVG     |    CUR     |'),
            call('+----------+------------+------------+------------+------------+------------+------------+'),
            call('| 17:20:40 |      10.55 |      10.55 |    20.0 MB |    20.0 MB |         30 |         30 |')
        ])

        self._process_monitoring._process.cpu_percent.assert_called_once_with()
        self._process_monitoring._process.memory_full_info.assert_called_once_with()
        self._process_monitoring._process.num_fds.assert_not_called()
        self._process_monitoring._process.num_handles.assert_called_once_with()
        
    @patch('builtins.print')
    def test_process_metrics_with_process_not_running(self, mock_print) -> None:
        # Mock
        self._process_monitoring._process = MagicMock()
        self._process_monitoring._process.name = 'pycharm'
        self._process_monitoring._process.pid = 1234
        self._process_monitoring._process.cpu_percent = MagicMock(side_effect=NoSuchProcess(1234))
        
        # Run
        with self.assertRaisesRegex(RuntimeError, 'Process pycharm with pid 1234 is not running, application will stop'):
            self._process_monitoring._process_metrics()
    
        # Assert
        self.assertEqual(0, len(self._process_monitoring._dataframe))
        mock_print.assert_not_called()

    @patch('supplier.process_monitoring.datetime', wrapper=datetime)
    @patch('builtins.print')
    def test_process_metrics_with_potential_memory_leak(self, mock_print, mock_datetime) -> None:
        # Mock
        now = datetime(2024, 2, 10, 17, 20, 40)
        mock_datetime.now = MagicMock(return_value=now)
    
        dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([
                (now - timedelta(seconds=10), 10.00, 10485760, 100),  # 10485760 is 10 MB
                (now - timedelta(seconds=5), 20.00, 20971520, 200),  # 20971520 is 20 MB
            ])
        )
    
        self._process_monitoring._is_running_on_windows = False
        self._process_monitoring._dataframe = copy.deepcopy(dataframe)
        self._process_monitoring._has_potential_memory_leak = MagicMock(return_value=True)
    
        self._process_monitoring._process = MagicMock()
        self._process_monitoring._process.cpu_percent = MagicMock(return_value=30.00)
        self._process_monitoring._process.memory_full_info = MagicMock()
        type(self._process_monitoring._process.memory_full_info.return_value).uss = PropertyMock(
            return_value=31457280.00)
        self._process_monitoring._process.num_fds = MagicMock(return_value=300.0)
        self._process_monitoring._process.num_handles = MagicMock()
    
        # Run
        self._process_monitoring._process_metrics()
    
        # Assert
        dataframe.loc[2] = [now, 30.00, 31457280, 300]  # 31457280 is 30 MB
        assert_frame_equal(dataframe, self._process_monitoring._dataframe, check_dtype=False)
    
        mock_print.assert_called_once_with(
            '| 17:20:40 |       20.0 |       30.0 |    20.0 MB |    30.0 MB |        200 |        300 | WARNING, potential memory leak detected'
        )
    
        self._process_monitoring._process.cpu_percent.assert_called_once_with()
        self._process_monitoring._process.memory_full_info.assert_called_once_with()
        self._process_monitoring._process.num_fds.assert_called_once_with()
        self._process_monitoring._process.num_handles.assert_not_called()
    # endregion
    
    # region _has_potential_memory_leak
    def test_has_potential_memory_leak_with_too_few_samples(self) -> None:
        self._process_monitoring._dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([
                (None, 0, 1000, 0),
                (None, 0, 2000, 0),
                (None, 0, 3000, 0),
                (None, 0, 4000, 0),
                (None, 0, 5000, 0),
                (None, 0, 6000, 0),
                (None, 0, 7000, 0),
                (None, 0, 8000, 0),
                (None, 0, 9000, 0),
            ])
        )
        self.assertFalse(self._process_monitoring._has_potential_memory_leak())
    
    def test_has_potential_memory_leak_with_constant_value(self) -> None:
        self._process_monitoring._dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0)
            ])
        )
        self.assertFalse(self._process_monitoring._has_potential_memory_leak())

    def test_has_potential_memory_leak_with_partial_increase_trend(self) -> None:
        self._process_monitoring._dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 1000, 0),
                (None, 0, 2000, 0),
                (None, 0, 3000, 0),
                (None, 0, 4000, 0),
                (None, 0, 5000, 0)
            ])
        )
        self.assertFalse(self._process_monitoring._has_potential_memory_leak())

    def test_has_potential_memory_leak_with_increase_trend(self) -> None:
        self._process_monitoring._dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([
                (None, 0, 1000, 0),
                (None, 0, 2000, 0),
                (None, 0, 2000, 0),
                (None, 0, 2000, 0),
                (None, 0, 3000, 0),
                (None, 0, 4000, 0),
                (None, 0, 5000, 0),
                (None, 0, 6000, 0),
                (None, 0, 7000, 0),
                (None, 0, 8000, 0),
                (None, 0, 9000, 0),
                (None, 0, 9000, 0)
            ])
        )
        self.assertTrue(self._process_monitoring._has_potential_memory_leak())
    
    def test_has_potential_memory_leak_without_increase_trend(self) -> None:
        self._process_monitoring._dataframe = pd.DataFrame(
            columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'],
            data=np.array([
                (None, 0, 1000, 0),
                (None, 0, 2000, 0),
                (None, 0, 2000, 0),
                (None, 0, 2000, 0),
                (None, 0, 3000, 0),
                (None, 0, 4000, 0),
                (None, 0, 3000, 0),
                (None, 0, 6000, 0),
                (None, 0, 7000, 0),
                (None, 0, 8000, 0),
                (None, 0, 9000, 0),
                (None, 0, 9000, 0)
            ])
        )
        self.assertFalse(self._process_monitoring._has_potential_memory_leak())
    # endregion

    # region _persist
    def test_persist(self) -> None:
        # Mock
        self._process_monitoring._dataframe = MagicMock()
        self._process_monitoring._dataframe.to_csv = MagicMock()
        
        # Run
        self._process_monitoring._persist()
        
        # Assert
        self._process_monitoring._dataframe.to_csv.assert_called_once_with(
            path_or_buf=Path('output/reports/pycharm_20240210170102.csv'),
            index=False
        )
    # endregion
