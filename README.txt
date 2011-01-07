Usage: rtc-super-template.py [options]

RTC "Super" Template:
Generate high-performance RT-Component from simple formula.

This utility script will generate high-performance (C++ based) RT-Component
from simple one-line formula.

Example:
$ rtc-super-template.py --name SampleFormula --formula \
        "out:RTC.TimedLong = in1:RTC.TimedLong + in2:RTC.TimedLong"


Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -n NAME, --name=NAME  name of the RT-Component [Default: Formula]
  -f FORMULA, --formula=FORMULA
                        the formula
  -c, --compile         compile the component
  -l HOST, --load=HOST  load the component to the manager
