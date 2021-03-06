"""Super simple RPC webhandler, inspired by Pulsar"""

import struct

import aiohttp
from aiohttp import web


class MetaRCPHandler(type):
    """Collect all user defined RPC methods"""
    def __new__(cls, name, bases, attrs):
        rpc_methods = set()
        for key, method in attrs.items():
            if hasattr(method, '__call__') and key.startswith('rpc_'):
                method_name = key[4:]
                rpc_methods.add(method_name)
        for base in bases:
            if hasattr(base, 'rpc_methods'):
                rpc_methods.update(base.rpc_methods)
        attrs['rpc_methods'] = frozenset(rpc_methods)
        return super().__new__(cls, name, bases, attrs)


class RPCHandler(metaclass=MetaRCPHandler):
    """Base RPC handler for aiohttp"""
    def get_handler(self, method):
        if method in self.rpc_methods:
            return getattr(self, 'rpc_%s' % (method))
        raise Exception("Method not defined")


class WSRPCHandler(RPCHandler):
    """Simple implementation of a Websocket RPC handler"""

    async def websocket_handler(self, request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        while True:
            msg = await ws.receive()
            if msg.tp == aiohttp.MsgType.text:
                if msg.data == 'close':
                    # Breaking makes more sense here...
                    break
            elif msg.tp == aiohttp.MsgType.binary:
                body = msg.data
                (i, ), data = struct.unpack('I', body[:4]), body[4:]
                method, blob = data[:i], data[i:]
                handler = self.get_handler(method.decode('utf-8'))
                # Expects async handler
                result = await handler(ws, method, blob)
            elif msg.tp == aiohttp.MsgType.error:
                print('ws connection closed with exception %s' %
                      ws.exception())

        await ws.close()
        print('websocket connection closed')

        return ws
