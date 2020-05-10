import configparser
import os
import getpass
import argparse


CONFIG_PATH = os.path.expanduser('~/.jira_client/config.ini')


def get_configuration():
    configuration = {}
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    configuration['server'] = config.get('jira', 'server')
    configuration['user'] = config.get('jira', 'user')
    configuration['password'] = config.get('jira', 'password')
    return configuration


def create_configuration():
    if os.path.exists(CONFIG_PATH):
        print("WARNING: JIRA config exists and will be replaced.")
    server = input('JIRA server: ')
    user = input('Username: ')
    password = getpass.getpass(prompt='Password: ')
    config = configparser.ConfigParser()
    config['jira'] = {'server': server,
                      'user': user,
                      'password': password}
    with open(CONFIG_PATH, 'w') as config_file:
        config.write(config_file)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--create', action='store_true', required=True,
                        help="create new configuration file")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    if args.create:
        create_configuration()
