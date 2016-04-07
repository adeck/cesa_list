#!/usr/bin/env python2
#
#
# NOTE: this program uses `yield` statements, so it only needs
#       enough heap memory for:
#       - the webpage for the current month's centos announcement
#         subject lines, and
#       - the webpage for the current CESA
#       In other words, it's written to use resources pretty efficiently.
# 

import logging
from cesa import CESAList, severities, corrections
from datetime import date, timedelta
from sys import argv
import argparse
import re

days_per_year = 365.25
days_per_month = days_per_year / 12

def time_window(string):
  # days, weeks, months, years
  re_str = r'(\d+)(d|w|m|y)'
  regex = re.compile(re_str)
  match = regex.match(string)
  if match:
    try:
      size = int(match.group(1))
    except ValueError:
      raise argparse.ArgumentTypeError("Difficulty converting window duration to integer (maybe the value you're using is too large?)")
    timescale = match.group(2)
    duration = None
    if timescale == 'd':
      duration = timedelta(days=size)
    elif timescale == 'w':
      duration = timedelta(weeks=size)
    elif timescale == 'm':
      duration = timedelta(days=int((days_per_month * size) + 0.5))
    elif timescale == 'y':
      duration = timedelta(days=int((days_per_year * size) + 0.5))
    else:
      logging.critical("Somehow the regex library managed to misinterpret the timescale you gave (which was '{}'. This should never happen, but since it did the program must now exit." % timescale)
      sys.exit(os.EX_SOFTWARE)
    return duration
  else:
    raise argparse.ArgumentTypeError("The time window given was not in a valid format. It must match the regex '{}'" % re_str)

def cesa_id(string):
  re_str = r'CESA-(\d+):(\d+)'
  if re.match(re_str, string):
    return string
  else:
    raise argparse.ArgumentTypeError("The CESA ID given was not in a valid format. It must match the regex '{}'" % re_str)

def cesa_format(string):
  re_str = r'(id|rhid|package|severity|c_version|date|url)(?:,\1)*'
  if re.match(re_str, string):
    return string.split(',')
  raise argparse.ArgumentTypeError("The format string given was invalid. It must match the regex '{}'" % re_str)


def date_str(string):
  try:
    s = map(int, string.split('-'))
    return date(year=s[0], month=s[1], day=s[2])
  except Exception:
    raise argparse.ArgumentTypeError("Dates must be in the format year-month-day, where 'month' is an integer in the range 1-12")
    

def parse_args(args):
  parser = argparse.ArgumentParser(description='Get CentOS security announcements.')
  parser.add_argument('--window', '-w', metavar='DURATION', type=time_window
    ,help="specifies how far back from the current date to search. Specify days (e.g. '3d'), weeks (e.g. '4w'), months (e.g. '5m'), or years (e.g. '9y'). Uses the average number of days per month and per year over a four-year interval, rounding to the nearest day. So, for example, two years will actually be 731 days (round(365.25 * 2)). Defaults to '2w'"
    ,dest='window'
    ,default='2w')
  parser.add_argument('--severity', choices=severities
                      ,help='select only those CESAs which are at least the given severity.'
                      ,dest='severity'
                      )
  parser.add_argument('--daterange', metavar='DATE', type=date_str, nargs=2
                      ,help='the range of dates to search, from start date (exclusive) to end date (inclusive). Overrides the --window option.'
                      ,dest='daterange'
                      )
  parser.add_argument('--after', metavar='CESA_ID', type=cesa_id
                      ,help='ignore all CESA IDs prior to (and including) the given ID'
                      ,dest='cesa_id'
                      )
  parser.add_argument('--centos-version','--cv', metavar='CENTOS_VERSION', type=int
                      ,help='the centos major version number to get results for'
                      ,dest='centos_version'
                      )
  formatter_default = 'id,date,c_version,severity,package'
  parser.add_argument('--format', metavar='FORMAT', type=cesa_format
                        ,default=formatter_default
                        ,help= \
"""the comma-separated list of fields to include. The fields are:

'id' the CESA ID associated with the CESA,
'rhid' the RHSA ID associated with the CESA,
'c_version' the centos version associated with the CESA
'package' name of the affected package
'severity' if --correct is specified, guaranteed to be one of 'low', 'moderate', 'important', or 'critical'. Otherwise there may be typos
'date' in the format YYYY-MM-DD (MM is a number from 1 to 12. Neither MM nor DD are padded with leading zeros)
'url' the URL for the announcement.

The default format is """ + formatter_default)
  parser.add_argument('--correct', action='store_true'
                      ,dest='correct_severity'
                      ,help="If a severity level is found which doesn't match any of the known severities, this option forces correction of that severity. In other words, by default, the severity is allowed to be any combination of alpha letters and underscores. However, with this option flag, the program will attempt to recover the actual severity level if an invalid value is found, and if resolving a given severity to a valid value is impossible, the program will exit with a nonzero return code.")
  parser.add_argument('--packages', metavar='PACKAGE_NAME', nargs='+'
                      ,help='the list of packages to track'
                      )
  return parser.parse_args(args)

def get_num(cesa_id):
  # [year, cesa_num]
  return map(args.cesa_id.split('-')[1].split(':'), int)

def create_filter(args):
  cesa_filter = None
  if args.cesa_id is not None:
    cesa_filter = get_num(cesa_id)
  severity_filter = None
  if args.severity is not None:
    severity_filter = severities.index(args.severity)
  centos_version_filter = args.centos_version
  pkg_filter = args.packages
  # cesa.date is None when this is called
  def filter(cesa):
    logging.debug('filtering CESA')
    if cesa_filter is not None:
      [year, cesa_num] = get_num(cesa.cesa_id)
      if cesa_filter[0] > year \
          or (cesa_filter[0] == year and cesa_filter[1] >= cesa_num):
        logging.debug('CESA filtered because of CESA ID')
        return False
    if severity_filter is not None \
        and cesa.severity in severities \
        and severity_filter < severities.index(cesa.severity):
      logging.debug('CESA filtered because of severity')
      return False
    if centos_version_filter is not None \
          and int(cesa.centos_version) != centos_version_filter:
      logging.debug('CESA filtered because of centos version')
      return False
    if pkg_filter is not None and cesa.pkg_name not in pkg_filter:
      logging.debug('CESA filtered because of package name')
      return False
    return True
  return filter

def print_cesa(cesa, formatter):
  mapping = {
    'id'          : cesa.cesa_id
    ,'rhid'       : cesa.get_rhsa_id()
    ,'c_version'  : cesa.centos_version
    ,'package'    : cesa.pkg_name
    ,'severity'   : cesa.severity
    ,'date'       : cesa.date
    ,'url'        : cesa.url
  }
  for k in mapping:
    mapping[k] = str(mapping[k])
  result = ''
  sep=''
  for field in formatter:
    result += sep + mapping[field]
    sep = ' '
  print result

# entry point
if __name__ == '__main__':
  # left here commented out because there is currently no 'debug' flag,
  #logging.basicConfig(filename='list.log', level=logging.DEBUG)
  logging.debug('parsing args')
  args = parse_args(argv[1:])
  if args.correct_severity:
    corrections.append('severity')
  logging.debug('creating filter')
  filter = create_filter(args)
  logging.debug('getting daterange')
  if args.daterange is None:
    logging.debug('got window daterange %s' % args.window)
    cel = CESAList(date.today() - args.window, date.today())
  else:
    logging.debug('got non-window daterange %s to %s'
                  % (args.daterange[0], args.daterange[1]))
    cel = CESAList(args.daterange[0], args.daterange[1])
  logging.debug('getting announcements')
  for a in cel.get_announcements(filter):
    logging.debug('outputting CESA' + str(a))
    print_cesa(a, args.format)



