import argparse
import os
from pathlib import Path

from model.configuration import Configuration


def parse_configuration() -> Configuration:
    parser = argparse.ArgumentParser(description='Process resources monitoring application')
    parser.add_argument('-p', '--process', help='Process name', type=str, required=True)
    parser.add_argument('-d', '--duration', help='Overall duration of the monitoring (in seconds)', type=int, required=True)
    parser.add_argument('-s', '--sampling', help='Sampling interval (in seconds)', type=int, default=5)
    parser.add_argument('-r', '--reports-dir', help='Report directory to store CSV', type=str, default='output/reports')
    parser.add_argument('-l', '--logs-dir', help='Logs directory', type=str, default='output/logs')
    
    args = parser.parse_args()
    configuration = Configuration(
        process_name=args.process,
        duration=args.duration,
        sampling=args.sampling,
        reports_directory=Path(args.reports_dir),
        logs_directory=Path(args.logs_dir)
    )
    configuration.validate()
    
    return configuration


def is_running_on_windows() -> bool:
    return os.name == 'nt'


def pretty_print_bytes(bytes: float, bsize: int = 1024) -> str:
    mapping = {4: 'TB', 3: 'GB', 2: 'MB', 1: 'KB'}
    for size, unit in mapping.items():
        value = bytes / (bsize ** size)
        if int(value) > 0:
            return f'{round(value, 2)} {unit}'
    
    return f'{bytes} Bytes'
