from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from utils.date_utils import serialize_datetime_to_file_format


@dataclass
class Configuration:
    process_name: str
    duration: int
    sampling: int
    reports_directory: Path
    logs_directory: Path
    reference_datetime: datetime = field(default_factory=lambda: datetime.now())
    
    def validate(self) -> None:
        if self.sampling > self.duration:
            raise RuntimeError('The sampling interval should be lower than the total duration.')
        
        if not (self.reports_directory.exists() and self.reports_directory.is_dir()):
            raise RuntimeError(f'Report directory {self.reports_directory} does not exist or is not a valid directory.')
    
        if not (self.logs_directory.exists() and self.logs_directory.is_dir()):
            raise RuntimeError(f'Logs directory {self.logs_directory} does not exist or is not a valid directory.')
        
    @property
    def log_path(self) -> Path:
        return self.logs_directory.joinpath(f'{self.process_name}_{serialize_datetime_to_file_format(self.reference_datetime)}.log')
    
    @property
    def csv_report_path(self) -> Path:
        return self.reports_directory.joinpath(f'{self.process_name}_{serialize_datetime_to_file_format(self.reference_datetime)}.csv')