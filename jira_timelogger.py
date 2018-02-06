import logging
import sys
import os
import errno
import shutil
import getpass
from glob import glob
from datetime import datetime
from jira import JIRA
from jira.exceptions import JIRAError

import config
from time_logger import TimeLogger, TimeLoggerError


def create_dir_if_not_exit(directory):
    try:
        logging.debug('Creating directory: {}'.format(directory))
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logging.error('Unexpected error while creating directory: {}'.format(e))

def try_to_move_file(from_path, to_path):
    try:
        logging.debug('Moving {} to {}'.format(from_path, to_path))
        create_dir_if_not_exit(os.path.dirname(to_path))
        shutil.move(from_path, to_path)
    except IOError as e:
        logging.error('IOError while moving file: {}'.format(e))
    except Exception as e:
        logging.error('Unexpected error while moving file: {}'.format(e))

# Current run directory
time_suffix = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
run_dir_current = os.path.join(config.RUN_DIR, time_suffix)
run_dir_success = os.path.join(run_dir_current, 'success')
run_dir_error = os.path.join(run_dir_current, 'error')
run_dir_log = os.path.join(run_dir_current, 'timelogger.log')

# Create run directory
os.makedirs(run_dir_current)

# Set up logging to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=run_dir_log,
                    filemode='w')

# Define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# Set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# Tell the handler to use this format
console.setFormatter(formatter)
# Add the handler to the root logger
logging.getLogger('').addHandler(console)

# Start
logging.debug('Start')

# Get user credentials
user = input('User: ')
logging.debug('User: {}'.format(user))
password = getpass.getpass('Password: ')
print()

# Create Jira object
try:
    jira = JIRA(
        options=config.SERVER_OPTIONS,
        basic_auth=(user, password))
except JIRAError as e:
    logging.error('JIRAError: {}'.format(e.text))
    logging.debug('JIRAError: {}'.format(e))
    sys.exit(1)

has_error = False

# Create a TimeLogger instance
time_logger = TimeLogger(jira)

# Read timelog csv files
timelog_file_glob = os.path.join(config.WORK_DIR, '*.csv')
timelog_files = glob(timelog_file_glob)
for timelog_file in timelog_files:
    try:
        time_logger.log_from_csv(timelog_file)
        try_to_move_file(
            timelog_file,
            os.path.join(run_dir_success, os.path.basename(timelog_file)))
    except TimeLoggerError as e:
        has_error = True
        try_to_move_file(
            timelog_file,
            os.path.join(run_dir_error, os.path.basename(timelog_file)))
    except Exception as e:
        has_error = True
        logging.error('Unexpected error: {}'.format(e))

# Set exit status
if has_error:
    logging.error('Finished with errors')
    sys.exit(2)
else:
    logging.info('Finished with success')
    sys.exit(0)
