
# Critical

- before adding any new functionality, make the interfaces between existing
  components cleaner
  - write a CESABuilder class, distinct from the CESA class,
  - associate regex constants with the classes which use them, rather than
    the entire file
  - create a simple Webpage class to abstract away calls to urllib2
    and BeautifulSoup
    - create subclasses for CESAMonthWebpage and CESAWebpage which simply
      retrieve strings and don't do any regex processing on those strings.
      So, ideally, if this needed to be rewritten because URLs changed or
      webpage structures changed, only the *Webpage classes would need
      to be changed, while CESAMonth and CESA would still be fine
  - the 'filter' def
    - should be renamed so it doesn't shadow the global builtin
    - should be changed from a function to a list of functions which all
      take only one argument, a CESABuilder, and return a bool to indicate
      whether the given CESABuilder should continue to be built
  - remove all mutable global state s.t. no method / function
    can have side effects which affect behavior of enclosing scopes.
    So, no side effects apart from:
    - HTTP(S) requests
    - logger entries
    - changes to state in 'self' or subfields of 'self'

# Important

- if subject line contains 'CESA' and '[CentOS-announce]' (case insensitive)
  but doesn't match the CESA regex, issue a warning to the logger

# Moderate

- figure out how to remove all arguments before the program name so that
  if someone calls the program as ./cesa/__main__.py or as python cesa
  it will always fail on at least one type of invocation
- create debugging options (e.g. 'create logfile', 'log to stderr', 'set
  loglevel')
- if severity is an unrecognized value, try to cross-check the
  corresponding RHSA before attempting heuristics
  - if there are any issues resolving the RHSA link or parsing the response,
    issue an ERROR to the logger (but don't terminate)
- do a better job of distinguishing between Exception types (e.g. URLError,
  ParseError, etc.) to generate more helpful error messages
- allow filtering for multiple centos versions

# Low

- check POSIX spec for short option flags to ensure there are no conflicts
  with POSIX flags, then select short flags accordingly
- provide an option to compute Damerau distance and guess severity IFF
  Damerau distance is low enough (e.g. 1 for "low", 2 for the others: moderate,
  important, and critical).
- add an '--ignore-errors' flag s.t. failed requests or malformed
  entries do not cause immediate program termination. Return codes and
  logger messages should still indicate error, however
- add more featureful formatting syntax


