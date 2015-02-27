# -*- coding: utf-8 -*-
import sys
import PIL.Image
from pyinsane.abstract import Scanner


__author__ = 'viruzzz-kun'


def main():
    dev_name = sys.argv[1]
    print('DEVICE:%s' % dev_name)
    device = Scanner(dev_name)
    print('SCANNER')
    scan_session = device.scan(multiple=False)
    try:
        while True:
            scan_session.scan.read()
    except EOFError:
        pass
    print('ACQUIRED')
    img = scan_session.images[0]
    w, h = img.size
    new_w = 2560
    new_h = int(h * (float(new_w) / w))
    image = img.resize((new_w, new_h), PIL.Image.LANCZOS)
    print('DATA')
    image.save(sys.stdout, 'png')


if __name__ == "__main__":
    main()