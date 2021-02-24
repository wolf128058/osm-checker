# Osm-Checker
Don't become a click-sheep and check your osm-files automatically!

*Because not everything on the internet has to be handcrafted.
Especially thousands of standard and rookie mistakes.
Automation can save you lots of time and work .
But be careful(!) it does not save discussions.*

## Python-Scripts
- **[check_facebook.py](check_facebook.py "check_facebook.py")**
    - check for *website*-tags containing facebook-pages
    - move them to *contact:facebook* and check the urls for common mistakes like:
    - country-specific sub- or tld-domains
    - tracking or other needless get-parameters
    - availability (http-statuscode = 200)
    - redirections (trying to find out the final redirection target)
    - read first:
        - [key:website](https://wiki.openstreetmap.org/wiki/Key:website "key:website")
        - [contact:facebook](https://wiki.openstreetmap.org/wiki/Key:contact:facebook "contact:facebook")
        - [Talk:Key:website](https://wiki.openstreetmap.org/wiki/Talk:Key:website "Talk:Key:website")
- **[check_website.py](check_website.py "check_website.py")**
    - check for website-tags missing scheme in url
    - read first:
        - [key:website](https://wiki.openstreetmap.org/wiki/Key:website "key:website")
        - [Talk:Key:website](https://wiki.openstreetmap.org/wiki/Talk:Key:website "Talk:Key:website")


##  Dos and Don'ts 
- check your results responsibly
- do not break the limits (do not make it a mass-editing)