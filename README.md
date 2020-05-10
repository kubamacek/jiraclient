# jiraclient

Commandline tool to automate daily JIRA activities. Uses [jira-python](https://jira.readthedocs.io/en/master/) library.

## setup

Clone repo and install necessary libraries using pip.

> pip install -r requirements.txt

## usage

Type

> python jiraclient.py -h

to get help and read about possible actions.

## config.py

Script creates config file with JIRA credentials. 
Default folder for config file is `~/.jira_client/config.ini`.
Type

> python config.py -c

to create your configuration file.
