# -*- coding: utf-8 -*-
#
# virtualmachineagent.py
#
# Copyright (C) 2012 parspooyesh <everplays@gmail.com>
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

import xmpp
from archipelcore.archipelPlugin import TNArchipelPlugin

# Namespace
ARCHIPEL_NS_GUEST_CONTROL                  = "archipel:guest:control"

class TNVirtualMachineAgent(TNArchipelPlugin):
    """
    This plugin allows to create scheduled actions.
    """
    def __init__(self, configuration, entity, entry_point_group):
        """
        Initialize the plugin.
        @type configuration: Configuration object
        @param configuration: the configuration
        @type entity: L{TNArchipelEntity}
        @param entity: the entity that owns the plugin
        @type entry_point_group: string
        @param entry_point_group: the group name of plugin entry_point
        """
        TNArchipelPlugin.__init__(self, configuration=configuration, entity=entity, entry_point_group=entry_point_group)

    def register_handlers(self):
        TNArchipelPlugin.register_handlers(self)
        self.entity.xmppclient.RegisterHandler('message', self.process_message, typ="chat")
        self.entity.xmppclient.RegisterHandler('iq', self.process_iq, ns=ARCHIPEL_NS_GUEST_CONTROL)

    def unregister_handlers(self):
        TNArchipelEntity.unregister_handlers(self)
        self.entity.xmppclient.UnregisterHandler('message', self.process_message, typ="chat")
        self.entity.xmppclient.UnregisterHandler('iq', self.process_iq, ns=ARCHIPEL_NS_GUEST_CONTROL)

    @staticmethod
    def plugin_info():
        """
        Return informations about the plugin.
        @rtype: dict
        @return: dictionary contaning plugin informations
        """
        return {    "common-name"               : "Virtual Machine Agent",
                    "identifier"                : "virtualmachineguestagent",
                    "configuration-section"     : None,
                    "configuration-tokens"      : []}

    def process_iq(self, conn, iq):
        self.entity.log.info(str(iq.getFrom()).lower()+'=='+(self.entity.uuid+'-agent@'+self.entity.jid.getDomain()+'/guestagent').lower())
        if str(iq.getFrom()).lower()==(self.entity.uuid+'-agent@'+self.entity.jid.getDomain()+'/guestagent').lower():
            archipel = iq.getTag("query").getTag("archipel")
            msg = xmpp.protocol.Message(archipel.getAttr('executor'), archipel.getData())
            conn.send(msg)
            raise xmpp.NodeProcessed

    def process_message(self, conn, msg):
        body = str(msg.getBody())
        if body.find('!exec')==0 and self.entity.permission_center.check_permission(str(msg.getFrom().getStripped()), "message"):
            command = body.replace('!exec', '').strip()
            executor = msg.getFrom()
            runIq = self.execute(command, executor)
            self.entity.log.info('sending: '+str(runIq ))
            conn.send(runIq)
            raise xmpp.NodeProcessed

    def execute(self, command, executor):
        to = xmpp.JID(self.entity.uuid+'-agent@'+self.entity.jid.getDomain()+'/guestagent')
        iq = xmpp.protocol.Iq(typ='get', to=to)
        iq.setQueryNS(ARCHIPEL_NS_GUEST_CONTROL);
        query = iq.getTag("query");
        archipel = query.addChild('archipel');
        archipel.setAttr('executor', executor)
        archipel.setAttr('action', 'exec')
        archipel.addData(command)
        return iq

