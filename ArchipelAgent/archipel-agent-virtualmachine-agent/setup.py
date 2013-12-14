# 
# setup.py
# 
# Copyright (C) 2012 parspooyesh <everplays@gmail.com>
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

from setuptools import setup, find_packages

VERSION             = '0.0.1'

AUTHOR              = 'Behrooz Shabani'
MAIL                = 'everplays@gmail.com'
URL                 = 'http://archipelproject.org'
LICENSE             = 'AGPL'
NAME                = 'archipel-agent-virtualmachine-guest'
SHORTDESCRIPTION    = "This module enables user to execute commands on guest os"
LONGDESCRIPTION     = "This module works as a tunnel between guest-agent running on \
guest os and user (or other modules). module transforms every messages starting with \
!exec to guest-agent (using xmpp) to run on guest os, so if user runs !exec ls the ls \
command will run on guest os and result of it will be sent back to user as message."
ENTRY_POINTS        = { 'archipel.plugin.virtualmachine' : [
                            'factory=archipelvirtualmachineagent:make_archipel_plugin'],
                        'archipel.plugin' : [
                            'factory=archipelvirtualmachineagent:version']}

RPM_REQUIRED_DEPS   = "archipel-core"

## HACK FOR DEPS IN RPMS
from setuptools.command.bdist_rpm import bdist_rpm
def custom_make_spec_file(self):
    spec = self._original_make_spec_file()
    lineDescription = "%description"
    spec.insert(spec.index(lineDescription) - 1, "requires: %s" % RPM_REQUIRED_DEPS)
    return spec
bdist_rpm._original_make_spec_file = bdist_rpm._make_spec_file
bdist_rpm._make_spec_file = custom_make_spec_file
## END OF HACK


setup(name=NAME,
      version=VERSION,
      description=SHORTDESCRIPTION,
      long_description=LONGDESCRIPTION,
      classifiers=[
        'Development Status :: 4 - Beta',
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
      author=AUTHOR,
      author_email=MAIL,
      url=URL,
      license=LICENSE,
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "archipel-core>=0.5.0beta"
      ],
      entry_points=ENTRY_POINTS
      )
