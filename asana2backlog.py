import sys
import os
import asana
import urllib.request
from pybacklogpy.BacklogConfigure import BacklogComConfigure
from pybacklogpy.Issue import Issue, IssueType, IssueComment
from pybacklogpy.CustomField import CustomField
from pybacklogpy.Category import Category
from pybacklogpy.Priority import Priority
from pybacklogpy.Project import Project
from pybacklogpy.User import User
from pybacklogpy.Attachment import Attachment
from pybacklogpy.Status import Status

# Get information from args
asana_project_id = sys.argv[1]
asana_pat = sys.argv[2]

backlog_space_name = sys.argv[3]
backlog_api_key = sys.argv[4]
backlog_project_key = sys.argv[5]

PRIORITY_HIGH = '優先度: 高'
PRIORITY_MIDDLE = '優先度: 中'
PRIORITY_LOW = '優先度: 低'

STATUS_MITAIOU = 'Inbox'
STATUS_TODO = 'ToDo'
STATUS_TODO2 = 'To-Do'
STATUS_SHORICHU = 'In Progress'
STATUS_KANRYO = 'Completed'

# utility function
def search_from_json_list(target_json, search_key, search_word, return_key):
    item = next((item for item in target_json if item[search_key] == search_word), None)
    if item:
        return item[return_key]
    return None

# Setup API access
print('--- API setup')
asana_client = asana.Client.access_token(asana_pat)
backlog_config = BacklogComConfigure(space_key=backlog_space_name, api_key=backlog_api_key)
backlog_project_api = Project(backlog_config)
backlog_issue_api = Issue(backlog_config)
backlog_issue_type_api = IssueType(backlog_config)
backlog_issue_comment_api = IssueComment(backlog_config)
backlog_custom_field_api = CustomField(backlog_config)
backlog_priority_api = Priority(backlog_config)
backlog_user_api = User(backlog_config)
backlog_category_api = Category(backlog_config)
backlog_attachment_api = Attachment(backlog_config)
backlog_status_api = Status(backlog_config)

# Collect necessary info
backlog_project = backlog_project_api.get_project(backlog_project_key).json()
backlog_project_id = backlog_project['id']
backlog_task_issue_type_id = search_from_json_list(backlog_issue_type_api.get_issue_type_list(backlog_project_key).json(), 'name', 'タスク', 'id')

# Create user mapping
print('--- Create user mapping')
user_gid_mapping = {}
asana_workspace_gid = asana_client.projects.get_project(asana_project_id)['workspace']['gid']
asana_users = asana_client.users.get_users({'workspace': asana_workspace_gid})
backlog_users = backlog_user_api.get_user_list().json()
for asana_user in asana_users:
    asana_user_detail = asana_client.users.get_user(asana_user['gid'])
    backlog_user_id = search_from_json_list(backlog_users, 'mailAddress', asana_user_detail['email'], 'id')
    print(asana_user_detail['name'] + ': ' + str(backlog_user_id))
    user_gid_mapping[asana_user['gid']] = backlog_user_id

# Create priority mapping
print('--- Create priority mapping')
priority_list = backlog_priority_api.get_priority_list().json()
priority_map = {}
priority_map[PRIORITY_HIGH] = search_from_json_list(priority_list, 'name', '高', 'id')
priority_map[PRIORITY_MIDDLE] = search_from_json_list(priority_list, 'name', '中', 'id')
priority_map[PRIORITY_LOW] = search_from_json_list(priority_list, 'name', '低', 'id')

# Create status mapping
# At this moment, pybacklogpy does not provied status list api.
status_map = {}
status_map[STATUS_MITAIOU] = 1
status_map[STATUS_TODO] = XXXXX # set your original status id
status_map[STATUS_SHORICHU] = 2
status_map[STATUS_KANRYO] = 4

# Create custom field mapping
print('--- Create custom field mapping')
categories = backlog_category_api.get_category_list(backlog_project_key).json()
tags = search_from_json_list(backlog_custom_field_api.get_custom_field_list(backlog_project_key).json(), 'name', 'タグ', 'items')

processed_tasks = {}

def add_task(the_task_gid, backlog_parent_issue_id):
    the_task = asana_client.tasks.get_task(the_task_gid)
    if the_task_gid in processed_tasks:
        return

    print(the_task['name'])

    processed_tasks[the_task_gid] = the_task

    # assignee
    assignee = None
    if the_task['assignee'] is not None and the_task['assignee']['gid'] in user_gid_mapping:
        assignee = user_gid_mapping[the_task['assignee']['gid']]

    # set priority
    priority_string = search_from_json_list(the_task['custom_fields'], 'name', '優先度', 'display_value')
    if priority_string is not None:
        priority_id = priority_map[priority_string]
    else:
        priority_id = priority_map[PRIORITY_MIDDLE]

    # set category
    category_string = search_from_json_list(the_task['custom_fields'], 'name', 'カテゴリー', 'display_value')
    if category_string is not None:
        category_id = [ search_from_json_list(categories, 'name', category_string, 'id') ]
    else:
        category_id = []

    # set custom fields
    tag_setting = search_from_json_list(the_task['custom_fields'], 'name', 'タグ', 'multi_enum_values')
    if tag_setting is not None:
        tag_values = [ search_from_json_list(tags, 'name', ts['name'], 'id') for ts in tag_setting ]
    else:
        tag_values = []

    goal_setting = search_from_json_list(the_task['custom_fields'], 'name', 'ゴール設定', 'display_value')

    added_issue = backlog_issue_api.add_issue(
        project_id = backlog_project_id,
        summary =  the_task['name'],
        parent_issue_id = backlog_parent_issue_id,
        assignee_id = assignee,
        description = the_task['notes'],
        issue_type_id = backlog_task_issue_type_id,
        priority_id = priority_id,
        category_id = category_id,
        due_date = the_task['due_on'],
        customField_XXXXXX = tag_values,  # set your custom field
        customField_YYYYYY = goal_setting).json()

    # add comment to the issue
    added_issue_id = added_issue['id']
    stories = asana_client.stories.get_stories_for_task(the_task_gid)
    for story in stories:
        if story['type'] == 'comment':
            backlog_issue_comment_api.add_comment(added_issue_id, story['text'])

    # add attachement for the issue
    attachment_ids = []
    attachments = asana_client.attachments.get_attachments_for_task(the_task_gid)
    for attachment in attachments:
        attachment_detail = asana_client.attachments.get_attachment(attachment['gid'])
        fileurl = attachment_detail['download_url']
        filename = attachment_detail['name']
        urllib.request.urlretrieve(fileurl, filename)

        post_file_info = backlog_attachment_api.post_attachment_file(filename, filename).json()
        if 'id' in post_file_info:
            post_file_id = post_file_info['id']
            attachment_ids.append(post_file_id)
            os.remove(filename)
        else:
            print('upload error: ' + filename)
    
    if len(attachment_ids) > 0:
        backlog_issue_api.update_issue(added_issue_id, attachment_id = attachment_ids)

    if the_task['memberships'] is not None and len(the_task['memberships']) > 0:
        status_id = status_map[the_task['memberships'][0]['section']['name']]
        if status_id != 1:
            backlog_issue_api.update_issue(added_issue_id, status_id = status_id)

    # add sub issues for the issue
    backlog_parent_issue_id = backlog_parent_issue_id or added_issue_id
    sub_tasks = asana_client.tasks.get_subtasks_for_task(the_task_gid)
    for sub_task in sub_tasks:
        sub_task_gid = sub_task['gid']
        add_task(sub_task_gid, backlog_parent_issue_id)

print('--- Migrate tasks')
the_project_tasks = asana_client.tasks.get_tasks_for_project(asana_project_id)
for the_task in the_project_tasks:
    the_task_gid = the_task['gid']
    add_task(the_task_gid, None)
