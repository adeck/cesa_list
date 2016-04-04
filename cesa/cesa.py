#!/usr/bin/env python2
#
# NOTE: this program uses `yield` statements, so it only needs
#       enough heap memory for:
#       - the webpage for the current month's centos announcement
#         subject lines, and
#       - the webpage for the current CESA
#       In other words, it's written to use resources pretty efficiently.
# 

# what do I want this thing to be able to do?
#   - given
#     - daterange
#     - centos major version
#   - get 
#     - list of CESAs within that daterange and targeting that version
#     - s.t. a CESA is:
#       - CESA ID
#       - RHSA ID
#       - severity
#       - package name
#       - announcement date
#       - CESA announcement URL
#
#   USAGE GUIDE:
#   - basic functionality
#     - list installed packages
#       * rpm -qa --qf "%{name}\n"
#     - list packages requiring updates
#       * yum check-update
#    

# TODO -- handle edge cases:
#     - failed to connect to site
#     - got non-200 return code
#     - failed to parse HTML
#     - HTML in unexpected format
#       - at list level
#       - at post level
#       - at RHSA announcement level (if I check that)

import re
from datetime import date, timedelta
from collections import namedtuple
import calendar
import urllib2
try: 
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup

#### BEGIN public constants
severities = [
  'critical'
  ,'important'
  ,'moderate'
  ,'low'
]
#### END public constants

#### BEGIN private constants (here for efficiency reasons
rhsa_url_regex = re.compile(r"https://rhn.redhat.com/errata/(RHSA-\d+-\d+).html")
# weekday, month, day, hour, minute, second, year
cesa_date_regex = re.compile(r"\w+\s+\w+\s+(\d+)\s+\d+:\d+:\d+\s+UTC\s+\d+")
# using \s instead of ' ' because sometimes the same position will contain
#   a tab rather than a space.
# cesa_id, severity, centos_version, pkg_name
cesa_re_str = r'\[CentOS-announce]\s(CESA-\d+:\d+)\s(\w+)\sCentOS\s(\d+)\s((?:\w|[.-])+).*\sSecurity\sUpdate$'
cesa_regex = re.compile(cesa_re_str)
#### END private constants

class CESA:
  def __init__(self, cesa_id, centos_version, severity, pkg_name, date, url):
    self.exceptions = []
    self.cesa_id = cesa_id
    self.centos_version = centos_version
    if severity in severities:
      self.severity = severity
    elif severity == 'moderte':
      # this is a known typo in a few places
      self.severity = 'moderate'
    else:
      self.severity = severity
      # TODO -- append an exception to self.exceptions
    self.date = date
    self.pkg_name = pkg_name
    self.url = url
  def get_rhsa_id(self):
    return self.cesa_id.replace(':','-').replace('CE','RH')
  def __str__(self):
    return str({'cesa_id'   : self.cesa_id
                ,'rhsa_id'  : self.get_rhsa_id()
                ,'centos_version' : self.centos_version
                ,'severity' : self.severity
                ,'date'     : self.date
                ,'package'  : self.pkg_name
                ,'url'      : self.url})

class CESAList:
  # from start_date (exclusive) to end_date (inclusive).
  # if start_date >= end_date, no matches.
  # if start_date == (end_date - 1), only CESAs from end date are listed
  def __init__(self, start_date, end_date):
    self.start_date = start_date + timedelta(days=1)
    self.end_date = end_date

  def get_announcements(self, filter=None):
    cur_date = self.start_date 
    while cur_date <= self.end_date:
      cesa_month = CESAMonth(cur_date)
      for announcement in cesa_month.get_announcements(filter):
        if announcement.date < self.start_date:
          continue
        elif announcement.date <= self.end_date:
          yield announcement
        else: break
      cur_date = date(cur_date.year + (cur_date.month // 12)
                      ,(cur_date.month % 12) + 1
                      ,1)

class CESAMonth:
  def __init__(self, date):
    self.date = date

  def get_announcements(self, filter=None):
    response = urllib2.urlopen(self._get_url())
    if response.getcode() == 200:
      body = BeautifulSoup(response.read(), 'html.parser').body
      posts = body.find_all('ul')[1]
      for post in posts.find_all('li'):
        match = cesa_regex.match(post.a.string)
        if match:
          [cesa_id, severity, centos_version, pkg_name] = map(match.group, xrange(1,5))
          severity = severity.lower()
          cesa_url = self._get_cesa_url(post)
          if filter is None or filter(cesa_id, severity, centos_version, pkg_name, cesa_url):
            yield self._get_cesa(cesa_id, centos_version, severity, pkg_name, cesa_url)
    # TODO -- make this an error instead

  def _get_cesa(self, cesa_id, centos_version, severity, pkg_name, cesa_url):
    body = self._get_cesa_page(cesa_url)
    if body is None:
      # TODO -- raise exception
      pass
    day = cesa_date_regex.match(body.i.string)
    if not day:
      pass
      # TODO raise exception
    release_date = date(self.date.year, self.date.month, int(day.group(1)))
    return CESA(cesa_id = cesa_id
                ,centos_version = centos_version
                ,severity = severity
                ,pkg_name = pkg_name
                ,url = cesa_url
                ,date = release_date
                )

  def _get_url(self):
    url = "https://lists.centos.org/pipermail/centos-announce/{}-{}/date.html"
    return url.format(self.date.year, self._month())

  def _get_cesa_url(self, post):
    url = "https://lists.centos.org/pipermail/centos-announce/{}-{}/{}"
    return url.format(self.date.year, self._month(), post.a['href'])

  def _month(self):
    return calendar.month_name[self.date.month]

  def _get_cesa_page(self, url):
    response = urllib2.urlopen(url)
    if response.getcode() == 200:
      return BeautifulSoup(response.read(), 'html.parser').body
    # TODO -- raise exception
    return None


