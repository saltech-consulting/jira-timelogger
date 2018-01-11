from jira import JIRA

jira = JIRA(
    options={'server': 'http://localhost:8080'},
    basic_auth=('admin', 'admin'))

# Log time
issue = jira.issue('TEST-1')
jira.add_worklog(issue, '30m', comment="Automated worklog loader")

# Create subtask
subtask_fields = {
    'project': { 'key': 'TEST' },
    'summary': 'Test child auto created issue',
    'description': 'Ignore this child. will be deleted shortly',
    'issuetype' : { 'name': 'Sub-task' },
    'parent' : { 'id': 'TEST-1'}
}
subtask = jira.create_issue(fields=subtask_fields)
