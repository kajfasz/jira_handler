import sqlite3 as lite
import mail_param
from c_logger import CustomLogger
from datetime import datetime as dt

log = CustomLogger('{0}_log_file.txt'.format(dt.now().date()))

def p_decorate(func):
    def func_wrapper(*args, **kwargs):
        log.debug("Running function {0} with number of arguments {1}".format(func.__name__, len(args) + len(kwargs)))
        return func(*args, **kwargs)
    return func_wrapper

@p_decorate
def put_sigle_row_into_table(issue_id, current_status, historical_status, issue_type, issue_name, db_file_name,
                             db_table, con=None, cur=None, notified=False):
    """
    :param issue_id:
    :param current_status:
    :param historical_status:
    :param issue_type:
    :param issue_name:
    :param db_file_name:
    :param db_table:
    :param con:
    :param cur:
    :param notified:
    :return:
    """
    created_inline = False
    if not con and not cur:
        cur, con = create_connection_to_db(db_file_name)
        created_inline = True
    try:
        cur.execute('INSERT INTO {0}("issue_id", "current_status", "historical_status", "notified", "issue_type", '
                    '"friendly_name") VALUES ({1}, "{2}", "{3}", "{4}", "{5}", "{6}");'.format(db_table, issue_id,
                                                                                               current_status,
                                                                                               historical_status,
                                                                                               notified, issue_type,
                                                                                               issue_name))
    except lite.IntegrityError:
        cur.execute('UPDATE {0} SET "current_status" = "{1}", "historical_status" = "{2}",'
                    '"issue_type" = "{5}", "friendly_name" = "{6}" WHERE "issue_id" = "{4}";'.format(db_table,
                                                                                                     current_status,
                                                                                                     historical_status,
                                                                                                     notified, issue_id,
                                                                                                     issue_type,
                                                                                                     issue_name))
    except:
        # create new table if the one with name not exists
        cur.execute('CREATE TABLE {0}("issue_id" INTEGER, "current_status", "historical_status", "notified", '
                    '"issue_type", "friendly_name", UNIQUE("issue_id"));'.format(db_table))
        cur.execute('INSERT INTO {0}("issue_id", "current_status", "historical_status", "notified", "issue_type", '
                    '"friendly_name") VALUES ({1}, "{2}", "{3}", "{4}", "{5}", "{6}");'.format(db_table, issue_id,
                                                                                               current_status,
                                                                                               historical_status,
                                                                                               notified, issue_type,
                                                                                               issue_name))
    if created_inline:
        con.commit()
    else:
        return con

@p_decorate
def update_notification_column(db_file_name, db_table_name, issue_id, notified=False):
    cur, con = create_connection_to_db(db_file_name)
    cur.execute('UPDATE {0} SET "notified" = "{1}" WHERE "issue_id" = "{2}";'.format(db_table_name, notified, issue_id))
    con.commit()

@p_decorate
def get_full_data_from_table(db_file_name, db_table_name):
    """
    :param db_file_name: path to db file
    :param db_table_name: name of table in db
    :return: data from db
    """
    cur, con = create_connection_to_db(db_file_name)
    cur.execute('SELECT * FROM {0};'.format(db_table_name))
    data = cur.fetchall()
    return data

@p_decorate
def get_data_with_issue_id(db_file_name, db_table_name, issue_id, cur=False, con=False):
    """
    :param db_file_name:
    :param db_table_name:
    :param issue_id:
    :return:
    """
    if not con and not cur:
        cur, con = create_connection_to_db(db_file_name)
    cur.execute('SELECT * FROM {0} WHERE "issue_id" = {1};'.format(db_table_name, issue_id))
    data = cur.fetchall()
    return data

@p_decorate
def get_data_for_notification(db_file_name, db_table_name):
    """
    :param db_file_name:
    :param db_table_name:
    :return:
    """
    cur, con = create_connection_to_db(db_file_name)
    cur.execute('SELECT * FROM {0} WHERE "current_status" = "done" AND "notified" = "False";'.format(db_table_name))
    data = cur.fetchall()
    return data

@p_decorate
def delete_row_from_table(db_file_name, db_table_name, line):
    """
    :param db_file_name: path to db file
    :param db_table_name: name of table in db
    :return: None
    """
    cur, con = create_connection_to_db(db_file_name)
    cur.execute('DELETE FROM {0} WHERE lines = "{1}";'.format(db_table_name, line))
    con.commit()


@p_decorate
def create_connection_to_db(db_file_name):
    """
    :param db_file_name: name of db file
    :return: cursor and connection objects
    """
    connection = lite.connect(db_file_name)
    cur = connection.cursor()
    return cur, connection

@p_decorate
def put_multiple_data_into_table(db_file_name, table_name, in_list, val_list, drop_db=False):
    """
    :param db_file_name:
    :param table_name:
    :param in_list:
    :param val_list:
    :param drop_db:
    :return:
    """
    cur, con = create_connection_to_db(db_file_name)
    if not drop_db:
        cur.execute('DELETE FROM {0};'.format(table_name))
    for line, value in zip(in_list, val_list):
        con = put_sigle_row_into_table(line, value, db_file_name, table_name, con, cur)
    con.commit()

@p_decorate
def generate_sql_input(file):
    """Temporary func to create input list from txt file
    :param file: name of file contains lines with mail intent
    :return: prepared text with " added on start and end
    """
    with open(file, 'r') as f:
        data = f.readlines()
    stripped_data = ['"{0}"'.format(item.strip()) for item in data]
    return stripped_data

# if __name__ == '__main__':
#     # put_sigle_row_into_table('12241', 'closed', 'candidate', mail_param.db_path, 'RECRUITT')
#     # print(get_data_for_notification(mail_param.db_path, 'RECRUITT'))
#     print(get_data_with_issue_id(mail_param.db_path, 'RECRUITT', '12241'))