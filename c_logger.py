import datetime
import mail_param
import send_email
import time
import os
from hurry.filesize import size

levels = {'debug': ['debug', 'info', 'warning', 'error'],
          'info': ['info', 'warning', 'error'],
          'warning': ['warning', 'error'],
          'error': ['error']}

class CustomLogger(object):
    def __init__(self, to_file_path, log_level='info'):
        self.to_file_path = to_file_path
        self.log_level = log_level
        self.needed_logs = levels[log_level]

    def __put_log_into_file(self, message, mode='a', log_level="INF"):
        with open(self.to_file_path, mode) as log_f:
            full_message = "{0}\t{1}\t- {2}\n".format(datetime.datetime.now(), log_level, message)
            print(full_message[:-1])
            log_f.write(full_message)

    def debug(self, message):
        if 'debug' in self.needed_logs:
            self.__put_log_into_file(message, log_level="DBG")

    def info(self, message):
        if 'info' in self.needed_logs:
            self.__put_log_into_file(message, log_level="INF")

    def warning(self, message):
        if 'warning' in self.needed_logs:
            self.__put_log_into_file(message, log_level="WRN")

    def error(self, message):
        if 'error' in self.needed_logs:
            self.__put_log_into_file(message, log_level="ERR")

    def header(self, message):
        self.__put_log_into_file('*' * len(message), log_level="HDR")
        self.__put_log_into_file(message, log_level="HDR")
        self.__put_log_into_file('*' * len(message), log_level="HDR")

class LogParser(object):
    def __init__(self, log_file):
        self.delta_start = time.time()
        self.delta_end = 0
        self.log_file = log_file
        self.logs_file_content = self.get_file_content()
        self.first = len(self.logs_file_content)
        self.last = 0
        self.logs = list()
        self.log_file_size = 0

    def get_file_content(self):
        try:
            with open(self.log_file, 'r') as log_f:
                tmp_data = log_f.readlines()
            return tmp_data
        except FileNotFoundError:
            return ''

    def get_file_after_run(self):
        self.logs_file_content = self.get_file_content()
        self.last = len(self.logs_file_content)

    def get_logs_from_run(self):
        self.logs = self.logs_file_content[self.first: self.last]

    def get_size_of_current_log_file(self):
        st = os.stat(self.log_file)
        self.log_file_size = size(st.st_size)

    def close_run(self):
        parsing_logs_start = time.time()
        self.get_file_after_run()
        self.get_logs_from_run()
        self.get_size_of_current_log_file()
        readable_logs = ''
        for line in self.logs:
            readable_logs += line
        parsing_logs_delta = round(time.time() - parsing_logs_start)
        send_email.send_email(mail_content_json={"subject": "Logs from run jira script",
                                                 "content": "Run took: {0} secs (it contains log parsing: {1} secs)."
                                                            "\nLog file size: {2}\n\n{3}"
                                                            "".format(round(time.time() - self.delta_start, 2),
                                                                      parsing_logs_delta, self.log_file_size,
                                                                      readable_logs)},
                              mail_to_list=mail_param.mail_developer_to,
                              )


