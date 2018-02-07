import requests
import inspect
import mail_param
import re
import json
import time
from requests_exception import *
from send_email import send_email
from c_logger import CustomLogger, LogParser
import database_handler

# # tmp solution
# from rest_output import rest
LOG_FILE = '{0}_log_file.txt'.format(dt.now().date())
log = CustomLogger(LOG_FILE, log_level="info")

def p_decorate(func):
    def func_wrapper(*args, **kwargs):
        log.debug("Running function {0} with number of arguments {1}".format(func.__name__, len(args) + len(kwargs)))
        return func(*args, **kwargs)
    return func_wrapper

@p_decorate
def lineno():
    """Returns the current line number"""
    return inspect.currentframe().f_back.f_lineno

@p_decorate
def return_auth_data(input_auth):
    try:
        user = input_auth[0]
        passwd = input_auth[1]
    except IndexError:
        user = mail_param.jira_rest_user
        passwd = mail_param.jira_rest_pass
    return (user, passwd)

@p_decorate
def handle_with_rest(req_type, url, post_json=False, user=mail_param.jira_rest_user, passwd=mail_param.jira_rest_pass,
                     headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}, rerun=False):
    auth=(user, passwd)
    if req_type.lower() == 'get':
        log.debug("Processing GET request: {0}".format(url))
        resp = requests.get(url, auth=return_auth_data(auth))
    elif req_type.lower() == 'post':
        log.debug("Processing POST request: {0} with data: {1}".format(url, post_json))
        # print(url, '\n', post_json, '\n', headers, '\n', return_auth_data(auth))
        resp = requests.post(url, data=json.dumps(post_json), headers=headers, auth=return_auth_data(auth))
    else:
        raise NothingSpecialException()
    if not resp.status_code in [200, 403, 201]:
        if not rerun:
            log.warning("Got status code: {0}. Trying to connect second time do jira rest api! Wait 30 secs before."
                        "".format(resp.status_code))
            time.sleep(30)
            return handle_with_rest(req_type, url, post_json, user, passwd, headers, rerun=True)
        else:
            raise GetException('Program occurred unexpected error.', resp.status_code, url)
    elif resp.status_code == 403:
        issue_id_obj = re.search('issue/(\d+)', url)
        if issue_id_obj:
            issue_id = issue_id_obj.group(1)
        try:
            if not issue_id in get_all_issues_with_status('all', get_all_issues_with_project_name(mail_param.jira_recruit_project_name,
                                                user=mail_param.jira_rest_user, passwd=mail_param.jira_rest_pass)):
                raise GetException("There is no issue with id {0} (url: {1})".format(issue_id, url), resp.status_code)
            else:
                raise GetException("Authorization error! (url: {0})".format(url), resp.status_code)
        except NameError:
            raise ImplementationException('issue_id', 'Bad url: {0}'.format(url))
    else:
        return resp.json()

@p_decorate
def get_json_with_issue_number(issue_number, user=mail_param.jira_rest_user, passwd=mail_param.jira_rest_pass):
    return handle_with_rest(req_type='get', url='{0}/issue/{1}'.format(mail_param.jira_rest_url, issue_number), user=user, passwd=passwd)

@p_decorate
def post_request_to_jira(json_content, url,
                         user=mail_param.jira_rest_user, passwd=mail_param.jira_rest_pass):
    return handle_with_rest('post', '{0}/issue/'.format(url), user=user, passwd=passwd, post_json=json_content)

@p_decorate
def get_all_issues_with_project_name(project_name, *arg, user=mail_param.jira_rest_user, passwd=mail_param.jira_rest_pass):
    # print('{0}/search?jql=project={1}'.format(mail_param.jira_rest_url, project_name))
    return handle_with_rest('get', '{0}/search?jql=project={1}'.format(mail_param.jira_rest_url, project_name), user=user, passwd=passwd)
    # return rest

@p_decorate
def get_all_issues_with_status(status, all_issues_dict=False, project_name=mail_param.jira_recruit_project_name):
    if not all_issues_dict:
        all_issues_dict = get_all_issues_with_project_name(project_name)
    issues_with_status = list()
    for issue in all_issues_dict['issues']:
        status_from_rest = get_data_from_dict(issue, 'fields', 'status', 'name').lower()
        if status_from_rest == status.lower() or status == 'all':
            issues_with_status.append(get_data_from_dict(issue, 'id'))
    return issues_with_status

def get_data_from_dict(issue_dict, *keys):
    tmp = issue_dict
    for key in keys:
        try:
            tmp = tmp[key]
        except TypeError:
            tmp = None
    return tmp

@p_decorate
def send_default_mail(closed_issue_number, closed_issue_name, new_issue_name, new_issue_details):
    send_email(mail_param.mail_content_json, issue=closed_issue_number, issue_name=closed_issue_name,
               new_issue=new_issue_name, new_issue_details=new_issue_details)

class IssueObj(object):
    def __init__(self, issue_number, jira_user, jira_pass, update=False):
        self.id = issue_number
        self.jira_user, self.jira_pass = return_auth_data([jira_user, jira_pass])
        self.__full_issue_data = self.__get_issue_data()
        self.full_issue_name = self.__get_issue_key()
        self.rest_url = self.__get_issue_rest_url()
        self.reporter = self.__get_reporter_data()
        self.assignee = self.__get_assignee_data()
        self.status = self.__get_status()
        self.type = self.__get_issue_type()
        try:
            self.update_issue_with_db_data(con=False, cur=False)[0]
        except:
            self.update_issue_in_db()
        self.data_from_db = self.update_issue_with_db_data(con=False, cur=False)[0]
        self.current_status = self.data_from_db[1]
        self.historical_status = self.data_from_db[2]
        self.notified = self.data_from_db[3].lower() == "true"
        if update:
            self.update_issue_in_db()

    @p_decorate
    def __str__(self):
        return (self.type, self.id)

    @p_decorate
    def create_json_for_new_issue(self):
        tmp_json = {'fields': {
                        'project': {
                            'id': mail_param.jira_hr_project_id
                        },
                        'summary': mail_param.jira_hr_default_summary.format(self.full_issue_name),
                        'description': mail_param.jira_hr_default_description,
                        'issuetype': {
                            'id': mail_param.jira_hr_issuetype
                        }
        }}
        log.info("Prepared json with data for POST request: {0}".format(tmp_json))
        return tmp_json

    @p_decorate
    def update_issue_in_db(self):
        status_from_rest = get_data_from_dict(self.__full_issue_data, 'fields', 'status', 'name').lower()
        if status_from_rest.lower() == 'done':
            historical_state = 'candidate'
        elif status_from_rest.lower() == 'candidate':
            historical_state = 'new'
        else:
            if self.type == 'Candidate':
                log.warning('Unexpected status od issue {0}'.format(self.full_issue_name))
            historical_state = 'Unknown'
        database_handler.put_sigle_row_into_table(get_data_from_dict(self.__full_issue_data, 'id'),
                                                  status_from_rest,
                                                  historical_state, self.type, self.full_issue_name,
                                                  mail_param.db_path,
                                                  mail_param.jira_recruit_project_name)

    @p_decorate
    def update_issue_with_db_data(self, con=False, cur=False):
        return database_handler.get_data_with_issue_id(mail_param.db_path, mail_param.jira_recruit_project_name, self.id, con=con, cur=cur)

    @p_decorate
    def notify_watchers(self, response):

        send_default_mail(self.id, self.full_issue_name, response['key'], response['self'])
        database_handler.update_notification_column(mail_param.db_path, mail_param.jira_recruit_project_name, self.id,
                                                    notified=True)

    @p_decorate
    def create_hr_task(self):
        log.debug("Try to create new task in {0} project".format(mail_param.jira_hr_project_name))
        if not self.notified and self.current_status == 'done' and self.historical_status == 'candidate':
            json_content = self.create_json_for_new_issue()
            response = post_request_to_jira(json_content=json_content, url=mail_param.jira_rest_url,
                                            user=mail_param.jira_rest_user, passwd=mail_param.jira_rest_pass)
            # response = {'id': '12332', 'key': 'HRT-13', 'self': 'https://jira.spyro-soft.com/rest/api/2/issue/12332'}
            if response:
                log.info("Got response: {0}".format(response))
                self.notify_watchers(response)
                return response
            else:
                log.error("There was problem during creation new {0} task!".format(mail_param.jira_hr_project_name))
                mail_content = {"subject": "[JIRA ERROR] Creation new task!",
                                "content": "There was problem during creation new {0} task!"
                                           "".format(mail_param.jira_hr_project_name)}
                send_email(mail_content, issue=self.id)
        else:
            log.debug("There is no need to perform some action or watchers {0} already notified!"
                     "".format(mail_param.mail_to))

    def __get_issue_data(self):
        return get_json_with_issue_number(self.id, self.jira_user, self.jira_pass)

    def __get_issue_rest_url(self):
        return get_data_from_dict(self.__full_issue_data, "self")

    def __get_issue_key(self):
        return get_data_from_dict(self.__full_issue_data, "key")

    def __get_reporter_data(self):
        data_tmp_dict = {"username": get_data_from_dict(self.__full_issue_data, "fields", "reporter", "name"),
                         "mail_address": get_data_from_dict(self.__full_issue_data, "fields", "reporter", "emailAddress"),
                         "name": get_data_from_dict(self.__full_issue_data, "fields", "reporter", "displayName")}
        return data_tmp_dict

    def __get_assignee_data(self):
        data_tmp_dict = {"username": get_data_from_dict(self.__full_issue_data, "fields", "assignee", "name"),
                         "mail_address": get_data_from_dict(self.__full_issue_data, "fields", "assignee", "emailAddress"),
                         "name": get_data_from_dict(self.__full_issue_data, "fields", "assignee", "displayName")}
        return data_tmp_dict

    def __get_status(self):
        return get_data_from_dict(self.__full_issue_data, "fields", "status", "name")

    def __get_issue_type(self):
        return get_data_from_dict(self.__full_issue_data, "fields", "issuetype", "name")


class IssueObjManager(object):
    def __init__(self, jira_user, jira_pass, *issues, create_inline = False):
        self.issues = issues[0]
        self.jira_user, self.jira_pass = return_auth_data([jira_user, jira_pass])
        self.issues_objs_keeper = dict()
        if create_inline:
            self.create_objects_for_all_issues()

    @p_decorate
    def create_objects_for_all_issues(self):
        for issue_number in self.issues:
            self.issues_objs_keeper[issue_number] = IssueObj(issue_number, self.jira_user, self.jira_pass, update=True)
        log.info("Created {0} task objects for issues from {1} project"
                 "".format(len(self.issues_objs_keeper), mail_param.jira_recruit_project_name))

    @p_decorate
    def give_me(self, issue_number):
        if self.issues_objs_keeper and issue_number in self.issues_objs_keeper.keys():
            return self.issues_objs_keeper[issue_number]
        else:
            raise NothingSpecialException()

    @p_decorate
    def create_hr_tasks_for_all_objects(self):
        counter = 0
        for issue in self.issues_objs_keeper:
            tmp_response = self.issues_objs_keeper[issue].create_hr_task()
            if tmp_response:
                counter += 1
        log.info("Notified watchers about {0} created task(s) in {1} project"
                 "".format(counter, mail_param.jira_hr_project_name))
        return counter

def full_main_script():
    tmp_log_keeper = LogParser(LOG_FILE)
    log.header("*** Start jira_rest_api_handler script! ***")
    try:
        all_issues = get_all_issues_with_status('all')
        issue_objs = IssueObjManager(mail_param.jira_rest_user, mail_param.jira_rest_pass, all_issues)
        issue_objs.create_objects_for_all_issues()
        issue_objs.create_hr_tasks_for_all_objects()
    except:
        log.error("Script stop working. Email with collected data was send to developers {0}"
                  "".format(mail_param.mail_developer_to))
    log.header("*** End of jira_rest_api_handler script! ***")
    tmp_log_keeper.close_run()

if __name__ == '__main__':
    counter = 1
    while True:
        input('Waiting...')
        log.info("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ RUN {0}".format(counter))
        full_main_script()
        if counter >= 1:
            break
        counter += 1
