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


import os
import sys
import logging
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
version = '1.0'
severities = [
  'critical'
  ,'important'
  ,'moderate'
  ,'low'
]

headers  = {
  'User-Agent' : 'CESA List Spider/' + version
}
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

corrections = []

class CESA:
  def __init__(self):
    self.cesa_id = None
    self.centos_version = None
    self.date = None
    self.pkg_name = None
    self.url = None
    self.severity = None
  def finalize(self):
    if None in [self.cesa_id
            ,self.centos_version
            ,self.date
            ,self.pkg_name
            ,self.url
            ,self.severity]:
      logging.critical('attempted to finalize CESA: {}'.format(self))
      sys.exit(os.EX_SOFTWARE)
    return self

  def set_severity(self, severity):
    if severity in severities:
      self.severity = severity
    else:
      logging.warning("CESA with ID '{}' had the unrecognized severity level '{}'"
                      .format(self.cesa_id, self.severity))
      if 'severity' in corrections:
        self.severity = self.correct_severity(severity)
      else:
        self.severity = severity
    
  def set_date(self, year, month):
    logging.debug("retrieving page for '{}' at URL '{}'"
                  .format(self.cesa_id, self.url))
    body = self._get_page()
    day = cesa_date_regex.match(body.i.string)
    if not day:
      logging.critical("Date not found on webpage for {}".formatcesa_id)
      sys.exit(os.EX_NOTFOUND)
    self.date = date(year, month, int(day.group(1)))
    return self
  def _get_page(self):
    try:
      req = urllib2.Request(self.url, headers=headers)
      response = urllib2.urlopen(req)
      if response.getcode() == 200:
          return BeautifulSoup(response.read(), 'html.parser').body
      logging.critical("CESA associated with URL '{}' yielded non-200 HTTP response".format(self.url))
      sys.exit(os.EX_NOTFOUND)
    except Exception, e:
      logging.critical('Exception: {}'.format(str(e)))
      sys.exit(os.EX_UNAVAILABLE)


  def correct_severity(self, severity):
    result = severity
    if severity == 'moderte':
      result = 'moderate'
    if severity is result:
      logging.error("CESA with ID '{}' could not correct severity '{}' to a known value"
                     .format(self.cesa_id, severity))
    else:
      logging.warning("CESA with ID '{}' had the severity corrected from '{}' to '{}'"
                     .format(self.cesa_id, severity, result))
    return result
    
  def get_rhsa_id(self):
    if self.cesa_id is None:
      return None
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
    logging.info("creating CESAList object for daterange '{}' to '{}'"
                  .format(start_date, end_date))
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
    logging.info("creating CESAMonth object for daterange month of '{}'"
                  .format(date))
    self.date = date

  def get_announcements(self, filter=None):
    url = self._get_url()
    logging.debug("getting URL '{}'".format(url))
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    if response.getcode() == 200:
      try:
        body = BeautifulSoup(response.read(), 'html.parser').body
        posts = body.find_all('ul')[1]
      except Exception, e:
        logging.critical("Failed to read or parse response for CESAs of {} {}"
                       .format(self._month(), self.date.year))
        sys.exit(os.EX_NOTFOUND)
      for post in posts.find_all('li'):
        match = cesa_regex.match(post.a.string)
        if match:
          logging.debug("got CESA string: '{}'".format(post.a.string))
          cesa = self._init_cesa(match, post)
          if filter is None or filter(cesa):
            try:
              yield cesa.set_date(self.date.year, self.date.month).finalize()
            except Exception, e:
              logging.critical("Failed to get '{}', exception: {}"
                              .format(cesa, str(e)))
              sys.exit(os.EX_SOFTWARE)
    else:
      logging.critical("Got a non-200 response code while attempting to list"
                        " CESAs for {}, {}"
                        .format(self._month(), self.date.year))
      sys.exit(os.EX_NOTFOUND)

  def _init_cesa(self, match, post):
    cesa = CESA()
    [cesa_id, severity, centos_version, pkg_name] = map(match.group, xrange(1,5))
    cesa.set_severity(severity.lower())
    cesa.cesa_id = cesa_id
    cesa.centos_version = centos_version
    cesa.pkg_name = pkg_name
    cesa.url = self._get_cesa_url(post)
    return cesa

  def _get_url(self):
    url = "https://lists.centos.org/pipermail/centos-announce/{}-{}/date.html"
    return url.format(self.date.year, self._month())

  def _get_cesa_url(self, post):
    url = "https://lists.centos.org/pipermail/centos-announce/{}-{}/{}"
    return url.format(self.date.year, self._month(), post.a['href'])

  def _month(self):
    return calendar.month_name[self.date.month]

