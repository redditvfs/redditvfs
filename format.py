import praw
import textwrap
import time
import codecs

wrapper = textwrap.TextWrapper()
def format_submission(submission):
    """return formatted submission and all comments as [String]"""
    text = []
    text.append(submission.title)
    text.append(get_info_str(submission))

    text = '\n'.join(text)
    text = [text] + ['\n'.join(format_comment(c)) for c in submission.comments]
    return '\n'.join(text)

def get_info_str(comsub):
    d = {}
    d['author'] = comsub.author if comsub.author else "DELETED"
    d['time'] = time.ctime(comsub.created)
    d['score'] = comsub.score
    d['ups'] = comsub.ups
    d['downs'] = comsub.downs
    d['id'] = comsub.id
    return "%(author)s %(score)d points %(time)s ago"\
    " (%(ups)d|%(downs)d) id:%(id)s" % d

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
    return indent * '-' + get_info_str(comment)

def get_comment_body(comment, indent):
    """returns formatted body of comment as [String]"""
    indent = indent * ' '
    wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent,
            width=79)
    return wrapper.wrap(comment.body)

def get_top_10(subreddit):
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
            lines = format_submission(post) 
            f.write(lines)
