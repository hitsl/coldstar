# -*- coding: utf-8 -*-
import sys
import PIL.Image
import signal
from pyinsane.abstract import Scanner
from pyinsane.rawapi import SaneException


__author__ = 'viruzzz-kun'


max_width = 2560


def handler(number, frame):
    print('INTERRUPTED')
    exit(0)


signal.signal(signal.SIGINT, handler)


def main():
    dev_name = sys.argv[1]
    sys.stdout.write('DEVICE:%s\n' % dev_name)
    device = Scanner(dev_name)
    for i in xrange(10):
        try:
            device.options['resolution'].value = 600
        except SaneException, e:
            if i == 9:
                print('CANNOT SET DPI: %r' % e)
                return exit(1)
        else:
            if i:
                print('TOOK ATTEMPTS TO SET DPI: %s' % (i+1))
            break
    sys.stdout.write('SCANNING\n')
    try:
        scan_session = device.scan(multiple=False)
    except SaneException, e:
        print('FAILED: %r' % e)
        return exit(1)
    try:
        while True:
            scan_session.scan.read()
    except EOFError:
        pass
    sys.stdout.write('ACQUIRED\n')
    img = scan_session.images[0]
    w, h = img.size
    if w > max_width:
        new_w = max_width
        new_h = int(h * (float(new_w) / w))
        img = img.resize((new_w, new_h), PIL.Image.LANCZOS)
    sys.stdout.write('DATA\n')
    img.save(sys.stdout, 'png')


if __name__ == "__main__":
    main()