#
# setup.py
#
# Copyright: (C) 2012 Parspooyesh
# Author: Behrooz Shabani <everplays@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from setuptools import setup, find_packages

VERSION             = '0.0.1'

DESCRIPTION="""\
** Archipel Guest Agent **

Copyright: (c) 2012 parspooyesh
Author: Behrooz Shabani <everplays@gmail.com>

You need to run this package on your guest machine to be able to
run commands from archipel on guest os.

For more information, please go to http://archipelproject.org
"""

RPM_REQUIRED_DEPS = "archipel-core"
RPM_POST_INSTALL = "%post\narchipel-initinstall\n"

## HACK FOR DEPS IN RPMS
from setuptools.command.bdist_rpm import bdist_rpm
def custom_make_spec_file(self):
    spec = self._original_make_spec_file()
    lineDescription = "%description"
    spec.insert(spec.index(lineDescription) - 1, "requires: %s" % RPM_REQUIRED_DEPS)
    spec.append(RPM_POST_INSTALL)
    return spec
bdist_rpm._original_make_spec_file = bdist_rpm._make_spec_file
bdist_rpm._make_spec_file = custom_make_spec_file
## END OF HACK

def create_avatar_list(folder):
    ret = []
    for avatar in os.listdir(folder):
        ret.append("%s%s" % (folder, avatar))
    return ret

setup(name='archipel-guest',
      version=VERSION,
      description="The guest's agent part of Archipel",
      long_description=DESCRIPTION,
      classifiers=[
        'Development Status :: 0 - Alpha',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: System :: Emulators',
        'Topic :: System :: Operating System'],
      keywords='archipel, virtualization, libvirt, orchestration',
      author='Behrooz Shabani',
      author_email='everplays@gmail.com',
      url='http://archipelproject.org',
      license='AGPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      provides=["archipel"],
      install_requires=[
        "archipel-core>=0.5.0beta",
        "PIL"
      ],
      entry_points="""
        # -*- Entry points: -*-
        """,
      scripts = [
        'install/bin/runarchipelguest'
        ],
      data_files=[
        ('install/etc/init.d'              , ['install/etc/init.d/archipel']),
        ('install/etc/archipel/'           , ['install/etc/archipel/archipel.conf'])
        ]
      )
