# -*- coding: utf-8 -*-
#
# archipelGuest.py
#
# Copyright (C) 2012 Parspooyesh - Behrooz Shabani <everplays@gmail.com>
# This file is part of ArchipelProject
# http://archipelproject.org
#
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

"""
Contains L{TNArchipelGuest}, singleton entity for guest os
"""
import glob
import xmpp
import subprocess
import os
import re
from threading import Thread
from lxml import etree
from StringIO import StringIO

from xmpp.simplexml import XML2Node
from archipelcore.archipelEntity import TNArchipelEntity
from archipelcore.archipelHookableEntity import TNHookableEntity
from archipelcore.utils import build_error_iq

# Namespace
ARCHIPEL_NS_GUEST_CONTROL                  = "archipel:guest:control"

# XMPP shows
ARCHIPEL_XMPP_SHOW_ONLINE                       = "Online"

class TNArchipelGuest(TNArchipelEntity, TNHookableEntity):
    """
    This class represents a Guest XMPP Capable.
    """
    def __init__(self, jid, password, configuration):
        """
        This is the constructor of the class.
        @type jid: string
        @param jid: the jid of the hypervisor
        @type password: string
        @param password: the password associated to the JID
        @type configuration: ConfigParser
        @param configuration: configuration object
        """
        TNArchipelEntity.__init__(self, jid, password, configuration, 'auto')
        self.log.info("starting archipel-guest")

        self.xmppserveraddr             = self.jid.getDomain()
        self.entity_type                = "vmguest"

        self.log.info("Server address defined as %s" % self.xmppserveraddr)

        # module inits
        self.initialize_modules('archipel.plugin.vmguest')

    ### Utilities

    def register_handlers(self):
        """
        lets register our iq handler
        """
        TNArchipelEntity.register_handlers(self)
        self.xmppclient.RegisterHandler('iq', self.process_iq, ns=ARCHIPEL_NS_GUEST_CONTROL)

    def unregister_handlers(self):
        """
        hmm, seems that we must unregister our iq handler
        """
        TNArchipelEntity.unregister_handlers(self)
        self.xmppclient.UnregisterHandler('iq', self.process_iq, ns=ARCHIPEL_NS_GUEST_CONTROL)

    def execute_command(self, command, result=True):
        """
        executes given command using subprocess module
        @type command: String
        @param command: command to be executed
        """
        p = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not result:
            return ''
        response, stderr = p.communicate()
        return str(response)+"\n"+str(stderr)

    ### XMPP Processing

    def process_iq(self, conn, iq):
        """
        This method is invoked when a ARCHIPEL_NS_GUEST_CONTROL IQ is received.
        It understands IQ of type:
            - exec
        @type conn: xmpp.Dispatcher
        @param conn: ths instance of the current connection that send the stanza
        @type iq: xmpp.Protocol.Iq
        @param iq: the received IQ
        """
        reply = None
        action = self.check_acp(conn, iq)

        # just run commands received from jid of vm
        if iq.getFrom().getStripped().lower() <> self.jid.getStripped().replace("-agent", '').lower():
            return

        if action == "exec":
            reply = self.iq_exec(iq)
        if action == "provisioning":
            reply = self.iq_provisioning(iq)
        if reply:
            conn.send(reply)
            raise xmpp.protocol.NodeProcessed

    def iq_exec(self, iq):
        """
        this method receives an Iq stanza with exec action, runs the command of Iq and
        creates a result containing the stdout of command
        @type iq: xmpp.Protocol.Iq
        @param iq: received Iq stanza
        @rtype xmpp.Protocol.Iq
        @return the reply of stanza
        """
        self.log.info('processing: '+str(iq))
        command = iq.getTag("query").getTag("archipel").getData()
        # if we're in safe mode just run scripts that we've provided along archipel
        if self.configuration.getboolean("GUEST", "safemode"):
            command = os.path.join(self.configuration.get("DEFAULT", "archipel_folder_lib"), "bin", command)
            self.log.info("going to execute: "+command)
            if not os.path.exists(command):
                response = "there's no such command available"
            else:
                response = self.execute_command(command)
        else:
            response = self.execute_command(command)
        result = iq.buildReply('result')
        query = result.getTag("query")
        archipel = query.addChild("archipel", attrs={
            "action": "exec",
            "executor": iq.getTag("query").getTag("archipel").getAttr("executor")})
        archipel.addData(response)
        self.log.info('responsing: '+str(result))
        return result

    def iq_provisioning(self, iq):
        """ response to provisioning request.
        if stanza is a get then return available provisionings
        if stanza is a set then run provisioning scripts with given values
        @type iq: xmpp.Protocol.Iq
        @param iq: received Iq stanza
        @rtype xmpp.Protocol.Iq
        @return the reply of stanza
        """
        if iq.getType() == "get":
            result = iq.buildReply('result')
            archipelTag = xmpp.simplexml.Node('archipel', attrs={'action': 'provisioning'}, payload=self.get_provisioning_config())
            result.setQueryPayload([archipelTag])
        elif iq.getType() == "set":
            result = iq.buildReply("result")
            archipelTag = xmpp.simplexml.Node('archipel', attrs={'action': 'provisioning'})
            result.setQueryPayload([archipelTag])
            try:
                self.run_provisionings(iq)
            except Exception as e:
                result = build_error_iq(self, e, iq, ARCHIPEL_NS_GUEST_CONTROL)
        return result

    def get_provisioning_config(self):
        """ create a list of valid configurations ready to be used as payload. """
        payload = []
        # create xsd to be able to check validity of xml files
        xsd_string = open(os.path.join(os.path.dirname(__file__), "configuration.xsd")).read()
        xsd_doc = etree.parse(StringIO(xsd_string))
        xsd = etree.XMLSchema(xsd_doc)
        config_dir = self.configuration.get("GUEST", "config_directory")
        for xmlPath in glob.glob("%s/*.xml" % config_dir):
            name = re.search(".*/(.*)\\.xml$", xmlPath).group(1)
            xml_string = open(xmlPath).read()
            xml_doc = etree.parse(StringIO(xml_string))
            if not xsd.validate(xml_doc):
                continue
            index = len(payload)
            payload.append(XML2Node(xml_string))
            payload[index].setAttr('name', name)
        return payload

    def run_provisionings(self, iq):
        """ run provisionings based on received iq
        @type iq: xmpp.Protocol.Iq
        @param iq: set provisionings stanza
        """
        for arguments in iq.getTag("query").getTag("archipel").getTags("arguments"):
            name = arguments.getAttr('name')
            xml_path = os.path.join(self.configuration.get("GUEST", "config_directory"), "%s.xml" % name)
            xml_doc = etree.parse(xml_path)
            command = xml_doc.xpath("/x:config/x:command", namespaces={'x': 'http://xamin.ir/provisioning'})[0].text
            arg_values = []
            for argument in arguments.getTags('argument'):
                arg_values.append(argument.getData())
            command = command % tuple(arg_values)
            self.execute_command(command, False)
