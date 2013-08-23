# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for L{twisted.names.server}.
"""

from zope.interface.verify import verifyClass

from twisted.internet.interfaces import IProtocolFactory
from twisted.names import dns, resolve, server
from twisted.python import log
from twisted.trial import unittest



class NoresponseDNSServerFactory(server.DNSServerFactory):
    def allowQuery(*args):
        return False

    def sendReply(*args):
        pass



class DNSServerFactoryTests(unittest.TestCase):
    """
    Tests for L{server.DNSServerFactory}.
    """

    def test_resolverType(self):
        """
        L{server.DNSServerFactory.resolver} is a
        L{resolve.ResolverChain} instance
        """
        self.assertIsInstance(
            server.DNSServerFactory().resolver,
            resolve.ResolverChain)


    def test_resolverDefaultEmpty(self):
        """
        L{server.DNSServerFactory.resolver} is an empty
        L{resolve.ResolverChain} by default.
        """
        self.assertEqual(
            server.DNSServerFactory().resolver.resolvers,
            [])


    def test_authorities(self):
        """
        L{server.DNSServerFactory.__init__} accepts an C{authorities}
        argument. The value of this argument is a list and is used to
        extend the C{resolver} L{resolve.ResolverChain}.
        """
        dummyResolver = object()
        self.assertEqual(
            server.DNSServerFactory(
                authorities=[dummyResolver]).resolver.resolvers,
            [dummyResolver])


    def test_caches(self):
        """
        L{server.DNSServerFactory.__init__} accepts a C{caches}
        argument. The value of this argument is a list and is used to
        extend the C{resolver} L{resolve.ResolverChain}.
        """
        dummyResolver = object()
        self.assertEqual(
            server.DNSServerFactory(
                caches=[dummyResolver]).resolver.resolvers,
            [dummyResolver])


    def test_clients(self):
        """
        L{server.DNSServerFactory.__init__} accepts a C{clients}
        argument. The value of this argument is a list and is used to
        extend the C{resolver} L{resolve.ResolverChain}.
        """
        dummyResolver = object()
        self.assertEqual(
            server.DNSServerFactory(
                clients=[dummyResolver]).resolver.resolvers,
            [dummyResolver])


    def test_resolverOrder(self):
        """
        L{server.DNSServerFactory.resolver} contains an ordered list of
        authorities, caches and clients.
        """
        class DummyAuthority: pass
        class DummyCache: pass
        class DummyClient: pass
        self.assertEqual(
            server.DNSServerFactory(
                authorities=[DummyAuthority],
                caches=[DummyCache],
                clients=[DummyClient]).resolver.resolvers,
            [DummyAuthority, DummyCache, DummyClient])


    def test_cacheDefault(self):
        """
        L{server.DNSServerFactory.cache} is L{None} by default.
        """
        self.assertIdentical(server.DNSServerFactory().cache, None)


    def test_cacheOverride(self):
        """
        L{server.DNSServerFactory.__init__} assigns the first object in
        the C{caches} list to L{server.DNSServerFactory.cache}.
        """
        dummyResolver = object()
        self.assertEqual(
            server.DNSServerFactory(caches=[dummyResolver]).cache,
            dummyResolver)


    def test_canRecurseDefault(self):
        """
        L{server.DNSServerFactory.canRecurse} is a flag indicating that
        this server is capable of performing recursive DNS lookups. It
        defaults to L{False}.
        """
        self.assertEqual(server.DNSServerFactory().canRecurse, False)


    def test_canRecurseOverride(self):
        """
        L{server.DNSServerFactory.__init__} sets C{canRecurse} to L{True}
        if it is supplied with C{clients}.
        """
        self.assertEqual(server.DNSServerFactory(clients=[None]).canRecurse, True)


    def test_verboseDefault(self):
        """
        L{server.DNSServerFactory.verbose} defaults to L{False}.
        """
        self.assertEqual(server.DNSServerFactory().verbose, False)


    def test_verboseOverride(self):
        """
        L{server.DNSServerFactory.__init__} accepts a C{verbose} argument
        which overrides L{server.DNSServerFactory.verbose}.
        """
        self.assertEqual(server.DNSServerFactory(verbose=True).verbose, True)


    def test_interface(self):
        """
        L{server.DNSServerFactory} implements L{IProtocolFactory}.
        """
        self.assertTrue(verifyClass(IProtocolFactory, server.DNSServerFactory))


    def test_defaultProtocol(self):
        """
        L{server.DNSServerFactory.protocol} defaults to
        L{dns.DNSProtocol}.
        """
        self.assertIdentical(server.DNSServerFactory.protocol, dns.DNSProtocol)


    def test_buildProtocolDefaultProtocolType(self):
        """
        L{server.DNSServerFactory.buildProtocol} returns an instance of
        L{server.DNSServerFactory.protocol} by default.
        """
        self.assertIsInstance(
            server.DNSServerFactory().buildProtocol(addr=None),
            server.DNSServerFactory.protocol)


    def test_buildProtocolProtocolOverride(self):
        """
        L{server.DNSServerFactory.buildProtocol} builds a protocol by
        calling L{server.DNSServerFactory.protocol} with its self as a
        positional argument.
        """
        class StubProtocol:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        f = server.DNSServerFactory()
        f.protocol = StubProtocol
        p = f.buildProtocol(addr=None)
        self.assertIsInstance(p, StubProtocol)
        self.assertEqual(p.args, (f,))
        self.assertEqual(p.kwargs, {})


    def test_messageReceivedLoggingNoQuery(self):
        """
        L{server.DNSServerFactory.messageReceived} logs about an empty query
        if the message had no queries and C{verbose} is  C{>0}.
        """
        m = dns.Message()

        loggedMessages = []
        log.addObserver(loggedMessages.append)

        f = NoresponseDNSServerFactory(verbose=1)

        f.messageReceived(message=m, proto=None, address=('192.0.2.100', 53))
        self.assertEqual(len(loggedMessages), 1)
        self.assertEqual(
            loggedMessages[0]['message'],
            ("Empty query from ('192.0.2.100', 53)",))


    def test_messageReceivedLogging1(self):
        """
        L{server.DNSServerFactory.messageReceived} logs the query types of
        all queries in the message if C{verbose} is set to C{1}.
        """
        m = dns.Message()
        m.addQuery(name='example.com', type=dns.MX)
        m.addQuery(name='example.com', type=dns.AAAA)

        loggedMessages = []
        log.addObserver(loggedMessages.append)

        f = NoresponseDNSServerFactory(verbose=1)

        f.messageReceived(message=m, proto=None, address=('192.0.2.100', 53))
        self.assertEqual(len(loggedMessages), 1)
        self.assertEqual(
            loggedMessages[0]['message'],
            ("MX AAAA query from ('192.0.2.100', 53)",))


    def test_messageReceivedLogging2(self):
        """
        L{server.DNSServerFactory.messageReceived} logs the repr of all
        queries in the message if C{verbose} is set to C{2}.
        """
        m = dns.Message()
        m.addQuery(name='example.com', type=dns.MX)
        m.addQuery(name='example.com', type=dns.AAAA)

        loggedMessages = []
        log.addObserver(loggedMessages.append)

        f = NoresponseDNSServerFactory(verbose=2)

        f.messageReceived(message=m, proto=None, address=('192.0.2.100', 53))
        self.assertEqual(len(loggedMessages), 1)
        self.assertEqual(
            loggedMessages[0]['message'],
            ("<Query example.com MX IN> "
             "<Query example.com AAAA IN> query from ('192.0.2.100', 53)",))


    def test_messageReceivedTimestamp(self):
        """
        L{server.DNSServerFactory.messageReceived} assigns a unix
        timestamp to the received message.
        """
        m = dns.Message()
        f = NoresponseDNSServerFactory()
        t = object()
        self.patch(server.time, 'time', lambda: t)
        f.messageReceived(message=m, proto=None, address=None)

        self.assertEqual(m.timeReceived, t)



    def test_messageReceivedAllowQuery(self):
        """
        L{server.DNSServerFactory.messageReceived} passes all messages to
        L{server.DNSServerFactory.allowQuery} along with the receiving
        protocol and origin address.
        """
        class AllowQueryException(Exception):
            pass

        class RaisingDNSServerFactory(server.DNSServerFactory):
            def allowQuery(self, *args, **kwargs):
                raise AllowQueryException(args, kwargs)

        message = dns.Message()
        stubProtocol = object()
        stubAddress = object()

        f = RaisingDNSServerFactory()
        e = self.assertRaises(
            AllowQueryException,
            f.messageReceived,
            message=message, proto=stubProtocol, address=stubAddress)
        args, kwargs = e.args
        self.assertEqual(args, (message, stubProtocol, stubAddress))
        self.assertEqual(kwargs, {})


    def test_allowQueryFalse(self):
        """
        If C{allowQuery} returns C{False},
        L{server.DNSServerFactory.messageReceived} calls
        L{server.sendReply} with a message whose C{rCode} is
        L{dns.EREFUSED}.
        """
        class SendReplyException(Exception):
            pass

        class RaisingDNSServerFactory(server.DNSServerFactory):
            def allowQuery(self, *args, **kwargs):
                return False

            def sendReply(self, *args, **kwargs):
                raise SendReplyException(args, kwargs)

        f = RaisingDNSServerFactory()
        e = self.assertRaises(
            SendReplyException,
            f.messageReceived,
            message=dns.Message(), proto=None, address=None)
        (proto, message, address), kwargs = e.args

        self.assertEqual(message.rCode, dns.EREFUSED)


    def _messageReceivedTest(self, methodName, message):
        """
        Assert that the named method is called with the given message when
        it is passed to L{DNSServerFactory.messageReceived}.
        """
        # Make it appear to have some queries so that
        # DNSServerFactory.allowQuery allows it.
        message.queries = [None]

        receivedMessages = []
        def fakeHandler(message, protocol, address):
            receivedMessages.append((message, protocol, address))

        class FakeProtocol(object):
            def writeMessage(self, message):
                pass

        protocol = FakeProtocol()
        factory = server.DNSServerFactory(None)
        setattr(factory, methodName, fakeHandler)
        factory.messageReceived(message, protocol)
        self.assertEqual(receivedMessages, [(message, protocol, None)])


    def test_queryMessageReceived(self):
        """
        L{DNSServerFactory.messageReceived} passes messages with an opcode
        of C{OP_QUERY} on to L{DNSServerFactory.handleQuery}.
        """
        self._messageReceivedTest(
            'handleQuery', dns.Message(opCode=dns.OP_QUERY))


    def test_inverseQueryMessageReceived(self):
        """
        L{DNSServerFactory.messageReceived} passes messages with an opcode
        of C{OP_INVERSE} on to L{DNSServerFactory.handleInverseQuery}.
        """
        self._messageReceivedTest(
            'handleInverseQuery', dns.Message(opCode=dns.OP_INVERSE))


    def test_statusMessageReceived(self):
        """
        L{DNSServerFactory.messageReceived} passes messages with an opcode
        of C{OP_STATUS} on to L{DNSServerFactory.handleStatus}.
        """
        self._messageReceivedTest(
            'handleStatus', dns.Message(opCode=dns.OP_STATUS))


    def test_notifyMessageReceived(self):
        """
        L{DNSServerFactory.messageReceived} passes messages with an opcode
        of C{OP_NOTIFY} on to L{DNSServerFactory.handleNotify}.
        """
        self._messageReceivedTest(
            'handleNotify', dns.Message(opCode=dns.OP_NOTIFY))


    def test_updateMessageReceived(self):
        """
        L{DNSServerFactory.messageReceived} passes messages with an opcode
        of C{OP_UPDATE} on to L{DNSServerFactory.handleOther}.

        This may change if the implementation ever covers update messages.
        """
        self._messageReceivedTest(
            'handleOther', dns.Message(opCode=dns.OP_UPDATE))


    def test_connectionTracking(self):
        """
        The C{connectionMade} and C{connectionLost} methods of
        L{DNSServerFactory} cooperate to keep track of all
        L{DNSProtocol} objects created by a factory which are
        connected.
        """
        protoA, protoB = object(), object()
        factory = server.DNSServerFactory()
        factory.connectionMade(protoA)
        self.assertEqual(factory.connections, [protoA])
        factory.connectionMade(protoB)
        self.assertEqual(factory.connections, [protoA, protoB])
        factory.connectionLost(protoA)
        self.assertEqual(factory.connections, [protoB])
        factory.connectionLost(protoB)
        self.assertEqual(factory.connections, [])
