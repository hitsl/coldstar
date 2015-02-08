#!/usr/bin/env python
# -*- coding: utf-8 -*-
from zope.interface import Interface

__author__ = 'viruzzz-kun'
__created__ = '07.02.2015'


class ITorrentRegistry(Interface):
    def add_peer(self, info_hash, peer_id, ip, port):
        """ Add the peer to the torrent database. """

    def peer_list(self, info_hash, compact):
        """ Depending on compact, dispatches to compact or expanded peer
        list functions. """

    def is_known_hash(self, info_hash):
        """"""

    def is_known_peer(self, info_hash, peer_id, ip, port):
        """"""

    def remove_peer(self, info_hash, peer_id, ip, port):
        """"""

    def register_hash(self, info_hash):
        """"""