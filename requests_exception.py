from requests import status_codes as sc
from c_logger import CustomLogger
from datetime import datetime as dt

log = CustomLogger('{0}_log_file.txt'.format(dt.now().date()))

class RestException(Exception):
    def __init__(self, direction, message, *args):
        self.direction = direction.upper()
        self.message = message
        if args:
            self.status_code = int(args[0][0])
            try:
                self.url = args[0][1]
            except KeyError:
                self.url = ''
            http_message_for_code = sc._codes[self.status_code]
            self.message += '\tStatus code: {0} - {1}\n{2}' \
                            ''.format(self.status_code, http_message_for_code[0].upper(), self.url)

        log.error(self.message)
        Exception.__init__(self, self.message)

class GetException(RestException):
    def __init__(self, message, *args):
        # log.error(message + str(args))
        super(GetException, self).__init__('get', message, args)

class PostException(RestException):
    def __init__(self, message, *args):
        # log.error(message + str(args))
        super(PostException, self).__init__('post', message, args)

class NotImplementedException(Exception):
    def __init__(self, method, line_number):
        message = "There is not implemented path in line {0} in {1} method".format(line_number, method)
        log.error(message)
        Exception.__init__(self, message)

class ImplementationException(Exception):
    def __init__(self, name_, *message):
        tmp_message = "There was problem with method/variable {0}. {1}".format(name_, message[0])
        log.error(tmp_message)
        Exception.__init__(self, tmp_message)

class NothingSpecialException(Exception):
    def __init__(self, message="There are wrong input values for this action!"):
        log.error(message)
        Exception.__init__(self, message)
