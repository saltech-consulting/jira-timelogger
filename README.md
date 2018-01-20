# Jira TimeLogger

## Usage
```
python jira_timelogger.py timelog.csv
```

## Sample CSV
```
TEST-1,Task 1 summary,30m,2018-01-20T22:00:00.000+0100,user@company.com,Comment 1
TEST-1/+ADD1,Subtask 1 summary,10h 20m,2018-01-20T22:00:00.000+0100,user@company.com,Comment 2
```

## Fields
- Task ID: required
  - Jira issue key
  - Jira issue key + "/" + unique subtask ID
- Task summary: required for subtasks, optional (not used) for main issue
  - Custom string
- Time: required
  - Time in Jira's format, e.g. "30m" or "1h 10m"
- Start time: required
  - '%Y-%m-%dT%H:%M:%S.000%z' format
- User: required
  - Custom string, not validated. It will appear in the worklog comment.
- Comment: optional
  - Custom string
