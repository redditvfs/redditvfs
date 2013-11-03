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
import getpass
import ConfigParser
import sys
import urllib2
import format

fuse.fuse_python_api = (0, 2)

content_stuff = ['thumbnail', 'flat', 'votes', 'content', 'reply']


def sanitize_filepath(path):
    """
    Converts provided path to legal UNIX filepaths.
    """
    # '/' is illegal
    path = path.replace('/', '_')
    # Direntry() doesn't seem to like non-ascii
    path = path.encode('ascii', 'ignore')
    return path


class redditvfs(fuse.Fuse):
    def __init__(self, reddit=None, username=None, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)

        if reddit is None:
            raise Exception('reddit must be set')

    def rmdir(self, path):
        if len(path.split('/')) == 3 and reddit.is_logged_in:
            reddit.unsubscribe(path.split('/')[-1:][0])
            return
        else:
            return -errno.ENOSYS

    def mkdir(self, path, mode):
        if len(path.split('/')) == 3 \
                and path.split('/')[-1:][0][-4:] == '.sub' \
                and reddit.is_logged_in:
            reddit.subscribe(path.split('/')[-1:][0][:-4])
            return
        else:
            return -errno.ENOSYS

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

        # pretend to accept editor backup files so they don't complain,
        # although we don't do anything with it.
        last_word = path.split(' ')[-1].split('/')[-1]
        if last_word.find('.') != -1 or last_word.find('~') != -1:
            st.st_mode = stat.S_IFDIR | 0777
            return st

        # everything defaults to being a normal file unless explicitly set
        # otherwise
        st.st_mode = stat.S_IFREG | 0444

        # useful information
        path_split = path.split('/')
        path_len = len(path_split)

        # "." and ".."
        if path_split[-1] == '.' or path_split[-1] == '..':
            # . and ..
            st.st_mode = stat.S_IFDIR | 0555
            return st

        # top-level directories
        if path in ['/', '/u', '/r']:
            st.st_mode = stat.S_IFDIR | 0555
            return st

        # r/*/ - subreddits
        if path_split[1] == 'r' and path_len == 3:
            # check for .sub directories for subscribing
            if reddit.is_logged_in():
                if path.split('/')[-1:][0][-4:] == '.sub':
                    my_subs = [sub.display_name.lower() for sub in
                               reddit.get_my_subreddits()]
                    if (path.split('/')[-1:][0][:-4]).lower() not in my_subs:
                        st = -2
                    else:
                        st.st_mode = stat.S_IFDIR | 0555
                else:
                    st.st_mode = stat.S_IFDIR | 0555
            else:
                # normal subreddit
                st.st_mode = stat.S_IFDIR | 0555
            return st

        # r/*/* - submissions
        if path_split[1] == 'r' and path_len == 4:
            st.st_mode = stat.S_IFDIR | 0555
            return st

        # r/*/*/[vote, etc] - content stuff in submission
        if (path_split[1] == 'r' and path_len == 5 and path_split[-1] in
                content_stuff):
            st.st_mode = stat.S_IFREG | 0444
            post_id = path_split[3].split(' ')[-1]
            post = reddit.get_submission(submission_id = post_id)
            formatted = ''
            if path_split[-1] == 'content':
                formatted = format.format_sub_content(post)
                formatted = formatted.encode('ascii', 'ignore')
            elif path_split[-1] == 'votes':
                formatted = str(post.score) + '\n'
            elif path_split[-1] == 'flat':
                formatted = format.format_submission(post)
                formatted = formatted.encode('ascii', 'ignore')
            elif (path_split[-1] == 'thumbnail' and 'thumbnail' in dir(post)
                    and post.thumbnail != '' and post.thumbnail != 'self'):
                f = urllib2.urlopen(post.thumbnail)
                if f.getcode() == 200:
                    formatted = f.read()
            elif path_split[-1] == 'reply':
                st.st_mode = stat.S_IFREG | 0666
            st.st_size = len(formatted)
            return st

        # r/*/*/** - comment post
        if (path_split[1] == 'r' and path_len > 4 and path_split[-1] not in
                content_stuff and path.split('/')[-1:][0][-1:] != '_'):
            st.st_mode = stat.S_IFDIR | 0555
            return st

        # user link
        if (path_split[1] == 'r' and path_len > 4 and path_split[-1] not in
                content_stuff and path.split('/')[-1:][0][-1:] == '_'):
            st.st_mode = stat.S_IFLNK | 0777
            return st

        # r/*/*/** - comment directory
        if (path_split[1] == 'r' and path_len > 5 and path_split[-1] not in
                content_stuff):
            st.st_mode = stat.S_IFDIR | 0555
            return st

        # r/*/*/** - comment stuff
        if (path_split[1] == 'r' and path_len > 5 and path_split[-1] in
                content_stuff):
            st.st_mode = stat.S_IFREG | 0444
            post = get_comment_obj(path)
            formatted = ''
            if path_split[-1] == 'content':
                formatted = format.format_comment(post, recursive=False)
                formatted = formatted.encode('ascii', 'ignore')
            elif path_split[-1] == 'votes':
                formatted = str(post.score) + '\n'
            elif path_split[-1] == 'flat':
                formatted = format.format_comment(post, recursive=True)
                formatted = formatted.encode('ascii', 'ignore')
            elif path_split[-1] == 'reply':
                st.st_mode = stat.S_IFREG | 0666
            st.st_size = len(formatted)
            return st

        # u/* - user
        if path_split[1] == 'u' and path_len == 3:
            st.st_mode = stat.S_IFDIR | 0555
            return st

        # u/*/* - user stuff (comments, submitted, etc)
        if path_split[1] == 'u' and path_len == 4:
            st.st_mode = stat.S_IFDIR | 0555
            return st

        # u/*/*/* - links (comment, submitted, etc)
        elif (path_split[1] == 'u' and path_len == 5):
            st.st_mode = stat.S_IFLNK | 0777
            return st

    def readlink(self, path):
        numdots = len(path.split('/'))
        dots=''
        if path.split('/')[-1:][0][-1:] == '_' and len(path.split('/'))>=5:
            #if this is a userlink
            numdots-=2
            while (numdots>0):
                dots+='../'
                numdots-=1
            return dots+'u/'+path.split('/')[-1:][0][11:-1]
        if path.split('/')[1] == 'u' and len(path.split('/')) == 5:
            numdots-=2
            while (numdots > 0):
                dots+='../'
                numdots-=1
            sub =  get_comment_obj(path).submission()
            #TODO fix this into the actual path.
            return path
            #return dots+'r/' +subname + '/'+postname+'/'+path.split('/')[-1:][0]


    def readdir(self, path, offset):
        """
        returns a list of directories in requested path
        """

        # Every directory has '.' and '..'
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        # TODO: maybe make this configurable later
        # cut-off length on items with id to make things usable for end-user
        pathmax = 50

        path_split = path.split('/')
        path_len = len(path_split)

        if path == '/':
            # top-level directory
            yield fuse.Direntry('u')
            yield fuse.Direntry('r')
        elif path_split[1] == 'r':
            if path_len == 2:
                # if user is logged in, populate with get_my_subreddits
                # otherwise, default to frontpage
                # TODO: figure out how to get non-logged-in default subreddits,
                # falling back to get_popular_subreddits
                if reddit.is_logged_in():
                    for subreddit in reddit.get_my_subreddits():
                        dirname = sanitize_filepath(subreddit.url.split('/')[2])
                        yield fuse.Direntry(dirname)
                else:
                    for subreddit in reddit.get_popular_subreddits():
                        dirname = sanitize_filepath(subreddit.url.split('/')[2])
                        yield fuse.Direntry(dirname)
            elif path_len == 3:
                # posts in subreddits
                subreddit = path_split[2]
                # TODO: maybe not hardcode limit?
                for post in reddit.get_subreddit(subreddit).get_hot(limit=20):
                    filename = sanitize_filepath(post.title[0:pathmax]
                            + ' ' + post.id)
                    yield fuse.Direntry(filename)
            elif path_len == 4:
                # a submission in a subreddit

                post_id = path_split[3].split(' ')[-1]
                post = reddit.get_submission(submission_id = post_id)

                # vote, content, etc
                for file in content_stuff:
                    if file != 'thumbnail':
                        yield fuse.Direntry(file)
                yield fuse.Direntry("_Posted_by_" + str(post.author) + "_")

                if post.thumbnail != "" and post.thumbnail != 'self':
                    # there is a thumbnail
                    yield fuse.Direntry('thumbnail')

                for comment in post.comments:
                    if 'body' in dir(comment):
                        yield fuse.Direntry(
                                sanitize_filepath(comment.body[0:pathmax]
                                    + ' ' + comment.id))
            elif len(path.split('/')) > 4:
                # a comment or a user

                # Can't find a good way to get a comment from an id, but there
                # is a good way to get a submission from the id and to walk
                # down the tree, so doing that as a work-around.

                comment = get_comment_obj(path)

                for file in content_stuff:
                    if file != 'thumbnail':
                        yield fuse.Direntry(file)
                yield fuse.Direntry('_Posted_by_' + str(comment.author)+'_')

                for reply in comment.replies:
                    if 'body' in dir(reply):
                        yield fuse.Direntry(
                                sanitize_filepath(reply.body[0:pathmax]
                                    + ' ' + reply.id))
        elif path_split[1] == 'u':
            if path_len == 2:
                # if user is logged in, show the user.  Otherwise, this empty
                # doesn't have any values listed.
                if reddit.is_logged_in():
                    yield fuse.Direntry(username)
            if path_len == 3:
                yield fuse.Direntry('Overview')
                yield fuse.Direntry('Submitted')
                yield fuse.Direntry('Comments')
            if path_len == 4:
                user = reddit.get_redditor(path_split[2])
                if path_split[3] == 'Overview':
                    for c in enumerate(user.get_overview(limit=10)):
                        yield fuse.Direntry(sanitize_filepath(c[1].body[0:pathmax]
                            + ' ' + c[1].id))
                elif path_split[3] == 'Submitted':
                    for c in enumerate(user.get_submitted(limit=10)):
                        yield fuse.Direntry(sanitize_filepath(c[1].body[0:pathmax]
                            + ' ' + c[1].id))
                elif path_split[3] == 'Comments':
                    for c in enumerate(user.get_comments(limit=10)):
                        yield fuse.Direntry(sanitize_filepath(c[1].body[0:pathmax]
                            + ' ' + c[1].id))

    def read(self, path, size, offset, fh=None):
        path_split = path.split('/')
        path_len = len(path_split)

        if path_split[1] == 'r' and path_len == 5:
            # Get the post
            post_id = path_split[3].split(' ')[-1]
            post = reddit.get_submission(submission_id = post_id)

            formatted = ''
            if path_split[-1] == 'content':
                formatted = format.format_sub_content(post)
                formatted = formatted.encode('ascii', 'ignore')
            elif path_split[-1] == 'votes':
                formatted = str(post.score) + '\n'
            elif path_split[-1] == 'flat':
                formatted = format.format_submission(post)
                formatted = formatted.encode('ascii', 'ignore')
            elif (path_split[-1] == 'thumbnail' and post.thumbnail != '' and
                    post.thumbnail != 'self'):
                f = urllib2.urlopen(post.thumbnail)
                if f.getcode() == 200:
                    formatted = f.read()
            return formatted[offset:offset+size]
        elif path_split[1] == 'r' and path_len > 5:
            # Get the comment
            post = get_comment_obj(path)
            if path_split[-1] == 'content':
                formatted = format.format_comment(post, recursive=False)
                formatted = formatted.encode('ascii', 'ignore')
            elif path_split[-1] == 'votes':
                formatted = str(post.score) + '\n'
            elif path_split[-1] == 'flat':
                formatted = format.format_comment(post, recursive=True)
                formatted = formatted.encode('ascii', 'ignore')
            return formatted[offset:offset+size]
        elif path.split('/')[1] == 'u':
            # TODO user handling
            pass

        return -errno.ENOSYS

    def truncate(self, path, len):
        """
        there is no situation where this will actually be used
        """
        pass

    def write(self, path, buf, offset, fh=None):
        """
        Handles voting, content creation, and management. Requires login
        """
        if not reddit.is_logged_in():
            return errno.EACCES

        path_split = path.split('/')
        path_len = len(path_split)

        # Voting
        if path_split[1] == 'r' and path_len >= 5 and path_split[-1] == 'votes':
            # Get the post or comment
            if path_len > 5:
                post = get_comment_obj(path)
            else:
                post_id = path_split[-2].split(' ')[-1]
                post = reddit.get_submission(submission_id=post_id)

            # Determine what type of vote and place the vote
            vote = int(buf)
            if vote == 0:
                post.clear_vote()
            elif vote > 0:
                post.upvote()
            elif vote < 0:
                post.downvote()
            return len(buf)

        # Reply to submission
        if path_split[1] == 'r' and path_len == 5 and\
                path_split[-1] == 'reply':
            post_id = path_split[-2].split(' ')[-1]
            post = reddit.get_submission(submission_id=post_id)
            post.add_comment(buf)
            return len(buf)

        # Reply to comments
        if path_split[1] == 'r' and path_len > 5 and\
                path_split[-1] == 'reply':
            post = get_comment_obj(path)
            post.reply(buf)
            return len(buf)

        # fake success for editor's backup files        
        return len(buf)

    def create(self, path, flags, mode):
        return errno.EPERM

def get_comment_obj(path):
    """
    given a filesystem path, returns a praw comment object
    """
    # Can't find a good way to get a comment from an id, but there
    # is a good way to get a submission from the id and to walk
    # down the tree, so doing that as a work-around.
    print path
    path_split = path.split('/')
    path_len = len(path_split)
    post_id = path_split[3].split(' ')[-1]
    post = reddit.get_submission(submission_id = post_id)
    for comment in post.comments:
        if comment.id == path_split[4].split(' ')[-1]:
            break
    level = 4
    if path_split[-1] in content_stuff:
        adjust = 2
    else:
        adjust = 1
    while level < path_len - adjust:
        level += 1
        for comment in comment.replies:
            if comment.id == path_split[level].split(' ')[-1]:
                break
    return comment

def login_get_username(config):
    """
    returns the username of the user to login
    """
    try:
        username = config.get('login', 'username')
    except Exception, e:
        # Prompt for username
        username = raw_input("Username: ")
        pass
    return username


def login_get_password(config):
    """
    returns the password of the user to login
    """
    try:
        password = config.get('login', 'password')
    except Exception, e:
        # Prompt for password
        password = getpass.getpass()
        pass
    return password


if __name__ == '__main__':
    # Create a reddit object from praw
    reddit = praw.Reddit(user_agent='redditvfs')

    # Login only if a configuration file is present
    if '-c' in sys.argv:
        # Remove '-c' from sys.argv
        sys.argv.remove('-c')

        # User wants to use the config file, create the parser
        config = ConfigParser.RawConfigParser(allow_no_value=True)

        # Check for default login
        try:
            config.read('~/.redditvfs.conf')
        except Exception, e:
            pass
        finally:
            username = login_get_username(config=config)
            password = login_get_password(config=config)
            try:
                reddit.login(username=username, password=password)
                print 'Logged in as: ' + username
            except Exception, e:
                print e
                print 'Failed to login'
    else:
        username = None

    fs = redditvfs(reddit=reddit, username=username)
    fs.parse(errex=1)
    fs.main()
