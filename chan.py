#!/usr/bin/env python3

from collections import deque


class chan(object):
    def __init__(self, cap=None):
        self.q = deque([])
        self.cap = cap

    def send(self, x):
        return False, lambda: self._send(x)

    def _send(self, x):
        if self.cap is None or len(self.q) < self.cap:
            self.q.append(x)
            return True, None
        else:
            return False, None

    def recv(self):
        return False, lambda: self._recv()

    def _recv(self):
        if len(self.q) > 0:
            return True, self.q.popleft()
        else:
            return False, None


def try_send(f, x):
    try:
        result = f.send(x)
    except StopIteration:
        return False, None
    else:
        return True, result


def step(p):
    it, (go_kludge, cmd) = p
    if go_kludge:
        ok, result = try_send(it, None)
        if ok:
            return [(it, result), (cmd, next(cmd))]
        else:
            return [(cmd, next(cmd))]
    ok, result = cmd()
    if not ok:
        return [p]
    ok, result = try_send(it, result)
    if not ok:
        return []
    return [(it, result)]


def flatmap(f, xs):
    result = []
    for x in xs:
        result.extend(f(x))
    return result


def run(*fs):
    parked = [(f, next(f)) for f in fs]
    while len(parked) > 0:
        next_parked = flatmap(step, parked)
        if next_parked == parked:
            print('no progress made :(')
            break
        else:
            parked = next_parked


def go(f):
    return True, f


def respond(name, reply_chan):
    yield reply_chan.send('Hello, {}!'.format(name))


def rpc_server(request_chan):
    while True:
        name, reply_chan = yield request_chan.recv()
        yield go(respond(name, reply_chan))


def rpc_client(request_chan, name):
    for i in range(3):
        reply_chan = chan()
        request = '{} {}'.format(name, 'I' * (i + 1))
        yield request_chan.send((request, reply_chan))
        reply = yield reply_chan.recv()
        print('sent request:', request, '->',
              'got reply:', reply)


def top():
    c = chan()
    yield go(rpc_server(c))
    yield go(rpc_client(c, 'Alice'))
    yield go(rpc_client(c, 'Bob'))


def main():
    run(top())


if __name__ == '__main__':
    main()
