# -*- encoding=utf8 -*-
__author__ = "Jason"

from airtest.core.api import *

# dev = connect_device("android://127.0.0.1:5037/?cap_method=MINICAP&ori_method=MINICAPORI&touch_method=MAXTOUCH")
auto_setup(__file__)

touch(Template(r"tpl1735030019490.png", record_pos=(-0.002, 0.883), resolution=(1440, 3200)))
sleep(5.0)
touch(Template(r"tpl1735030161356.png", record_pos=(0.401, 1.006), resolution=(1440, 3200)))
sleep(5.0)
touch(Template(r"tpl1735030185678.png", record_pos=(0.367, 0.131), resolution=(1440, 3200)))

