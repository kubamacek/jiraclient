from config import get_configuration
from jira import JIRA
from prettytable import PrettyTable
import argparse
import sys
import logging


def setup_jira():
    """ Create and return JIRA object instance. """
    configuration = get_configuration()
    jira = JIRA(configuration['server'], auth=(configuration['user'], configuration['password']))
    return jira


def setup_logger():
    """ Create and return logger. """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def print_issues_list(issues):
    """ Use prettytable to print list of JIRA issues. """
    table = PrettyTable()
    table.field_names = ['Issue link', 'Issue summary']
    for issue in issues:
        data = issue.fields.summary
        summary = (data[:75] + '...') if len(data) > 75 else data
        table.add_row([issue.permalink(), summary])
    table.align = "l"
    print(table)


def print_daily_worklog_summary(worklogs_inventory, day, user):
    """ Use prettytable to print summary of logged work for particular day. """
    table = PrettyTable()
    table.field_names = ['Issue link', 'Logged time (hrs)']
    total_time = 0
    for issue, worklogs in worklogs_inventory.items():
        logged_time = 0
        for worklog in worklogs:
            if worklog.started.split('T')[0] == day and worklog.author.name == user:
                logged_time += worklog.timeSpentSeconds
                total_time += worklog.timeSpentSeconds
        table.add_row([issue, round(logged_time/3600, 2)])
    table.add_row(['Total', round(total_time/3600, 2)])
    table.align = "l"
    print(table)


def print_issue_info(issue):
    """ Use prettytable to print basic info about JIRA issue. """
    table = PrettyTable()
    table.field_names = ['Attribute', 'Value']
    table.add_row(['Key', issue.key])
    table.add_row(['URL', issue.permalink()])
    table.add_row(['Summary', issue.fields.summary])
    table.add_row(['Project', issue.fields.project.name])
    table.add_row(['Reporter', issue.fields.reporter.name])
    table.add_row(['Labels', issue.fields.labels])
    table.add_row(['Components', [component.name for component in issue.fields.components]])
    table.add_row(['Status', issue.fields.status.name])
    table.add_row(['Issue type', issue.fields.issuetype.name])
    table.add_row(['Description', issue.fields.description])
    table.align = "l"
    print(table)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--my-open-issues', action='store_true',
                        help='Show issues assigned to me.')
    parser.add_argument('-w', '--worklogs', nargs=1, metavar='day',
                        help='Show my worklogs for given day. \
                              Input date format: YYYY-MM-DD.')
    parser.add_argument('-l', '--issue-log-work', nargs=3, metavar=('issue', 'time', 'comment'),
                        help='Log work under given issue.')
    parser.add_argument('-i', '--issue', nargs='+', metavar='issue',
                        help='Show issue details.')
    parser.add_argument('-s', '--issue-search', nargs='+', metavar='query',
                        help='Search issues using JQL.')
    parser.add_argument('-c', '--issue-create', nargs=6,
                        metavar=('project-key', 'issue-type', 'summary',
                                 'labels', 'components', 'description'),
                        help='Create new issue. \
                              To pass multiple labels or components, separate them by comma.')
    parser.add_argument('-a', '--issue-assign', nargs=2,
                        metavar=('issue', 'assignee'),
                        help='Assign issue to given user.')
    parser.add_argument('--issue-comment', nargs=2, metavar=('issue', 'comment'),
                        help='Add a comment under given issue.')
    parser.add_argument('--issue-transition', nargs=2, metavar=('issue', 'state'),
                        help='Move issue to given state.')
    parser.add_argument('--issue-subtask', nargs=5,
                        metavar=('issue', 'summary', 'labels', 'components', 'description'),
                        help='Create a subtask for given issue.')
    parser.add_argument('--issue-review-subtask', nargs=3,
                        metavar=('issue', 'description', 'assignee'),
                        help='Create a review subtask for given issue. \
                              To create more subtasks, separate reviewers by comma.')
    parser.add_argument('--issue-review-task', nargs=3,
                        metavar=('issue', 'description', 'assignee'),
                        help='Create a review task for given issue. \
                              To create more tasks, separate reviewers by comma.')
    parser.add_argument('--issue-label-add', nargs=2, metavar=('issue', 'label'),
                        help='Add label for given issue.')
    parser.add_argument('--issue-label-remove', nargs=2, metavar=('issue', 'label'),
                        help='Remove label from given issue.')
    parser.add_argument('--issue-component-add', nargs=2, metavar=('issue', 'component'),
                        help='Add component for given issue.')
    parser.add_argument('--issue-component-remove', nargs=2, metavar=('issue', 'component'),
                        help='Remove component from given issue.')

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()
    jira = setup_jira()
    logger = setup_logger()

    if args.my_open_issues:
        logger.info("STARTED - print open issues")
        issues = jira.search_issues('resolution = Unresolved and assignee = {}'
                                    .format(jira.current_user()))
        print_issues_list(issues)
        logger.info("FINISHED")
        sys.exit(0)

    if args.worklogs:
        day = args.worklogs[0]
        logger.info("STARTED - print worklogs for {}".format(day))
        issues = jira.search_issues('workLogDate="{}" and workLogAuthor={}'
                                    .format(day, jira.current_user()),
                                    fields=['worklog'], maxResults=False)
        worklogs_inventory = {}
        for issue in issues:
            worklogs_inventory[issue.permalink()] = jira.worklogs(issue.id)
        print_daily_worklog_summary(worklogs_inventory, day, jira.current_user())
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_log_work:
        issue, time_spent, comment = args.issue_log_work
        logger.info("STARTED - log {} under {}".format(time_spent, issue))
        jira.add_worklog(issue=issue, timeSpent=time_spent, comment=comment)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue:
        key = args.issue[0]
        issue = jira.search_issues('key={}'.format(key))[0]
        print_issue_info(issue)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_search:
        query = args.issue_search[0]
        issues = jira.search_issues(query)
        print_issues_list(issues)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_assign:
        issue, assignee = args.issue_assign
        jira.assign_issue(issue=issue, assignee=assignee)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_comment:
        issue, comment = args.issue_comment
        jira.add_comment(issue=issue, body=comment)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_transition:
        issue, state = args.issue_transition
        jira.transition_issue(issue=issue, transition=state)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_create:
        project_key, issue_type, summary, labels, components, description = args.issue_create
        logger.info("STARTED - create new issue")
        issue = {
            'project': {'key': project_key},
            'issuetype': {'name': issue_type},
            'summary': summary,
            'description': description
        }
        if len(labels) > 0:
            issue['labels'] = labels.split(',')
        if len(components) > 0:
            issue['components'] = [{'name': c} for c in components.split(',')]
        new = jira.create_issue(fields=issue)
        print_issue_info(new)
        logger.info("FINISHED")

    if args.issue_subtask:
        issue, summary, labels, components, description = args.issue_subtask
        logger.info("STARTED - create subtask for {} issue".format(issue))
        issue = jira.issue(issue)
        subtask_dict = {
            'project': {'id': issue.fields.project.id},
            'issuetype': {'name': 'Sub-task'},
            'summary': summary,
            'description': description,
            'parent': {'key': issue.key}
        }
        if len(labels) > 0:
            subtask_dict['labels'] = labels.split(',')
        if len(components) > 0:
            subtask_dict['components'] = [{'name': c} for c in components.split(',')]
        subtask = jira.create_issue(fields=subtask_dict)
        print_issue_info(subtask)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_review_subtask:
        issue, description, assignees = args.issue_review_subtask
        issue = jira.issue(issue)
        assignees = assignees.split(',')
        for assignee in assignees:
            review_task_dict = {
                'project': {'id': issue.fields.project.id},
                'issuetype': {'name': 'Sub-task'},
                'summary': '[REVIEW] {}'.format(issue.fields.summary),
                'description': description,
                'labels': ['REVIEW'],
                'parent': {'key': issue.key},
                'assignee': {'name': assignee},
                'components': [{'name': component.name} for component in issue.fields.components]
            }
            logger.info("STARTED - create review subtask for {} under {} issue"
                        .format(assignee, issue.key))
            review_task = jira.create_issue(fields=review_task_dict)
            print_issue_info(review_task)
            jira.create_issue_link('is review for', review_task, issue)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_review_task:
        issue, description, assignees = args.issue_review_task
        issue = jira.issue(issue)
        assignees = assignees.split(',')
        for assignee in assignees:
            review_task_dict = {
                'project': {'id': issue.fields.project.id},
                'issuetype': {'name': 'Task'},
                'summary': '[REVIEW] {}'.format(issue.fields.summary),
                'description': description,
                'labels': ['REVIEW'],
                'assignee': {'name': assignee},
                'components': [{'name': component.name} for component in issue.fields.components]
            }
            logger.info("STARTED - create review task for {} under {} issue"
                        .format(assignee, issue.key))
            review_task = jira.create_issue(fields=review_task_dict)
            print_issue_info(review_task)
            jira.create_issue_link('is review for', review_task, issue)
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_label_add:
        issue, label = args.issue_label_add
        logger.info("STARTED - add {} label to {}".format(label, issue))
        issue = jira.issue(issue)
        issue.fields.labels.append(label)
        issue.update(fields={"labels": issue.fields.labels})
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_label_remove:
        issue, label_to_remove = args.issue_label_remove
        logger.info("STARTED - remove {} label from {}".format(label_to_remove, issue))
        issue = jira.issue(issue)
        if label_to_remove in issue.fields.labels:
            updated_labels = [label for label in issue.fields.labels if label != label_to_remove]
            issue.update(fields={"labels": updated_labels})
        else:
            logger.info("{} does not have {} label!".format(issue.key, label_to_remove))
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_component_add:
        issue, component_to_add = args.issue_component_add
        logger.info("STARTED - add {} component to {}".format(component_to_add, issue))
        issue = jira.issue(issue)
        issue_components = [{'name': component.name} for component in issue.fields.components]
        issue_components.append({'name': component_to_add})
        issue.update(fields={"components": issue_components})
        logger.info("FINISHED")
        sys.exit(0)

    if args.issue_component_remove:
        issue, component_to_remove = args.issue_component_remove
        logger.info("STARTED - remove {} component from {}".format(component_to_remove, issue))
        issue = jira.issue(issue)
        updated_components = [
            {'name': c.name}
            for c in issue.fields.components
            if c.name != component_to_remove
        ]
        issue.update(fields={"components": updated_components})
        logger.info("FINISHED")
        sys.exit(0)
