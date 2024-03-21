import logging
import time
from datetime import timedelta, datetime

import pandas as pd
import psutil
import schedule
from psutil import NoSuchProcess

from model.configuration import Configuration
from utils.common_utils import is_running_on_windows, pretty_print_bytes
from utils.date_utils import serialize_time


class ProcessMonitoring:

    def __init__(self, configuration: Configuration) -> None:
        self._configuration = configuration
        self._process = None
        self._is_running_on_windows = is_running_on_windows()
        self._dataframe = pd.DataFrame(columns=['timestamp', 'cpu_percent', 'private_memory', 'handles_fds'])

    def run(self) -> None:
        self._init()
        
        try:
            logging.info(f'Scheduling the monitoring for {self._configuration.duration} '
                         f'seconds with sampling every {self._configuration.sampling} seconds')
            
            schedule.every(
                self._configuration.sampling
            ).seconds.until(
                timedelta(seconds=self._configuration.duration)
            ).do(
                self._process_metrics
            )

            while True:
                if not schedule.jobs:
                    break
                
                schedule.run_pending()
                time.sleep(1)
        finally:
            self._persist()

    def _init(self) -> None:
        logging.info(f'Retrieve running process {self._configuration.process_name} information')
        for process in psutil.process_iter():
            if process.name() == self._configuration.process_name:
                self._process = psutil.Process(process.pid)
                self._process.cpu_percent()  # to init cpu percent cache to avoid 0 value.
                                             # Utilization measured since the last call to cpu_percent
                logging.info(f'Process has been found with PID {process.pid}')
                return
        raise RuntimeError(f'No running process {self._configuration.process_name} was found')
    
    def _process_metrics(self) -> None:
        logging.info('Retrieve process metrics')

        timestamp = datetime.now()
        
        try:
            cpu_percent = round(self._process.cpu_percent(), 2)
            private_memory = int(self._process.memory_full_info().uss)
            handles_fds = int(self._process.num_handles() if self._is_running_on_windows else self._process.num_fds())
        except NoSuchProcess:
            raise RuntimeError(f'Process {self._process.name} with pid {self._process.pid} '
                               f'is not running, application will stop')

        self._dataframe.loc[len(self._dataframe)] = {
            'timestamp': timestamp,
            'cpu_percent': cpu_percent,
            'private_memory': private_memory,
            'handles_fds': handles_fds,
        }

        average_metrics = self._dataframe.mean()
        
        # First metric output, we show the header first
        if (len(self._dataframe)) == 1:
            print('+----------+-------------------------+-------------------------+-------------------------+')
            print('+          |          CPU %          |          Memory         |       Handle / FDS      |')
            print('+   Time   +------------+------------+------------+------------+------------+------------+')
            print('+          |    AVG     |    CUR     |    AVG     |    CUR     |    AVG     |    CUR     |')
            print('+----------+------------+------------+------------+------------+------------+------------+')
       
        # We combine average and current metrics to compile them into an ascii table row
        metrics = [
            round(average_metrics['cpu_percent'], 2),
            cpu_percent,
            pretty_print_bytes(average_metrics['private_memory']),
            pretty_print_bytes(private_memory),
            int(average_metrics['handles_fds']),
            handles_fds
        ]
        output = '|' + serialize_time(timestamp).rjust(9, ' ') + ' |' \
                 + ' |'.join([str(metric).rjust(11, ' ') for metric in metrics]) + ' |'
        
        if self._has_potential_memory_leak():
            output += ' WARNING, potential memory leak detected'
        
        print(output)
        
    def _has_potential_memory_leak(self) -> bool:
        # We need at least 10 samples to detect a potential leak trend
        if len(self._dataframe) >= 10:
            memory_series = self._dataframe['private_memory']
            # is_monotonic_increasing will return True if all values are equals or increasing,
            # we add an additional check to skip if values stay the same for more than 33%
            return memory_series.is_monotonic_increasing and memory_series.nunique() > (len(self._dataframe) * 2/3)
           
        return False

    def _persist(self) -> None:
        logging.info(f'Persist results to {self._configuration.csv_report_path}')
        
        self._dataframe.to_csv(
            path_or_buf=self._configuration.csv_report_path,
            index=False
        )
