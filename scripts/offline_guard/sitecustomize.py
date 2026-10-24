"""Audit-only process network fence. Local app services remain reachable.

Activate with PYTHONPATH=scripts/offline_guard. Does not change the host firewall.
"""
import ipaddress
import socket


def local(host):
    if host in ('localhost', None, ''):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


_connect = socket.socket.connect
_connect_ex = socket.socket.connect_ex
_resolve = socket.getaddrinfo


def connect(self, address):
    if isinstance(address, tuple) and not local(address[0]):
        raise OSError('Offline audit blocks non-loopback networking')
    return _connect(self, address)


def connect_ex(self, address):
    if isinstance(address, tuple) and not local(address[0]):
        raise OSError('Offline audit blocks non-loopback networking')
    return _connect_ex(self, address)


def resolve(host, *args, **kwargs):
    if not local(host):
        raise OSError('Offline audit blocks external DNS')
    return _resolve(host, *args, **kwargs)


socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
socket.getaddrinfo = resolve
