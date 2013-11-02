redditVFS
========

Access reddit through a virtual file system.

Description
-----------
**reddivfs** is a FUSE-based filesystem that allows the user to read, post, and explore the content aggregation site reddit by maniplulating files and directories. The goal is to provide feature-complete access to the website via your file browser of choice.

Setup
-----
redditvfs runs off Python 2.3. Once Python 2.3 has been installed and all paths are set, redditvfs can then be run without any setup. However, if the user wishes to log in, a config file must be set up.

If a config file is used, but is empty or noncomplete, then redditvfs will prompt the user to input any missing information from the config.

Usage
-----
Default usage is
`./redditvfs.py [options] <mount-point>`

Once redditvfs is running, one can navigate from the mount point like a regular file system.

File System
-----------

The top-level mountpoint holds several directories and any config files, like so.

        user1.config
        r/
        u/
        m/

`r/` holds different subreddits. Subreddits can be subscribed or unsubscribed by `rm -r` the subreddit directory to unsubscribe, and 'mkdir <subreddit name>` to subscribe.

Inside each subreddit directory, each post is another directory which contains a file with the post contents and all comments.

`u/` holds user information. `ls <username>` returns the files
        overview/
        comments/
        submitted/
        gilded/
Each directory holds the relevant comments or submissions as a symlink to the relevant post or comment in r/

`m/` holds the messages of the user in two directories, should one be logged in. One directory, `sent/` holds all sent messages from the user. The other, `inbox/` holds all messages received. To compose a message, a new text file is created in the directory `m/`, with the username of the recipient as the name of the file, and the contents of the file being the contents of the message.

Options
-------
`-c -config [optional-config-file]` Designates a config files that may be empty, noncomplete, or filled out. If no config file is given, `.redditvfs.conf` is used.
`-f -foreground` Forces redditvfs to run in the foreground instead of in daemon mode. Useful for debugging.


Miscellaneous
-------------
