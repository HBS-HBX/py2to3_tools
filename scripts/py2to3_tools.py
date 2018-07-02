#!/usr/bin/env python

import os 
import shutil
import argparse
import pprint
import sys
import pip
import json
import requests
from distutils.version import LooseVersion
from cStringIO import StringIO

parser = argparse.ArgumentParser(
    description='Find out if the packages used in your project are Python3 compatible.'
)
parser.add_argument(
    '--action',
    dest='action',
    default='search',
    help='Possible actions are "search" (default) and "create_ansible_roles". The \'search\' action will look through all your project dependent packages for py3 versions. The \'create_ansible_roles\' action will create ansible roles to test the packages provided in the \'--names\' argument. The \'--names\' argument is required for the \'create_ansible_roles\' action. '
)
parser.add_argument(
    '--version_count',
    dest='version_count',
    default=2,
    help='The number of latest py2 and py3 versions to return (default is 2)'
)
parser.add_argument(
    '--names',
    dest='names',
    help='A comma separated list of PyPI package names (eg. --names "Django, Pillow, django-rest-framework"). If provided, this list will override the list of names provided by running the pip list command.'
)

pp = pprint.PrettyPrinter(indent=4)

processing = True
def process(**kwargs):
    action = kwargs.get("action")
    names_str = kwargs.get("names")

    if names_str:
        names_str = names_str.replace(" ", "")
        kwargs["names"] = names_str.split(",")

    if action == "search":
        print "Searching for py3 packages in your project"
        search(**kwargs)
    elif action == "create_ansible_roles":
        if not kwargs.get("names"):
            print "Use the '--names' argument to provide the names of the packages you want to create roles for"
            return

        print "Creating the ansible roles to test the packages in your project for py3 compliance"
        create_ansible_roles(**kwargs)

def create_ansible_roles(**kwargs):
    """
    Step 1: Use the jinja2 templates to create dynamic ansible roles/playbook
    Step 2: Run newly created playbook to create virtualenv of package and test
    """
    names = kwargs.get("names")

    # Importing here so you can run search method without jinja2 install
    from jinja2 import Environment, FileSystemLoader

    root_dir = os.path.dirname(os.path.realpath(__file__))
    ansible_dir = "%s/../%s" % (root_dir.rstrip("/"), "/ansible")
    venv_dir = "%s/virtualenvs" % ansible_dir
    roles_dir = "%s/roles" % venv_dir
    template_dir = "%s/templates" % venv_dir
    playbook_file_path = "%s/test_sources.yml" % ansible_dir

    try:
        # Remove roles directory
        shutil.rmtree(roles_dir)
    except OSError as e:
        pass

    try:
        # Recreate roles directory
        os.makedirs(roles_dir)
    except OSError as e:
        raise

    jinja2_env = Environment(
        loader=FileSystemLoader(template_dir),
    )

    venv_task_template = jinja2_env.get_template('tasks_for_virtualenv.yml.j2')
    test_task_template = jinja2_env.get_template('tasks_for_test_sources.yml.j2')
    playbook_template = jinja2_env.get_template('test_playbook.yml.j2')

    entries = []
    vagrant_root_dir = "/home/ubuntu/virtualenvs"
    for name in names:
        sys.stdout.write(".")
        sys.stdout.flush()

        clean_name = name.lower().replace("-", "_")
        entry = {
            "clean_name": clean_name,
            "project_name": name,
            "root_dir": vagrant_root_dir
        }

        venv_tasks_dir = "%s/%s/tasks" % (roles_dir, clean_name)
        venv_templates_dir = "%s/%s/templates" % (roles_dir, clean_name)
        venv_test_sources_file_path_src = "%s/test_sources.py.j2" % template_dir
        venv_test_sources_file_path_dest = "%s/test_sources.py.j2" % venv_templates_dir
        venv_file_path = "%s/main.yml" % venv_tasks_dir

        test_tasks_dir = "%s/%s_test_sources/tasks" % (roles_dir, clean_name)
        test_file_path = "%s/main.yml" % test_tasks_dir

        try:
            os.makedirs(venv_tasks_dir)
            os.makedirs(venv_templates_dir)
            os.makedirs(test_tasks_dir)
        except OSError as e:
            raise

        shutil.copyfile(venv_test_sources_file_path_src, venv_test_sources_file_path_dest)

        file = open(venv_file_path, "w")
        file.write(venv_task_template.render(**entry))
        file.close()

        file = open(test_file_path, "w")
        file.write(test_task_template.render(**entry))
        file.close()
 
        entries.append(entry)

    # Write playbook file
    file = open(playbook_file_path, "w")
    file.write(playbook_template.render(**{"entries": entries}))
    file.close()

    print "\nDone creating ansible roles"

def search(**kwargs):
    version_count = int(kwargs.get("version_count"))
    names = kwargs.get("names")

    pip_entries = []
    no_py3_found = []

    old_stdout = sys.stdout
    sys.stdout = pip_stdout = StringIO()
    pip.main(['list', '--format', 'json'])
    sys.stdout = old_stdout

    pip_list_string = pip_stdout.getvalue()
    pip_list = json.loads(pip_list_string)

    pip_dict = {v.get("name").lower(): v for v in pip_list}

    if names:
        names_lowered = []
        for name in names:
            name_lowered = name.lower()
            names_lowered.append(name_lowered)
            if name_lowered not in pip_dict.keys():
                pip_list.append({"name": name, "version": "Not installed"})

        pip_list2 = pip_list
        pip_list = []
        for entry in pip_list2:
            if entry.get("name").lower() in names_lowered:
                pip_list.append(entry)

    for entry in pip_list:
        sys.stdout.write(".")
        sys.stdout.flush()
        dist_tags = {}
        py2_versions = []
        py3_versions = []

        name = entry.get("name")

        url = "https://pypi.python.org/pypi/%s" % name

        response = requests.get("%s/json" % url)

        pip_entry = {
            "name": name,
            "current_version": entry.get("version"),
            "url": url,
            "response_code": response.status_code,
        }

        if response.status_code == 200:

            r_json = response.json()

            info = r_json.get("info")
            version = info.get("version")
            for classifier in info.get("classifiers", []):
                if "Python :: 2" in classifier \
                        and version not in py2_versions:
                    py2_versions.append(version)
                if "Python :: 3" in classifier \
                        and version not in py3_versions:
                    py3_versions.append(version)

            # Get versions from dict keys
            versions = r_json.get("releases", {}).keys()

            # Sort versions based on LooseVersion numbering
            versions.sort(key=LooseVersion, reverse=True)
            for v in versions:

                for release in r_json.get("releases").get(v):
                    rv = release.get("python_version")
                    dist_tags[rv] = 1

                    is_py2 = False
                    is_py3 = False

                    if len(py2_versions) < version_count:
                        if rv.startswith("2."):
                            is_py2 = True
                        elif rv.startswith("cp2"):
                            is_py2 = True
                        elif "py2" in rv:
                            is_py2 = True

                        if is_py2 and v not in py2_versions:
                            py2_versions.append(v)

                    if len(py3_versions) < version_count:
                        if rv.startswith("3."):
                            is_py3 = True
                        elif rv.startswith("cp3"):
                            is_py3 = True
                        elif "py3" in rv:
                            is_py3 = True

                        if is_py3 and v not in py3_versions:
                            py3_versions.append(v)

                    if len(py2_versions) >= version_count \
                            and len(py3_versions) >= version_count:
                        break

        pip_entry["py2_versions"] = py2_versions
        pip_entry["py3_versions"] = py3_versions
        pip_entry["dist_tags"] = dist_tags.keys()

        if not py3_versions:
            no_py3_found.append(pip_entry)

        pip_entries.append(pip_entry)

    print ""
    if no_py3_found:
        print "Here is a report of the libraries with no py3 versions. You may need to manually check the source code to see if it's py3 compatible."
        pp.pprint(no_py3_found)
    else:
        print "It looks like all your python libraries have py3 versions"

    print ""
    print "Here is the detailed report:"
    pp.pprint(pip_entries)

if __name__ == '__main__':
    args = vars(parser.parse_args())
    process(**args)
