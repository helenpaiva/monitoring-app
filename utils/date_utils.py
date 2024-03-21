from datetime import datetime


def serialize_datetime_to_file_format(value: datetime) -> str:
    return datetime.strftime(value, '%Y%m%d%H%M%S')


def serialize_time(value: datetime) -> str:
    return datetime.strftime(value, '%H:%M:%S')

