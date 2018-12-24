#!/usr/bin/python
#-*-coding:utf-8-*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# All Rights Reserved.

# @author: Zhangyh, Inc.

#pip install python-gitlab

import gitlab

class GitlabHandler(object):
    def __init__(self, host, port, email, token):
        self.host = host
        self.port = port
        self.email = email
        self.token = token
        self.client = None
        return

    def connect(self):
        try:
            #Gitlab(self, url, private_token=None, oauth_token=None, email=None, password=None, ssl_verify=True, http_username=None, http_password=None, timeout=None, api_version='4', session=None, per_page=None)
            self.client = gitlab.Gitlab('{0}:{1}'.format(self.host, self.port), email = self.email, private_token = self.token, timeout = 60)
        except Exception as e:
            print 'connect gitlab [{0}:{1}] Exception: {2}'.format(self.host, self.port, e)
        return

    def is_project_exist(self, project_name, project_git):
        #https://docs.gitlab.com/ce/api/projects.html#list-all-projects check from project_name
        is_exist = False
        try:
            projects = self.client.projects.list(all=True)
            if len(projects) > 0:
                for item in projects:
                    if item.ssh_url_to_repo == project_git and item.path == project_name:
                        is_exist = True
                        break
                    else:
                        continue
        except Exception as e:
            print 'get project [{0}] Exception: {1}'.format(project_name, e)

        return is_exist

import sys

if __name__ == '__main__':
    gitlab_handler = GitlabHandler(host = 'https://git.xxxx.com', port = '443', email = 'admin@example.com', token = 'zyz1234asklaj')

    gitlab_handler.connect()
    is_exist1 = gitlab_handler.is_project_exist(project_name = 'admin-server', project_git = 'git://test.git')
    is_exist2 = gitlab_handler.is_project_exist(project_name = 'admin-ser', project_git = 'git@git.cloud.xxxx.com:snap/admin-server.git')
    is_exist = gitlab_handler.is_project_exist(project_name = 'admin-server', project_git = 'git@git.cloud.xxxx.com:snap/admin-server.git')

    print is_exist1, is_exist2, is_exist
    sys.exit(0)
