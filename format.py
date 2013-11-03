import praw
import textwrap
import time
import codecs


def format_sub_content(submission):
    """return formatted submission without comments as a String"""
    text = []
    indent = 3
    wrap = textwrap.TextWrapper(initial_indent=indent*' '+'|', subsequent_indent=indent*' '+'|')
    br = indent * ' ' + '-' * (79-indent)
    text.append(br)
    text += wrap.wrap(submission.title)
    text.append(br)
    if post.selftext:
        text += wrap.wrap('\n' + submission.selftext + '\n')
        text.append(br)
    d = get_info_dict(submission)
    formatted = "%(author)s %(time)s ago\n"\
    +"%(score)d points (%(ups)d|%(downs)d) id:%(id)s"
    text += wrap.wrap(formatted % d)
    text.append(br)
    return '\n'.join(text)+'\n'

def format_submission(submission):
    """return formatted submission and all comments as [String]"""
    text = [format_sub_content(submission)] +\
             ['\n'.join(format_comment(c)) for c in submission.comments]
    return '\n'.join(text)+'\n'

def get_info_dict(comsub):
    d = {}
    d['author'] = comsub.author if comsub.author else "DELETED"
    d['time'] = time.ctime(comsub.created)
    d['score'] = comsub.score
    d['ups'] = comsub.ups
    d['downs'] = comsub.downs
    d['id'] = comsub.id
    return d

def format_comment(comment, depth=0):
    """returns formatted comment + children as a [String]""" 
    indent = 2
    base_ind=4
    indent += depth * base_ind
    if isinstance(comment, praw.objects.MoreComments):
        return [' '*indent + "More..."]
    text = ['\n\n',get_comment_header(comment, indent),''] 
    text += get_comment_body(comment,indent)
    for child in comment.replies:
        text += format_comment(child, depth+1)
    return text  


def get_comment_header(comment, indent):
    """return formatted header of post"""
    formatted = indent * '-'+ "%(author)s %(time)s ago\n"\
    + indent * ' ' + "%(score)d points (%(ups)d|%(downs)d) id:%(id)s"
    d = get_info_dict(comment)
    return formatted % d 

def get_comment_body(comment, indent):
    """returns formatted body of comment as [String]"""
    indent = indent * ' '
    wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent,
            width=79)
    return wrapper.wrap(comment.body)


def get_top_10(subreddit):
    """utility testing function"""
    r = praw.Reddit('test!')
    sub = r.get_subreddit(subreddit)
    return [post for post in sub.get_top(limit=10)]    

    
#testing code
if __name__=='__main__':
    r = praw.Reddit('test!')
    sub = r.get_subreddit('iama')
    posts = [post for post in sub.get_top(limit=1)]   
    with codecs.open('out.txt', mode='w',encoding='utf-8') as f:
        for post in posts:
            lines = format_sub_content(post) 
            print lines 
