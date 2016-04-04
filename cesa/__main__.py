#!/usr/bin/env python2
#
# NOTE: this program uses `yield` statements, so it only needs
#       enough heap memory for:
#       - the webpage for the current month's centos announcement
#         subject lines, and
#       - the webpage for the current CESA
#       In other words, it's written to use resources pretty efficiently.
# 

from cesa import CESAList, severities
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
      pass # TODO -- raise exception
    return duration
  else:
    raise argparse.ArgumentTypeError("The time window given was not in a valid format. It must match the regex '{}'" % re_str)

def cesa_id(string):
  re_str = r'CESA-(\d+):(\d+)'
  match = re.match(re_str, string)
  if match:
    return string
  else:
    raise argparse.ArgumentTypeError("The CESA ID given was not in a valid format. It must match the regex '{}'" % re_str)


def parse_args(args):
  parser = argparse.ArgumentParser(description='Get CentOS security announcements.')
  parser.add_argument('--window', '-w', metavar='DURATION', type=time_window
    ,help="specifies how far back from the current date to search. Specify days (e.g. '3d'), weeks (e.g. '4w'), months (e.g. '5m'), or years (e.g. '9y'). Uses the average number of days per month and per year over a four-year interval, rounding to the nearest day. So, for example, two years will actually be 731 days (round(365.25 * 2)). Defaults to '2w'"
    ,dest='window'
    ,default='2w')
  parser.add_argument('--severity', '-s', choices=severities
                      ,help='select only those CESAs which are at least the given severity.'
                      ,dest='severity'
                      )
  # TODO -- check date is a possible type
  parser.add_argument('--daterange', '-d', metavar='DATE', type=date, nargs=2
                      ,help='the range of dates to search, from start date (exclusive) to end date (inclusive). Overrides the --window option.'
                      ,dest='dates'
                      )
  parser.add_argument('--after', metavar='CESA_ID', type=cesa_id
                      ,help='ignore all CESA IDs prior to the given ID'
                      ,dest='cesa_id'
                      )
  parser.add_argument('packages', metavar='PACKAGE_NAME', nargs='+'
                      ,help='the list of packages to track'
                      ,dest='packages'
                      ,required=False)
  result = parser.parse_args(args)
  
  # TODO -- validate args
  pass

def create_filter(args):
  # TODO
  pass

# entry point
if __name__ == '__main__':
  # TODO -- create filter given command-line arguments
  def filter(cesa_id, severity, centos_version, pkg_name, cesa_url):
    #return centos_version == '7'
    return True
  cel = CESAList(date.today() - timedelta(days=900), date.today())
  #cel = CESAList(date(2016, 2, 17), date.today())
  anns = cel.get_announcements(filter)
  for a in anns:
    #print [a.cesa_id, a.severity, a.pkg_name, a.date]
    print str([a.cesa_id, a.centos_version, a.pkg_name, a.date])



