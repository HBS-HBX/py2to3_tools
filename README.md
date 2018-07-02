# Python 2 to 3 Tools

This script will help you find python3 compatible packages in your project.

## How to use

Activate your project's virtual environment and then run the following commands.

```
git clone https://github.com/HBS-HBX/py2to3_tools.git

cd py2to3_tools

python scripts/py2to3_tools.py

```

```
# For help run
python scripts/py2to3_tools.py -h
```

```
# To find out if specific packages are py3 compatible enter comma separated list of packages to the --names option
python py2to3_tools.py --names "Pillow, django" --version_count 5
```

## Results

The script will print a JSON that looks like

```

[   {   'current_version': u'3.0',
        'dist_tags': [u'source'],
        'name': u'celery-with-redis',
        'py2_versions': [],
        'py3_versions': [],
        'response_code': 200,
        'url': u'https://pypi.python.org/pypi/celery-with-redis'},
    {   'current_version': u'1.4b5',
        'dist_tags': [u'source'],
        'name': u'django-easymode',
        'py2_versions': [u'0.14.5'],
        'py3_versions': [],
        'response_code': 200,
        'url': u'https://pypi.python.org/pypi/django-easymode'},
    {   'current_version': u'0.1.3',
        'dist_tags': [],
        'name': u'django-elastic-migrations',
        'py2_versions': [],
        'py3_versions': [],
        'response_code': 404,
        'url': u'https://pypi.python.org/pypi/django-elastic-migrations'},
    {   'current_version': u'0.5.6',
        'dist_tags': [u'py2.py3', u'source', u'2.7'],
        'name': u'XlsxWriter',
        'py2_versions': [u'1.0.5', u'1.0.4'],
        'py3_versions': [u'1.0.5', u'1.0.4'],
        'response_code': 200,
        'url': u'https://pypi.python.org/pypi/XlsxWriter'}
]

```

Here is a listing of the fields and what they mean:

- current_version: This is the current version installed in your project
- dist_tags: This is a list of the PEP 425 tags found in the pypi distribution
- name: The name of the package
- py2_versions: The list of py2 versions found on pypi. Limit this list via the '--version_count' option.
- py3_versions: The list of py3 versions found on pypi. Limit this list via the '--version_count' option.
- response_code: The script searches pypi for this package. It will return a 404 if it wasn't found.
- url: The package's pypi URL

## How it works

This script searches https://pypi.python.org for the package. If it is not found (i.e. you get a 404 in the response_code field) then this script cannot help you. You will need to manually determine if the package is python3 compatible.

If the package is found on pypi then the script will look in the dist_tags information provided in the package's setup file. If the package developer provided the appropriate tags for python3 then the script will mark this as python3 compatible.

Read more about PEP 425 here: https://www.python.org/dev/peps/pep-0425/

## What to do when the pypi package has no python3 information

As mentioned above, this script will only work if the package developer remembers to provide the python3 PEP 425 tags in the **dist_tags** field.

If the developer does not provide this information then the **py3_versions** field will be empty.

For instance, in the example provided above, the *django-easymode* package has an empty **py3_versions** field but that does not mean it is not python3 compatible. It just means the developer may not have provided the appropriate tags so it is up to you to test the source code in a python3 environment.

## Testing packages

Follow these steps to use vagrant and ansible to test one or more packages for python3 compatibility.

- Setup vagrant.
- Use ansible to deploy python3 vagrant environment.
- Use py2to3_tools to create ansible roles for testing packages.
- Run ansible playbook to test sources.


#### Setup vagrant 

```
# Step 1
cd /path/to/py2to3_tools

# Step 2
# id_rsa.pub, which is gitignored, is needed by vagrant
cat ~/.ssh/id_rsa.pub > id_rsa.pub

# Step 3
# Vagrantfile is gitignored
cp Vagrantfile.example Vagrantfile

# Step 4
vagrant up
```

#### Use ansible to deploy python3 vagrant environment

```
# Step 1
cd /path/to/py2to3_tools

# Step 2
# Setup vagrant and start it up as shown above
# You may need to remove 192.168.33.223 entry from .ssh/known_hosts file

# Step 3
# Do this step if you haven't installed ansible and jinja
pip install -r requirements.txt

# Step 4
ansible-playbook ansible/install_py35.yml -i ansible/hosts -v --extra-vars "host=vagrant"

```

#### Use py2to3_tools to create ansible roles for testing packages

```
# This will dynamically create the roles for testing the package names you provide. Roles can be found in ansible/virtualenvs/roles (delete the files in this folder when you re-run this script).
python scripts/py2to3_tools.py --names "Pillow, django" --action create_ansible_roles
```

#### Run ansible playbook to test sources

```
ansible-playbook ansible/test_sources.yml -i ansible/hosts -v --extra-vars "host=vagrant"
```
