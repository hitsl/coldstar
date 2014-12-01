# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute

__author__ = 'mmalkov'


class ICasService(Interface):
    db_service = Attribute('db_service', 'Database service')

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