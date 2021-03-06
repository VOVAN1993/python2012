from xml.etree.ElementPath import _SelectorContext

__author__ = 'mazzachuses'
#http://www.ibm.com/developerworks/ru/library/l-python_part_10/
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.web.sux import XMLParser
import base64
from stanza import Stanza

HOST = "localhost"

step1 = open("step1.xml").read()
step2 = open("step2.xml").read()
step3 = open("step3.xml").read()

step4 = open("step4.xml").read()
step5 = open("step5.xml").read()
step6 = open("step6.xml").read()

class XMLChatProtocol(XMLParser):
    def __init__(self):
        self.username = None
        self.realm = None
        self.login = None
        self.id = None
        self.stack_stanzas = []
        self.success_auth = False
        self.resource = None


    def get_user_name(self):
        return self.username

    def gotTagStart(self, name, attributes):
        XMLParser.gotTagStart(self, name, attributes)
        stanza = Stanza(name, attributes)
        self.stack_stanzas.append(stanza)
        self.__handle_()


    def __handle_(self):
        stack = self.stack_stanzas
        stanza = stack.pop()
        length = len(stack)
        if stanza.is_closed():
            if stanza.get_name() == "auth":#todo add nonce
                self.transport.write(step3)
            elif stanza.get_name() == "response":
                if not self.success_auth:
                    data = stanza.get_text()
                    data = base64.b64decode(data)
                    data = data.split(",")
                    for entry in data:
                        if entry.startswith("username"):
                            self.username = entry.split("=")[1].replace("'", "").replace('"', '')
                        if entry.startswith("realm"):
                            self.realm = entry.split("=")[1].replace("'", "").replace('"', '')
                    self.transport.write(step4)
                    self.success_auth = True
                else:
                    self.transport.write(step5)
            elif stanza.get_name() == "iq":
                self.handle_query(stanza)
            elif stanza.get_name() == "message":
                self.__handle_message_(stanza)
            elif stanza.get_name() == "presence":
                self.__handle_presence_(stanza)
            stack[length - 1].add_child(stanza)

        else:
            if stanza.get_name() == "stream:stream":
                if not self.success_auth:
                    self.id = self.factory.get_id()
                    host = self.factory.get_host()
                    response = step1 % (self.id, host)
                    self.transport.write(response)
                    self.transport.write(step2)
                if self.success_auth: #end auth and add user
                    host = self.factory.get_host()
                    response = step6 % (self.id, host)
                    self.transport.write(response)

            stack.append(stanza)

    def __handle_presence_(self, stanza):
        map = self.factory.get_clients()
        for client in map.items():
            if client[0] != self.username:
                client[1].report_presence(self)


    def __handle_message_(self, stanza):
        attrs = stanza.get_attrs()
        to = attrs['to'].split("@")[0]
        user = self.factory.get_client(to)
        attrs['to'] = user.login
        user.transport.write(stanza.to_xml())

    def handle_query(self, stanza):
        attrs = stanza.get_attrs()
        id = attrs["id"]
        type = attrs["type"]
        if type == "set":
            child1 = stanza.get_children()[0]
            if child1.get_name() == "bind":
                resource = child1.get_children()[0]
                del child1.get_children()[0]
                self.resource = resource.get_text()
                response = Stanza("iq", {'id': id, 'type': 'result'})
                self.login = self.username + "@" + self.realm + "/" + self.resource

                self.add_user()
                jid = Stanza("jid", text=self.login)
                child1.add_child(jid)
                response.add_child(child1)
                self.transport.write(response.to_xml())
            elif child1.get_name() == "session":
                response = Stanza("iq", {'from': self.realm, 'type': 'result', "id": id})
                self.transport.write(response.to_xml())
            else:
                stanza = Stanza("iq", {'type': 'error', 'from': self.factory.get_host(), 'id': id, 'to': self.login})
        elif type == "get":
            for child in stanza.get_children():
                if child.get_name() == "query":
                    query = child
                    if query.get_attr("xmlns") == "jabber:iq:roster":
                        response = Stanza("iq", {"to": self.login, type: "result", "id": id})
                        response.add_child(query)
                        for user in self.factory.get_clients().items():
                            if user[0] != self.username:
                                item = Stanza("item",
                                    {'jid': user[1].login, 'name': user[1].username, 'subscription': 'both'})
                                query.add_child(item)
                        self.transport.write(response.to_xml())
                        for user in self.factory.get_clients().items():
                            if user[0] != self.username:
                                presence = Stanza("presence", {'from': user[1].login, 'to': self.login})
                                self.transport.write(presence.to_xml())
                    else:
                        stanza = Stanza("iq",
                            {'type': 'error', 'from': self.factory.get_host(), 'id': id, 'to': self.login})
                        stanza.add_child(query)
                        self.transport.write(stanza.to_xml())


    def report_presence(self, other_user):
        stanza = Stanza("presence", {'from': other_user.login, 'to': self.login})
        self.transport.write(stanza.to_xml())


    def add_user(self):
        self.factory.add_client(self)#todo mabe  self.username


    def gotTagEnd(self, name):
        XMLParser.gotTagEnd(self, name)
        stack = self.stack_stanzas
        stanza = stack.pop()
        stanza.close()
        stack.append(stanza)
        self.__handle_()


    def gotText(self, data):
        XMLParser.gotText(self, data)
        length = len(self.stack_stanzas)
        if length > 0:
            self.stack_stanzas[length - 1].add_text(data)


class ChatProtocolFactory(ServerFactory):
    protocol = XMLChatProtocol#ChatProtocol


    def __init__(self):
        self.__clients_ = {} #login - > XMLChatProtocol todo add support resourses
        self.__host_ = HOST
        self.__cur_id_ = -1

    def sendMessageToAllClients(self, mesg):
        for client in self.clientProtocols:
            client.sendLine(mesg)

    def get_host(self):
        return self.__host_

    def get_id(self):
        self.__cur_id_ += 1
        return self.__cur_id_

    def add_client(self, user):
        self.__clients_[user.get_user_name()] = user

    def get_clients(self):
        return self.__clients_

    def get_client(self, user_name):
        return self.__clients_[user_name]


print "Starting Server"
factory = ChatProtocolFactory()
reactor.listenTCP(5222, factory)
reactor.run()