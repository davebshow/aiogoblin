Protocol 0.1 (Draft)

This protocol is based on the [ZMQ Majordomo Protocol 0.2](http://rfc.zeromq.org/spec:18) (MDP/0.2) w/modifications inspired by the heartbeating model described in the [ZMQ Freelance Protocol](http://rfc.zeromq.org/spec:10). As stated in the [MDP](http://rfc.zeromq.org/spec:18) definition:

>The Majordomo Protocol (MDP) defines a reliable service-oriented request-reply dialog between a set of client applications, a broker and a set of worker applications. MDP covers presence, heartbeating, and service-oriented request-reply processing

### Goals

Like MDP/0.2, this protocol uses name based service resolution and allows for multiple replies to a single request. It is not 100% compatible with MDP/0.2. The significant differences are that this protocol allows for multiple requests to be sent without waiting for a reply (maybe), and each request has a unique id that can be managed explicitly.

The goals are the same as those stated in the [MDP](http://rfc.zeromq.org/spec:18) contract:

> Allow requests to be routed to workers on the basis of abstract service names.
> Allow both peers to detect disconnection of the other peer, through the use of heartbeating.
> Allow the broker to implement a "least recently used" pattern for task distribution to workers for a given > service.
> Allow the broker to recover from dead or disconnected workers by resending requests to other workers.

### Overall topology

The overall topology is quite similar to the [MDP](http://rfc.zeromq.org/spec:18):

> MDP connects a set of client applications, a single broker device and a pool of workers applications. Clients connect to the broker, as do workers. Clients and workers do not see each other, and both can come and go arbitrarily.

The broker SHOULD open two sockets (ports), one front-end for clients, and one back-end for workers.

ROUTER addressing

As stated in [MDP](http://rfc.zeromq.org/spec:18):

> The broker MUST use a ROUTER socket to accept requests from clients, and connections from workers.

> When receiving messages a ROUTER socket shall prepend a message part containing the identity of the originating peer to the message before passing it to the application. When sending messages a ROUTER socket shall remove the first part of the message and use it to determine the identity of the peer the message shall be routed to.

> This extra frame is not shown in the sub-protocol commands explained below.

### Protocol Client

The Protocol/Client is a sync/async dialog initiated by the client ('C' is client, 'B' is broker).

Dialog:|
-------|
Repeat:|
  C: REQUEST|
Repeat:|
  B: \*PARTIAL|
  B: FINAL|

Breakdown:

* Client initiates communication by sending one or more REQUEST commands to broker.
* Broker responds by returning 0 or more PARTIAL RESPONSE commands followed by exactly 1 FINAL RESPONSE messages per REQUEST issued.

REQUEST, PARTIAL, and FINAL framing is the same as described in the [MDP](http://rfc.zeromq.org/spec:18) with the exception of the content of Frame 0, which will indicate the protocol specified in this document:

A REQUEST command consists of a multipart message of 5 or more frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: 0x01 (one byte, representing REQUEST)
* Frame 2: Service name (printable string)
* Frame 3: Request id (uuid?)
* Frames 4+: Request body (opaque binary)

A PARTIAL command consists of a multipart message of 5 or more frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: 0x02 (one byte, representing PARTIAL)
* Frame 2: Service name (printable string)
* Frame 3: Request id (uuid?)
* Frames 4+: Reply body (opaque binary)

A FINAL command consists of a multipart message of 5 or more frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: 0x03 (one byte, representing FINAL)
* Frame 2: Service name (printable string)
* Frame 3: Request id (uuid?)
* Frames 4+: Reply body (opaque binary)

As stated in MDP:

> Clients MUST use a DEALER socket. The client MUST be prepared to handle zero or more PARTIAL commands from the broker.

However, after a FINAL command, the broker can continue to send messages to the client. The client MUST keep track of REQUEST messages issued and receive a FINAL command for each REQUEST.

Like [MDP](http://rfc.zeromq.org/spec:18):

> Clients MAY use any suitable strategy for recovering from a non-responsive broker.

### Protocol/Worker

Protocol/Worker is a mix of a synchronous request-reply dialog initiated by the worker and a synchronous ping-pong heartbeat dialog, also initiated by the worker. The request-reply dialog is the same as described in [MDP](http://rfc.zeromq.org/spec:18) (W is worker, B is broker):

Request-reply dialog:|
---------------------|
W: READY|
Repeat:|
  B: REQUEST|
  W: \*PARTIAL|
  W: FINAL|

Ping-pong dialog:|
-----------------|
Repeat:|
  W: PING|
  B: PONG|
B: DISCONNECT|

For the most part, commands are identical to those specified in the [MDP](http://rfc.zeromq.org/spec:18) (with the exception of an explicit request id, and ping-pong heartbeating):

A READY command consists of a multipart message of 3 frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: 0x01 (one byte, representing READY)
* Frame 2: Service name (printable string)

A REQUEST command consists of a multipart message of 5 or more frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: 0x02 (one byte, representing REQUEST)
* Frame 2: Client address (envelope stack)
* Frame 3: Empty (zero bytes, envelope delimiter)
* Frame 4: Request id (uuid?)
* Frames 5+: Request body (opaque binary)

A PARTIAL command consists of a multipart message of 5 or more frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: 0x03 (one byte, representing PARTIAL)
* Frame 2: Client address (envelope stack)
* Frame 3: Empty (zero bytes, envelope delimiter)
* Frame 4: Request id (uuid?)
* Frames 5+: Request body (opaque binary)

A FINAL command consists of a multipart message of 5 or more frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: 0x04 (one byte, representing FINAL)
* Frame 2: Client address (envelope stack)
* Frame 3: Empty (zero bytes, envelope delimiter)
* Frame 4: Request id (uuid?)
* Frames 5+: Request body (opaque binary)

A PING command consists of a multipart message of 2 frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: "PING" (four characters)

A PONG command consists of a multipart message of 2 frames, formatted on the wire as follows:

* Frame 0: Protocol name and version
* Frame 1: "PONG" (four characters)

A DISCONNECT command consists of a multipart message of 2 frames, formatted on the wire as follows:

* Frame 0: "MDPW02" (six bytes, representing MDP/Worker v0.2)
* Frame 1: 0x06 (one byte, representing DISCONNECT)

### Opening and Closing Connections:

Same as [MDP](http://rfc.zeromq.org/spec:18):

* The worker is responsible for opening and closing a logical connection. One worker MUST connect to exactly one broker using a single ØMQ DEALER socket.
* Since ØMQ automatically reconnects peers after a failure, every MDP command includes the protocol header to allow proper validation of all messages that a peer receives.
* The worker opens the connection to the broker by creating a new socket, connecting it, and then sending a READY command to register a service. One worker handles precisely one service, and many workers MAY handle the same service. The worker MUST NOT send a further READY.
* There is no response to a READY. The worker SHOULD assume the registration succeeded until or unless it receives a DISCONNECT, or it detects a broker failure through heartbeating.
* The worker MAY send DISCONNECT at any time, including before READY. When the broker receives DISCONNECT from a worker it MUST send no further commands to that worker.
* The broker MAY send DISCONNECT at any time, by definition after it has received at least one command from the worker.
* The broker MUST respond to any valid but unexpected command by sending DISCONNECT and then no further commands to that worker. The broker SHOULD respond to invalid messages by dropping them and treating that peer as invalid.
* When the worker receives DISCONNECT it must send no further commands to the broker; it MUST close its socket, and reconnect to the broker on a new socket. This mechanism allows workers to re-register after a broker failure and recovery.

### Request and Reply Processing:

Largely the same as [MDP](http://rfc.zeromq.org/spec:18):

* The worker SHALL send zero or more PARTIAL commands for a single REQUEST, followed by exactly one FINAL command.
* The REQUEST, PARTIAL and FINAL commands SHALL contain precisely one client address frame. This frame MUST be followed by an empty (zero sized) frame.
* The REQUEST, PARTIAL and FINAL commands SHALL contain precisely one request id frame. This frame MUST follow an empty (zero sized) frame (envelope delimiter).
* The address of each directly connected client is prepended by the ROUTER socket to all request messages coming from clients. That ROUTER socket also expects a client address to be prepended to each reply message sent to a client

### Heartbeating

Similar to [MDP](http://rfc.zeromq.org/spec:18):

* PING commands are valid at any time, after a READY command.
* Any received command except DISCONNECT acts as a heartbeat. Peers SHOULD NOT send HEARTBEAT commands while also sending other commands.
* The worker MUST send PING (or other non-DISCONNECT) commands at an agreed upon interval. A worker MUST consider the router "disconnected" if no PONG (or other non-DISCONNECT) arrives within some multiple of that interval (usually 3-5).
* The router MUST send PONG (or other non-DISCONNECT) as a response to a worker PING. A router MUST consider the worker "disconnected" if no PING (or other non-DISCONNECT) arrives within some multiple of agreed upon PING interval.
* If the worker detects that the broker has disconnected, it SHOULD restart a new conversation.
* If the broker detects that the worked has disconnected, it SHOULD stop sending it messages of any type.


*Reliability* and *Security* should be similar to [MDP](http://rfc.zeromq.org/spec:18).


### Scalability and Performance

As stated in [MDP](http://rfc.zeromq.org/spec:18):

> Majordomo is designed to be scalable to large numbers (thousands) of workers and clients, limited only by system resources on the broker. Partitioning of workers by service allows for multiple applications to share the same broker infrastructure.

> Throughput performance for a single client application will be limited to tens of thousands, not millions, of request-reply transactions per second due to round-trip costs and the extra latency of a broker-based approach. The larger the request and reply messages, the more efficient Majordomo will become. Majordomo may be complemented by high-speed data delivery architectures.

> System requirements for the broker are moderate: no more than one outstanding request per client will be queued, and message contents can be switched between clients and workers without copying or processing. A single broker thread can therefore switch several million messages per second, and multithreaded implementations (offering multiple virtual brokers, each on its own port) can scale to as many cores as required.


### Known weaknesses

* The use of multiple frames for command formatting has a performance impact.
