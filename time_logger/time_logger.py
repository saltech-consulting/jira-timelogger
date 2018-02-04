import logging
import csv
from datetime import datetime
from jira.exceptions import JIRAError

from time_logger import TimeLoggerError


class TimeLogger:
    log_entry_format = '{}, {}, {}, {}'

    def __init__(self, jira):
        self._jira = jira
        self._subtask_dictionary = {}

    def log_from_csv(self, path):
        self._csv_path = path
        self._has_error = False

        self._try_log_from_csv()

        if self._has_error:
            raise TimeLoggerError()

    def _try_log_from_csv(self):
        try:
            logging.info('Logging from: {}'.format(self._csv_path))
            with open(self._csv_path) as timelog_file:
                timelog_reader = csv.reader(timelog_file, delimiter=',', quotechar='"')
                for timelog_row in timelog_reader:
                    self._try_log_row_from_csv(timelog_row)
        except IOError as e:
            self._has_error = True
            logging.error('IOError: {}'.format(e))
        except Exception as e:
            self._has_error = True
            logging.error('Unexpected error: {}'.format(e))

    def _try_log_row_from_csv(self, timelog_row):
        try:
            logging.debug('Logging row: {}'.format(timelog_row))
            issue_key, summary, time, started, user, comment = timelog_row
            self._log_task_from_row(issue_key, summary, time, started, user, comment)
        except ValueError as e:
            self._has_error = True
            logger.error('Wrong format: {}'.format(e))
        except Exception as e:
            self._has_error = True
            logging.error('Unexpected error: {}'.format(e))

    def _log_task_from_row(self, issue_key, summary, time, started, user, comment):
        self._issue_key = issue_key
        self._summary = summary
        self._time = time
        self._started = datetime.strptime(started, '%Y-%m-%dT%H:%M:%S.000%z')
        self._user = user
        self._comment = comment

        self._try_to_log_task()

    def _try_to_log_task(self):
        log_entry = self.log_entry_format.format(
            self._issue_key, self._summary, self._time, self._started, self._comment)
        logging.info('Logging entry: {}'.format(log_entry))

        try:
            self._log_task()
            logging.info('OK')
        except JIRAError as e:
            self._has_error = True
            logging.error('JIRAError: {}'.format(e.text))
            logging.debug('JIRAError: {}'.format(e))
        except Exception as e:
            self._has_error = True
            logging.error('Unexpected error: {}'.format(e))

    def _log_task(self):
        comment = 'Automated worklog loader ({})'.format(self._user)
        if self._comment:
            comment += ': {}'.format(self._comment)

        if '/' in self._issue_key:
            issue = self._find_or_create_subtask()
        else:
            issue = self._jira.issue(self._issue_key)

        self._jira.add_worklog(
            issue, self._time, started=self._started, comment=comment)

    def _find_or_create_subtask(self):
        if self._issue_key in self._subtask_dictionary:
            return self._subtask_dictionary[self._issue_key]

        main_issue_key, sub_issue_id = self._issue_key.split('/')
        subtasks = self._jira.search_issues('parent=' + main_issue_key)
        for subtask in subtasks:
            if subtask.fields.summary.startswith(sub_issue_id):
                self._subtask_dictionary[self._issue_key] = subtask.key
                return self._jira.issue(self._subtask_dictionary[self._issue_key])

        return self._create_subtask(main_issue_key, sub_issue_id)

    def _create_subtask(self, main_issue_key, sub_issue_id):
        main_issue = self._jira.issue(main_issue_key)

        subtask_fields = {
            'project': { 'key': main_issue.fields.project.key },
            'summary': sub_issue_id + ': ' + self._summary,
            'description': 'Automatically created by worklog loader',
            'issuetype' : { 'name': 'Sub-task' },
            'parent' : { 'id': main_issue_key }
        }
        subtask = self._jira.create_issue(fields=subtask_fields)

        self._subtask_dictionary[self._issue_key] = subtask.key
        return subtask
