import logging

from supplier.process_monitoring import ProcessMonitoring
from utils.common_utils import parse_configuration

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
root_logger.addHandler(console_handler)


def main():
    configuration = parse_configuration()

    log_handler = logging.FileHandler(configuration.log_path)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(log_handler)

    try:
        process_monitoring = ProcessMonitoring(configuration=configuration)
        process_monitoring.run()
    except RuntimeError as runtime_error:
        logging.error(str(runtime_error))
    except Exception as exception:
        logging.exception(str(exception))


if __name__ == '__main__':
    main()
