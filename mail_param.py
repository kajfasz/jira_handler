
jira_rest_user = "tporeba"
jira_rest_pass = "xxx"
jira_rest_url = "https://jira.spyro-soft.com/rest/api/2"
jira_recruit_project_id = "10101"
jira_recruit_project_name = "RECRUITT"
jira_recruit_issue_type = "10200" #Recruiment process
jira_hr_project_id = "10200"
jira_hr_project_name = "HRT"
jira_hr_default_summary = "New default test task connected with {0}"
jira_hr_default_description = "New default test task description"
jira_hr_issuetype = "10002" #Task

mail_smtp_server_host = "serwer1635397.home.pl"
mail_smtp_server_port_ssl = "465"
mail_smtp_server_port_tsl = "587"
mail_smtp_server_user = "noreply@m.spyro-soft.com"
mail_smtp_server_pass = "xxx"
mail_from = "noreply@m.spyro-soft.com"
mail_to = ["tporeba@spyro-soft.com"]
mail_content_json = {"subject": "[JIRA %(recruit)s] Closed issue in %(recruit)s project and further actions"
                                % {'recruit': jira_recruit_project_name, 'hr': jira_hr_project_name},
                     "content": "Hello\n"
                                "Please be informed that issue {0} ({1}) in %(recruit)s project is closed now, "
                                "and there is created issue in %(hr)s project {2} ({3}) for this activity\n\n"
                                "Bye\n"
                                "Jira team" % {'recruit': jira_recruit_project_name, 'hr': jira_hr_project_name}}

mail_developer_to = ["tporeba@spyro-soft.com"]
db_path = "issues_db.db"

