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
import praw

fuse.fuse_python_api = (0, 2)

def sanitize_filepath(path):
    """
    Converts provided path to legal UNIX filepaths.
    """
    # '/' is illegal
    path = path.replace('/',' ')
    # Direntry() doesn't seem to like non-ascii
    path = path.encode('ascii', 'ignore')
    return path

class redditvfs(fuse.Fuse):
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)

    def getattr(self, path):
        """
        returns stat info for file, such as permissions and access times.
        """
        # default nlink and time info
        st = fuse.Stat()
        st.st_nlink = 2
        st.st_atime = int(time.time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime
        # set if filetype and permissions
        if path.split('/')[-1] == '.' or path.split('/')[-1] == '..'
            st.st_mode = stat.S_IFDIR | 0444
        elif path in ['/', '/u', '/r' ]:
            st.st_mode = stat.S_IFDIR | 0444
        else:
            st.st_mode = stat.S_IFREG | 0444
        return st

    def readdir(self, path, offset):
        """
        returns a list of directories in requested path
        """

        # Every directory has '.' and '..'
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        # the root just has high-level items:
        # - /r (for subreddits)
        # - /u (for users)
        if path == '/':
            yield fuse.Direntry('u')
            yield fuse.Direntry('r')
        elif path == '/r':
            # if user is logged in, populate with get_my_subreddits
            # otherwise, default to frontpage
            # TODO: check if logged in
            # TODO: figure out how to get non-logged-in default subreddits,
            # falling back to get_popular_subreddits
            r = praw.Reddit(user_agent="redditvfs")
            for subreddit in r.get_front_page():
                yield fuse.Direntry(sanitize_filepath(subreddit.title))

if __name__ == '__main__':
    fs = redditvfs()
    fs.parse(errex=1)
    fs.main()
