# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'mmalkov'


class ICasService(Interface):
    db = Attribute('db', 'Database service')
    expiry_time = Attribute('expiry_time', 'Token time to live')
    clean_period = Attribute('clean_period', 'How often service should check for expired tokens')
    check_duplicate_tokens = Attribute(
        'check_duplicate_tokens',
        'Should the service raise exception if user already took a token?')

    def acquire_token(self, login, password):
        """
        Acquire auth token for login / password pair
        :param login:
        :param password:
        :return:
        """

    def release_token(self, token):
        """
        Release previously acquired token
        :param token:
        :return:
        """

    def check_token(self, token):
        """
        Check whether auth token is valid
        :param token:
        :return:
        """

    def prolong_token(self, token):
        """
        Make token live longer
        :param token:
        :return:
        """


class ICasResource(Interface):
    def acquire_token(self, login, password):
        """
        Acquire auth token for login / password pair
        :param login:
        :param password:
        :return:
        """

    def release_token(self, token):
        """
        Release previously acquired token
        :param token:
        :return:
        """

    def check_token(self, token):
        """
        Check whether auth token is valid
        :param token:
        :return:
        """

    def prolong_token(self, token):
        """
        Make token live longer
        :param token:
        :return:
        """

    def login_form(self):
        """
        Render Login form
        :return:
        """