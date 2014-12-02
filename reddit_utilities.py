import praw
from praw.helpers import flatten_comments
import time
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

UA = 'Scraper class for investigating redditors by /u/shaggorama'
 
class UserScraper(object):
    '''Generic utility for investigating redditors. '''
    def __init__(self
                , username
                , useragent = UA
                ,r=None):
        self.r = r
        if not r:
            self.r = praw.Reddit(useragent)
        self.user = self.r.get_redditor(username)
        self._comments = []
        self._submissions = []
        self._user_subreddits = None # This will be a pd.DataFrame
        
    @property
    def comments(self):
        if not self._comments:
            self.scrape_comments()
        return self._comments
    
    @property
    def submissions(self):
        if not self._submissions:
            self.scrape_submissions()
        return self._submissions
    
    @property
    def subreddits(self):
        if not self._user_subreddits:
            self.get_user_subreddits()
        return self._user_subreddits
    
    def scrape_comments(self):
        print "Getting comments"
        self.scrape_content('comments')
    
    def scrape_submissions(self):
        print "Getting submissions"
        self.scrape_content('posts')
    
    def scrape_content(self, type, kargs={}):
        '''Generic function for scraping comments or posts'''
        funcs = {'comments':self.user.get_comments, 'posts':self.user.get_submitted}
        memo  = {'comments':self._comments,          'posts':self._submissions}
        params = {'limit':None}        
        params.update(kargs)
        gen = apply(funcs[type], [], params)
        n=0
        for content in gen:
            if content not in memo[type]:
                memo[type].append(content)
                n+=1
                if n%100 == 0:
                    print n, type, "scraped"
            else:                
                break
        print n, type, "scraped\n"
    
    def content_activity_profile(self, content):        
        pivot = {}
        for d in [c.created_utc for c in content]:
            timestamp = time.gmtime(d)
            t = timestamp.tm_hour
            pivot[t] = pivot.get(t,0) + 1
        return pd.Series(pivot)
    
    def get_comment_activity_profile(self, plot=True):
        if not self._comments:
            self.scrape_comments()
        self.comment_activity_profile = self.content_activity_profile(self._comments)
        if plot:
            self.comment_activity_profile.plot()
            plt.show()
            
    def get_submission_activity_profile(self, plot=True):
        if not self._submissions:
            self.scrape_submissions()
        self.submission_activity_profile = self.content_activity_profile(self._submissions)
        if plot:
            self.submission_activity_profile.plot()
            plt.show()
    
    def get_activity_profile(self, plot=True):
        self.get_comment_activity_profile(plot=False)
        self.get_submission_activity_profile(plot=False)
        self.activity_profile = self.submission_activity_profile + self.comment_activity_profile
        if plot:
            self.activity_profile.plot()
            plt.show()
    
    def get_user_subreddits(self):
        by_comment = [c.subreddit.display_name for c in self.comments]
        by_submission = [c.subreddit.display_name for c in self.submissions]
        self._user_subreddits = pd.DataFrame({'comments':Counter(by_comment), 'submissions':Counter(by_submission)})
        self._user_subreddits = self._user_subreddits.fillna(0)
        self._user_subreddits['total'] = self._user_subreddits.sum(axis=1)
        self._user_subreddits = self._user_subreddits.sort('total', ascending=False)
    
    def investigate_user(self, plot=True, n_subreddits=10):
        """ Run the whole suite """        
        subs_report = self.subreddits.ix[:n_subreddits, :]
        print "Top Subreddits:"
        print subs_report
        self.get_activity_profile(plot)
        
        
class SubredditScraper(object):
    '''Generic utility for investigating a subreddit. '''
    def __init__(self
                , subreddit
                , useragent = UA
                ,r=None):
        self.r = r
        if not r:
            self.r = praw.Reddit(useragent)
        self.subreddit = r.get_subreddit(subreddit)
        self._submissions = []
        self._comments = []
        self._users = set()
        
    @property
    def submissions(self):
        if not self._submissions:
            for subm in self.subreddit.get_new(limit=None):
                self._submissions.append(subm)
        return self._submissions
        
    @property
    def comments(self):
        if not self._comments:
            for subm in self.submissions:
                self._comments.extend(flatten_comments(subm.comments))
        return self._comments
        
    @property
    def users(self):
        if not self._users:
            for c in self.comments:
                try:
                    self._users.add(c.author.name)
                except (praw.errors.InvalidUser, praw.errors.BadUsername): # hopefully one of these is right..?
                    continue
                