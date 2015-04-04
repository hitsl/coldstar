#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from twisted.application.service import Service

__author__ = 'viruzzz-kun'
__created__ = '03.04.2015'


class CmsService(Service):
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)

    def post(self, lang_code, rel_path, data):
        path = os.path.abspath(os.path.join(self.root_dir, lang_code, rel_path))
        if not path.startswith(self.root_dir):
            raise Exception() # TODO:
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        with open(path, 'wb') as f:
            f.write(data)

    def post_img(self, rel_path, data):
        path = os.path.abspath(os.path.join(self.root_dir, 'img', rel_path))
        if not path.startswith(self.root_dir):
            raise Exception()  # TODO:
        with open(path, 'wb') as f:
            f.write(data)

    def get_img(self, rel_path, consumer):
        path = os.path.abspath(os.path.join(self.root_dir, 'img', rel_path))
        if not path.startswith(self.root_dir):
            raise Exception()  # TODO:
        with open(path, 'rb') as f:
            while 1:
                data = f.read()
                if not data:
                    break
                consumer.write(data)

    def get(self, lang, rel_path, consumer):
        path = os.path.abspath(os.path.join(self.root_dir, lang, rel_path))
        if not path.startswith(self.root_dir):
            raise Exception()  # TODO:
        with open(path, 'rb') as f:
            while 1:
                data = f.read()
                if not data:
                    break
                consumer.write(data)

    def list_lang(self, rel_path):
        return [
            lang
            for lang in os.listdir(self.root_dir)
            if lang != 'img' and os.path.isfile(os.path.join(self.root_dir, lang, rel_path))
        ]