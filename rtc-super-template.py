#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''RTC "Super" Template

Copyright (C) 2011
Yosuke Matsusaka
Intelligent Systems Research Institute,
National Institute of Advanced Industrial Science and Technology (AIST),
Japan
All rights reserved.
Licensed under the Eclipse Public License -v 1.0 (EPL)
http://www.opensource.org/licenses/eclipse-1.0.txt
'''

import sys
import os
import optparse
import subprocess
from pprint import pprint
from formula import *

__version__ = '1.00'

def genport(p, iotype):
    global portsdefinition, portsinitialization, portscreation
    valmap = {'porttype': p._type.replace('.', '::'), 'portname': p._name,
              'iotype': iotype}
    portsdefinition += '''\
  %(porttype)s m_%(portname)s;
  %(iotype)sPort<%(porttype)s> m_%(portname)s%(iotype)s;
''' % valmap
    portsinitialization += ''', m_%(portname)s%(iotype)s("%(portname)s", m_%(portname)s)''' \
        % valmap
    portscreation += '''\
  add%(iotype)sPort("%(portname)s", m_%(portname)s%(iotype)s);
''' % valmap

def createlogic_recur(f):
    if isinstance(f.lhs, Formula):
        lhslogic = createlogic_recur(f.lhs)
    elif isinstance(f.lhs, Symbol):
        lhslogic = 'm_%s.data' % (f.lhs._name,)
    else:
        lhslogic = f.lhs.__str__()
    if isinstance(f.rhs, Formula):
        rhslogic = createlogic_recur(f.rhs)
    elif isinstance(f.lhs, Symbol):
        rhslogic = 'm_%s.data' % (f.rhs._name,)
    else:
        rhslogic = f.rhs.__str__()
    return '(%s %s %s)' % (lhslogic, f.type, rhslogic)

def main():
    global portsdefinition, portsinitialization, portscreation

    usage = '''Usage: %prog [options]

RTC "Super" Template:
Generate high-performance RT-Component from simple formula.

This utility script will generate high-performance (C++ based) RT-Component
from simple one-line formula.

Example:
$ %prog --name SampleFormula --formula \\
        "out:RTC.TimedLong = in1:RTC.TimedLong + in2:RTC.TimedLong"
'''
    parser = optparse.OptionParser(usage=usage, version=__version__)
    parser.add_option('-n', '--name', dest='name', action='store',
            type='string', default='Formula',
            help='Name of the RT-Component. ' \
            '[Default: %default]')
    parser.add_option('-f', '--formula', dest='formula', action='store',
            type='string', default='out:RTC.TimedLong = in1:RTC.TimedLong + in2:RTC.TimedLong',
            help='The formula. ' \
            '[Default: %default]')

    options, args = parser.parse_args()

    name = options.name
    formula = options.formula

    parser = FormulaParser()
    f = parser.parse(formula)
    if f.type != '=':
        print 'Input formula has to be in assignment form.'
        return(1)
    
    portsdefinition = ''
    portsinitialization = ''
    portsreinitialization = ''
    portscreation = ''
    logic = ''

    outports = []
    if isinstance(f.lhs, Formula):
        outports = f.lhs.getsymbols()
    elif isinstance(f.lhs, Symbol):
        outports = [f.lhs]
    for p in outports:
        genport(p, 'Out')
        valmap = {'porttype': p._type.replace('.', '::'), 'portname': p._name}
        portsdefinition += '  %(porttype)s m_%(portname)s_prev;\n' % valmap

    inports = []
    if isinstance(f.rhs, Formula):
        inports = f.rhs.getsymbols()
    elif isinstance(f.rhs, Symbol):
        inports = [f.rhs]
    for p in inports:
        genport(p, 'In')
        
    for p in inports:
        logic += '''\
  if (m_%(portname)sIn.isNew()) {
    m_%(portname)sIn.read();
  }
''' % {'portname': p._name}
    logic += '  %s;\n' % (createlogic_recur(f)[1:-1],)
    for p in outports:
        logic += '''\
  if (m_%(name)s_prev.data != m_%(name)s.data) {
    m_%(name)s_prev.data = m_%(name)s.data;
    m_%(name)sOut.write();
  }
''' % {'name': p._name}

    tmpl = """\
#include <rtm/idl/BasicDataTypeSkel.h>
#include <rtm/Manager.h>
#include <rtm/DataFlowComponentBase.h>
#include <rtm/CorbaPort.h>
#include <rtm/DataInPort.h>
#include <rtm/DataOutPort.h>

using namespace RTC;

class %(name)s
  : public RTC::DataFlowComponentBase
{
 public:
  %(name)s(RTC::Manager* manager);
  virtual RTC::ReturnCode_t onInitialize();
  virtual RTC::ReturnCode_t onActivated(RTC::UniqueId ec_id);
  virtual RTC::ReturnCode_t onExecute(RTC::UniqueId ec_id);
 private:
%(portsdefinition)s
};

extern "C"
{
  DLL_EXPORT void %(name)sInit(RTC::Manager* manager);
};

%(name)s::%(name)s(RTC::Manager* manager): RTC::DataFlowComponentBase(manager)%(portsinitialization)s
{
}

RTC::ReturnCode_t %(name)s::onInitialize()
{
%(portscreation)s
  return RTC::RTC_OK;
}

RTC::ReturnCode_t %(name)s::onActivated(RTC::UniqueId ec_id)
{
%(portsreinitialization)s
  return RTC::RTC_OK;
}

RTC::ReturnCode_t %(name)s::onExecute(RTC::UniqueId ec_id)
{
%(logic)s
  return RTC::RTC_OK;
}

static const char* %(name)s_spec[] =
  {
    "implementation_id", "%(name)s",
    "type_name",         "%(name)s",
    "description",       "%(formula)s",
    "version",           "1.0.0",
    "vendor",            "automatically generated by rtc -super- template",
    "category",          "formula",
    "activity_type",     "PERIODIC",
    "kind",              "DataFlowComponent",
    "max_instance",      "100",
    "language",          "C++",
    "lang_type",         "compile",
  };

extern "C"
{
  void %(name)sInit(RTC::Manager* manager)
  {
    coil::Properties profile(%(name)s_spec);
    manager->registerFactory(profile,
                             RTC::Create<%(name)s>,
                             RTC::Delete<%(name)s>);
  }
};
"""

    fp = open('%s.cc' % (name,), 'w')
    print >>fp, tmpl % {'name': name, 'formula': formula,
                        'portsdefinition': portsdefinition,
                        'portscreation': portscreation,
                        'portsinitialization': portsinitialization,
                        'portsreinitialization': portsreinitialization,
                        'logic': logic,
                        }
    fp.close()
    
    cmdline = 'g++ -shared -o %(name)s.so `rtm-config --cflags` `rtm-config --libs` %(name)s.cc' % {'name': name}
    
    subprocess.Popen(['/bin/sh', '-c', cmdline])
    return(0)

if __name__ == '__main__':
    sys.exit(main())

