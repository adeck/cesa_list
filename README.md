# index

- `cesa_list`
  - Very Important Note (please read!)
  - Usage

# `cesa_list`

This spiders the centos-announce mailing list archives and extracts CESA
information for easy postprocessing.

## Very Important Note (please read!)

Despite the fact that they appear form-generated, CESA announcement e-mails are
put together manually. Normally the difference is irrelevant, but occasionally
it has a significant effect. For example [this search][moderte] for CESAs with
a stated severity of "Moderte" brings up:

- [CESA-2015:0716][]
- [CESA-2015:0728][]
- [CESA-2015:2505][] (NOTE: This CESA is given to prove the above point, but to clarify it would not be found be `cesa_list`, because `cesa_list` doesn't spider the centos-cr-announce mailing list.)

The corresponding RHSAs, however, have the correct severity. In future I may
rewrite this to get severity data from the RH site, but given how rare this
phenomenon is, and the fact that this rewrite would mean an additional HTTPS
request for each CESA, even if I did add this functionality I wouldn't make it
the default. On a related note, the four actual severity levels
are explained [here][rh-severity].

Given the fact that some portions of these announcements are manually copied,
it's entirely possible that there are other typos I've missed (e.g. in package
names, centos versions, etc.). That being the case, it may be worthwhile to
minimize risk by simply directly converting from CESA IDs to RHSA IDs and then
getting most other information (affected packages, affected CentOS / RH versions,
severity) from the RH site.

<!-- TODO - rewrite what's below -->

a simple tool for processing CESA information
what do I want this thing to be able to do?
- given (all of these are optional)
  - daterange -- default: last two months
  - centos major version
  - severity
  - package name
- get 
  - list of CESAs matching the given criteria
  - s.t. a CESA is:
    - CESA ID
    - RHSA ID
    - severity
    - package name
    - announcement date
    - CESA announcement URL

USAGE GUIDE:
- basic functionality
 - list installed packages
   * rpm -qa --qf "%{name}\n"
 - list packages requiring updates
   * yum check-update

[moderte]: https://duckduckgo.com/?q=site:lists.centos.org/+CESA+%2B%22Moderte%22
[CESA-2015:0716]: https://lists.centos.org/pipermail/centos-announce/2015-April/021030.html
[CESA-2015:0728]: https://lists.centos.org/pipermail/centos-announce/2015-April/021020.html
[CESA-2015:2505]: https://lists.centos.org/pipermail/centos-cr-announce/2015-December/002721.html
[rh-severity]: https://access.redhat.com/security/updates/classification/

