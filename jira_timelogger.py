import sys
import getpass
import csv
from datetime import datetime
from jira import JIRA
from jira.exceptions import JIRAError

import config

class TimeLogger:
    log_entry_format = '{}, {}, {}, {}'

    def __init__(self, server_options):
        self._server_options = server_options

    def initalize(self):
        user = input('User: ')
        password = getpass.getpass('Password: ')
        print()

        self._jira = JIRA(
            options=self._server_options,
            basic_auth=(user, password))

    def log_from_csv(self, path):
        self._failures = []

        with open(path) as timelog_file:
            timelog_reader = csv.reader(timelog_file, delimiter=',', quotechar='"')
            for timelog_row in timelog_reader:
                issue_key, summary, time, started, user, comment = timelog_row
                self.log_task(issue_key, summary, time, started, user, comment)

        print()
        if self._failures:
            print('Failures:')
            for failure in self._failures:
                print(failure)
        else:
            print('Success')

    def log_task(self, issue_key, summary, time, started, user, comment):
        self._subtask_dictionary = {}

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
        print(log_entry, end='', flush=True)

        try:
            self._log_task()
            print(' - OK', flush=True)
        except JIRAError as e:
            print(' - Failed', flush=True)
            self._failures.append('{} - {}'.format(log_entry, e.text))
        except:
            print(' - Failed', flush=True)
            self._failures.append('{} - {}'.format(log_entry, 'Unexpected error'))

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

###############################################################################

if len(sys.argv) < 2:
    print('Supply the log file path in the first argument')
else:
    timelog_path = sys.argv[1]
    time_logger = TimeLogger(config.SERVER_OPTIONS)
    time_logger.initalize()
    time_logger.log_from_csv(timelog_path)
