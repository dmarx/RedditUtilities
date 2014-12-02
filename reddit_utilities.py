import praw
import time
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
 
class UserScraper(object):
    '''Generic utility for investigating redditors. '''
    def __init__(self
                , username
                , useragent = 'Scraper class for investigating redditors by /u/shaggorama'
                ,r=None):
        self.r = r
        if not r:
            self.r = praw.Reddit(useragent)
        self.user = self.r.get_redditor(username)
        self._comments = []
        self._submissions = []
        self._user_subreddits = None
        
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
        print "\nGetting comments"
        self.scrape_content('comments')
    
    def scrape_submissions(self):
        print "\nGetting submissions"
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
        print n, type, "scraped"
    
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
    
    def get_user_subreddits(self, use_comments=True, use_submissions=True, report=10):
        if not self._submissions and use_submissions:
            self.scrape_submissions()
        if not self._comments and use_comments:
            self.scrape_comments()
        by_comment = [c.subreddit.display_name for c in self._comments]
        by_submission = [c.subreddit.display_name for c in self._submissions]
        self._user_subreddits = Counter(by_comment + by_submission)
        # main_subr = self._user_subreddits.most_common()
        # row = "{col1}\t{col2}\t{col3}"
        # if report >0:
            # print
            # print row.format(col1="Rank", col2="Count", col3="Subreddit")
        # while report>0:            
            # report += -1            
            # record = main_subr[report]
            # print row.format(col1=report+1, col2=record[1], col3=record[0])
    
    def investigate_user(self, plot=True, report=10):
        """ Run the whole suite """        
        self.get_user_subreddits(report)
        self.get_activity_profile(plot)