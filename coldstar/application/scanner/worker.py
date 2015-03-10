# -*- coding: utf-8 -*-
import sys
import PIL.Image
from pyinsane.abstract import Scanner
from pyinsane.rawapi import SaneException


__author__ = 'viruzzz-kun'


max_width = 2560


def main():
    dev_name = sys.argv[1]
    sys.stdout.write('DEVICE:%s\n' % dev_name)
    device = Scanner(dev_name)
    for i in xrange(10):
        try:
            device.options['resolution'].value = 600
        except SaneException:
            if i == 10:
                print('CANNOT SET DPI')
        else:
            if i:
                print('TOOK ATTEMPTS TO SET DPI: %s' % (i+1))
            break
    sys.stdout.write('SCANNING\n')
    scan_session = device.scan(multiple=False)
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