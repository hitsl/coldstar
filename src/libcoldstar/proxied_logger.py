# -*- coding: utf-8 -*-
from twisted.web.http import _escape
from twisted.web.iweb import IAccessLogFormatter
from zope.interface import provider

__author__ = 'viruzzz-kun'


@provider(IAccessLogFormatter)
def proxiedLogFormatter(timestamp, request):
    """
    @return: A combined log formatted log line for the given request but use
        the value of the I{X-Forwarded-For} header as the value for the client
        IP address.

    @see: L{IAccessLogFormatter}
    """
    def getClientIP():
        """
        @return: The client address (the first address) in the value of the
            I{X-Forwarded-For header}.  If the header is not present, return
            C{Request.getClientIP()}.
        """
        if request.requestHeaders.hasHeader('x-forwarded-for'):
            return request.requestHeaders.getRawHeaders(b"x-forwarded-for")[0].split(b",")[0].strip()
        if request.requestHeaders.hasHeader('x-real-ip'):
            return request.requestHeaders.getRawHeaders(b"x-real-ip")[0].split(b",")[0].strip()
        return request.getClientIP()

    referrer = _escape(request.getHeader(b"referer") or b"-")
    agent = _escape(request.getHeader(b"user-agent") or b"-")
    ip = _escape(getClientIP() or b"-")
    line = (
        u'"%(ip)s" - "%(method)s %(uri)s %(protocol)s" %(code)d %(length)s "%(referrer)s" "%(agent)s"' % dict(
            ip=ip,
            timestamp=timestamp,
            method=_escape(request.method),
            uri=_escape(request.uri),
            protocol=_escape(request.clientproto),
            code=request.code,
            length=request.sentLength or u"-",
            referrer=referrer,
            agent=agent,
            ))
    return line