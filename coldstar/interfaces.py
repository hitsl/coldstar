#!/usr/bin/env python
# -*- coding: utf-8 -*-
from zope.interface import Interface

__author__ = 'viruzzz-kun'
__created__ = '13.09.2014'


class IColdStarService(Interface):
    def acquire_lock(self, object_id, locker):
        pass

    def release_lock(self, object_id, token):
        pass

    def acquire_tmp_lock(self, object_id, locker):
        pass

    def prolong_tmp_lock(self, object_id, token):
        pass


# class IDataAccessService(Interface):
#     def get_notification(self, notification_id):
#         pass
#
#     def get_personal_notifications(self, person_id):
#         pass
#
#     def add_notification(self, type_code, data):
#         pass
#
#     def add_subscription(self, user_id, type_code):
#         pass
#
#     def remove_subscription(self, user_id, type_code):
#         pass
#
#     def confirm_notification(self, personal_notification_id):
#         pass


