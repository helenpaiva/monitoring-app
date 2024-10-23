# Process Resources Monitoring Application

This project provides a console application for monitoring the resource usage of a specified process. The application gathers process metrics (CPU usage, private memory usage, open handles or file descriptors) over a specified duration, calculates averages and detects potential memory leaks.

## Installation

### Prerequisites:

- python >= 3.9
- pip

### Create a virtual environment:

```bash
python -m venv env
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows
```

### Install the requirements:

```bash
pip install -r requirements.txt
```

### Run the tests:

```bash
python -m unittest discover -v 
```

## Using the Application

```bash
python main.py -p <process_name> -d <duration_in_seconds> [-s <sampling_interval_in_seconds>] [-r <reports_dir>] [-l <logs_dir>]
```

Arguments:

```bash
-p, --process: Name of the process to monitor (required)
-d, --duration: Overall duration of the monitoring in seconds (required)
-s, --sampling: Sampling interval in seconds (optional, default: 5)
-r, --reports-dir: Directory to store csv  reports (optional, default: output/reports)
-l, --logs-dir: Directory to store logs (optional, default: output/logs)
```

> Please note that reports and logs directories should exist before executing the application.

Example:

```bash
python main.py -p chrome -d 20 -s 2 -r ./output/reports -l ./output/logs
```

## FAQ

#### Which platform is supported?

This application has been tested on Windows (Version 10) and Linux (Ubuntu 20).

### Which external libraries are used?

The application is using non-restricted licensed libraries [pandas](https://pypi.org/project/pandas/), [psutil](https://pypi.org/project/psutil/) and [schedule](https://pypi.org/project/schedule/).

### Which metrics are collected?

This application is using psutil to collect the process metrics. We are using the following methods from the library :

- **cpu_percent** to collect the percentage of CPU against all CPUs used by the process (percentage can be higher than 100).
- **memory_full_info.uss** (unique set size) to collect the private memory used by process (more information [here](https://gmpy.dev/blog/2016/real-process-memory-and-environ-in-python)).
- **num_handles** on Windows and **num_fds** on others platforms to obtain the number of open handlers/file descriptors used by process. 

#### How memory leak detection works?

The application requires at least 10 measures to be able to detect memory leak.

If the private memory usage has a monotonic increasing with no constant value for more than 66% of the time then the application will warn the user on the console output.

