# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


class Registry(object):
    __slots__ = ['value', 'children', 'undefined']
    undefined = None

    def __init__(self):
        self.value = self.undefined
        self.children = {}

    def __setitem__(self, key, value):
        path = key.split('.')
        o = self
        for child in path:
            if child not in o.children:
                o.children[child] = Registry()
            o = o.children[child]
        self[key].value = value

    def __getitem__(self, key):
        path = key.split('.')
        o = self
        for child in path:
            o = o.children[child]
        return o

    def __delitem__(self, key):
        path = key.split('.')
        o = self
        for child in path[:-1]:
            o = o.children[child]
        del o.children[path[-1]]

    def sub_tree(self):
        result = {}
        if self.value is not self.undefined:
            result[None] = self.value
        for key, child in self.children.iteritems():
            for k, v in child.sub_tree().iteritems():
                if k is None:
                    result[key] = v
                else:
                    result['%s.%s' % (key, k)] = v
        return result

    def super_tree(self, key):
        result = {}
        if self.value is not self.undefined:
            result[None] = self.value
        pre, path = [], key.split('.')
        o = self
        for k in path:
            pre.append(k)
            o = o.children[k]
            if o.value is not o.undefined:
                result['.'.join(pre) or None] = o.value
        return result


if __name__ == "__main__":
    a = Registry()
    a.value = 'Yatta'
    a['one.two.three'] = 123
    a['one.two'] = 12
    a['one'] = 1
    print(a.sub_tree())
    print(a['one.two'].sub_tree())
    print(a.super_tree('one.two'))
    del a['one.two']
    print(a.sub_tree())
    print(a['one'].value)