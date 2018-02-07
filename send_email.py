from smtplib import SMTP
import datetime
import mail_param

def send_email(mail_content_json, mail_to_list=mail_param.mail_to, timeout=10, debuglevel=0,
               smtp_host=mail_param.mail_smtp_server_host, smtp_port=mail_param.mail_smtp_server_port_tsl,
               smtp_user=mail_param.mail_smtp_server_user, smtp_passwd=mail_param.mail_smtp_server_pass,
               mail_from=mail_param.mail_from, issue='99999', issue_name='XXX', new_issue='XXX',
               new_issue_details='XXX'):

    smtp = SMTP(timeout=timeout)
    smtp.set_debuglevel(debuglevel)
    smtp.connect(smtp_host, smtp_port)
    smtp.login(smtp_user, smtp_passwd)

    subj = mail_content_json['subject']
    date = datetime.datetime.now().strftime( "%d/%m/%Y %H:%M" )
    try:
        message_text = mail_content_json['content'].format(issue, issue_name, new_issue, new_issue_details)
    except:
        message_text = mail_content_json['content']

    msg = "From: {0}\nTo: {1}\nSubject: {2}\nDate: {3}\n\n{4}".format(mail_from, mail_to_list, subj, date, message_text )

    smtp.sendmail(mail_param.mail_from, mail_param.mail_to, msg)
    smtp.quit()