import praw
import textwrap
import time

def format_submission(submission):
    """return formatted submission and all comments as [String]"""
    pass 

def format_comment(comment, depth=0):
    """returns formatted comment + children as [String]""" 
    indent = 2
    base_ind=4
    indent += depth * base_ind
    text = ['\n\n',get_header(comment, indent),'']+get_body(comment,indent)
    for child in comment.replies:
        text += format_comment(child, depth+1)
    return text


def get_header(comment, indent):
    """return formatted header of post"""
    return indent * '-' + "%(author)s %(score)d points %(time)s ago"\
    " (%(ups)d|%(downs)d) id:%(id)s" % \
    {"author":  comment.author if  comment.author else "DELETED",
     "score": comment.score, "ups": comment.ups, "downs": comment.downs,
     "time": time.ctime(comment.created), "id": comment.id}

def get_body(comment, indent):
    """returns formatted body of comment as [String]"""
    indent = indent * ' '
    wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent,
            width=79)
    return wrapper.wrap(comment.body)

    


    
#testing code
if __name__=='__main__':
    r = praw.Reddit('test!')
    sub = r.get_subreddit('osu')
    posts = [post for post in sub.get_top(limit=10)]   
    for post in posts:
        for comment in post.comments:
            for item in format_comment(comment):
                print item
