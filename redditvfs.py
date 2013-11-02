#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This is a demo/proof of concept for the reddit virtual filesystem
quick-and-dirty
"""
import errno
import fuse
import stat
import time
import urllib2
import json
import praw
import ConfigParser
import sys

fuse.fuse_python_api = (0, 2)

def redditapi(url):
    """
    talks to reddit via url, returns dictionary of response
    should handle rate limiting and caching
    """
    response = urllib2.urlopen(url)
    return json.load(response)

class redditvfs(fuse.Fuse):
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)

    def getattr(self, path):
        """
        returns stat info for file, such as permissions and access times.
        """
        # this should act differently for different files, but here's a sane
        # default so things just work:
        st = fuse.Stat()
        st.st_nlink = 2
        st.st_atime = int(time.time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime
        if path == '/' or path == '/.' or path == '/..':
            st.st_mode = stat.S_IFDIR | 0755
        else:
            st.st_mode = stat.S_IFREG | 0700
        return st

    def readdir(self, path, offset):
        """
        returns a list of directories in requested path
        """
        # add "." and ".." -- all directories have these
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')
        if path == "/":
            # test file
            yield fuse.Direntry('hello_world')
            # current posts in r/osu
            data = redditapi('http://reddit.com/r/osu/hot.json')
            for post in data['data']['children']:
                # '/' is illegal in UNIX filenames
                posttitle = str(post['data']['title']).replace('/',' ')
                yield fuse.Direntry(posttitle)


if __name__ == '__main__':
    # Create a reddit object from praw
    reddit = praw.Reddit(user_agent='redditvfs')

    # Login only if a configuration file is present
    if '-c' in sys.argv:
        # User wants to use the config file, create the parser
        config = ConfigParser.RawConfigParser(allow_no_value=True)

        # Check for default login
        try:
            config.readfp(open('~/.redditvfs.conf'))
            try:
                # Attempt to retrieve the logih information from
                username = config.get('login', 'username')
                password = config.get('login', 'password')

                reddit.login(username=username, password=password)

                print 'Logged in as: ' + username
            except Exception, e:
                # Failed to log in
                print 'Failed to login.'
                pass
        except Exception, e:
            # Configuration file not present, ignore
            pass

    fs = redditvfs()
    fs.parse(errex=1)
    fs.main()
