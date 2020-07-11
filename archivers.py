# import reload
from importlib import reload

# import system tools
import json
import os
import subprocess
from time import sleep
from datetime import datetime, timedelta

# import networking tools
import praw
import requests
import urllib


# define Archiver class for archiving a reddit subreddit
class Archiver(object):
    """Class Archiver to archive a redditt subreddit.

    Inherits from:
        object.
    """

    # initialize instance
    def __init__(self, subreddit):
        """Initialize an Archiver instance with a subreddit name.

        Arguments:
            subreddit: str, the subreddit
        """

        # define subreddit
        self.subreddit = subreddit

        # define main url components
        self.reddit = 'https://www.reddit.com'
        self.archive = 'http://archive.is/submit/'
        self.pushshift = 'https://api.pushshift.io/reddit/search/submission/?subreddit='

        # initialize authorization
        self.credentials = {}

        return None

    # combine records
    def _combine(self, records, recordsii):
        """Combine two sets of records, removing duplicates and sort by date.

        Arguments:
            records: list of dicts
            recordsii: list of dicts

        Returns:
            list of dicts
        """

        # sort records by criteria
        aggregate = records + recordsii

        # sort by length of comments
        aggregate.sort(key=lambda record: len(record['comments']), reverse=True)

        # make dictionary of permalinks
        links = list(set([record['permalink'] for record in aggregate]))
        links = {link: {'created': 0} for link in links}

        # add records to link
        for record in aggregate:

            # if a more recent created date is found
            link = record['permalink']
            if record['created'] > links[link]['created']:

                # replace record
                links[link] = record

        # sort records
        records = [record for record in links.values()]
        records.sort(key=lambda record: record['created'])

        return records

    # convert string into datetime
    def _date(self, day):
        """Convert a string into a datetime.

        Arguments:
            day: str, date in 'YYYY-MM-DD' format

        Returns:
            datetime object
        """

        # form datetime object
        date = datetime.strptime(day, '%Y-%m-%d')

        return date

    # extract data from post
    def _distil(self, post):
        """Distil particular fields from pushshift post.

        Arguments:
            post: the reddit posting

        Returns:
            dict
        """

        # define main fields with functions and default values
        fields = {'title': {'function': lambda post: post['title'], 'default': ''}}
        fields.update({'author': {'function': lambda post: post['author'], 'default': ''}})
        fields.update({'url': {'function': lambda post: post['url'], 'default': ''}})
        fields.update({'permalink': {'function': lambda post: post['permalink'], 'default': ''}})
        fields.update({'created': {'function': lambda post: post['created_utc'], 'default': 0}})
        fields.update({'comments': {'function': lambda post: [], 'default': []}})

        # begin record
        record = {field: self._resolve(reference, post) for field, reference in fields.items()}

        return record

    # extract data from post
    def _extract(self, post):
        """Extract particular fields from reddit post.

        Arguments:
            post: the reddit posting

        Returns:
            dict
        """

        # define main fields with functions and default values
        fields = {'title': {'function': lambda post: post.title, 'default': ''}}
        fields.update({'author': {'function': lambda post: post.author.name, 'default': ''}})
        fields.update({'url': {'function': lambda post: post.url, 'default': ''}})
        fields.update({'permalink': {'function': lambda post: post.permalink, 'default': ''}})
        fields.update({'created': {'function': lambda post: post.created, 'default': 0}})

        # define comment fields
        comments = {'author': {'function': lambda comment: comment.author.name, 'default': ''}}
        comments.update({'body': {'function': lambda comment: comment.body, 'default': ''}})
        comments.update({'created': {'function': lambda comment: comment.created, 'default': 0}})

        # begin record
        record = {field: self._resolve(reference, post) for field, reference in fields.items()}

        # get comments
        record['comments'] = []
        for comment in post.comments.list():

            # add comment record
            recordii = {field: self._resolve(reference, comment) for field, reference in comments.items()}
            record['comments'].append(recordii)

        return record

    # resolve a field from a post
    def _resolve(self, reference, post):
        """Resolve the field value from the post or get the default.

        Arguments:
            reference: (function, str or float) tuple
            default: str or float
            post: reddit post

        Returns:
            str or float
        """

        # try
        try:

            # to get attribute
            datum = reference['function'](post)

        # otherwise
        except AttributeError:

            # set to defautl
            datum = reference['default']

        return datum

    # get the timestamp from a date object
    def _stamp(self, date):
        """Get the timestamp from a date.

        Arguments:
            date: datetime object

        Returns:
            str, the timestamp
        """

        # get the timestamp
        stamp = date.timestamp()
        stamp = str(int(stamp))

        return stamp

    # get the date string from a timestamp
    def _unstamp(self, stamp):
        """Get the date string from a timestamp.

        Arguments:
            stamp: str or int

        Returns:
            str, the day
        """

        # get the date object
        date = datetime.fromtimestamp(float(stamp))

        # convert to str
        day = str(date)

        return day

    # access the subreddit instance
    def access(self):
        """Access the subreddit object.

        Arguments:
            None

        Returns:
            praw subreddit object
        """

        # authorize and make client
        self.authorize()
        reddit = praw.Reddit(**self.credentials)

        # get subreddit
        subreddit = reddit.subreddit(self.subreddit)

        return subreddit

    # archive the reddit site
    def archive(self, number, delay=10, listing='merged'):
        """Archive a number of sites at archive.is.

        Arguments:
            number: int, number of records to archive beginning with most recent.
            delay=10: time in seconds to delay next call, to prevent defensive actions by site
            listing='merged': the particular record set to archive

        Returns:
            None
        """

        # get archived links so far
        path = self.subreddit.lower() + '_archives.json'
        archives = self.retrieve(path)

        # get merged records
        pathii = self.subreddit.lower() + '_' + listing + '.json'
        records = self.retrieve(pathii)

        # get permalinks not yet archived
        links = [record['permalink'] for record in records]
        links = [link for link in links if link not in archives]

        # print status
        print('{} links archived so far...'.format(len(archives)))
        print('{} to go...'.format(len(links)))

        # archive
        for index, link in enumerate(links[:number]):

            # print status
            print('{} of {}:'.format(index, number))
            estimate = (number - index) * delay / 60
            print('estimated time: {} minutes'.format(estimate))

            # make url
            base = self.archive
            url = self.reddit + link
            print(url)
            result = subprocess.call(['curl', '-d', 'url=' + url, base])
            print('{}'.format(result))
            archives.append(link)

            # store archives
            self.store(archives, path)

            # sleep to avoid retaliation
            sleep(delay)

        return None

    # authorize with credentials
    def authorize(self):
        """Authorize access to the subreddit by populating authorization attributes from file.

        Arguments:
            None

        Returns:
            None
        """

        # try to read in default credentials
        try:

            # open up default credentials
            with open('default_credentials.txt') as pointer:

                # get credentials
                credentials = [line.strip() for line in pointer.readlines()]

        # otherwise
        except FileNotFoundError:

            # open up main credentials
            with open('credentials.txt') as pointer:

                # get credentials
                credentials = [line.strip() for line in pointer.readlines()]

        # parse credentials
        credentials = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in credentials[:5]}
        self.credentials.update(credentials)

        return None

    def grab(self, listing='hot', number=1000):
        """Retrieve a number of subreddit listings and store in a file.

        Arguments:
            listing: str, 'hot', 'new', or 'top'
            number: int, number of records to retrieve, 1000 max

        Returns:
            None
        """

        # get subreddit
        subreddit = self.access()

        # define listings
        listings = {'hot': subreddit.hot}
        listings.update({'new': subreddit.new})
        listings.update({'top': subreddit.top})

        # status
        print('grabbing {} {} records from {}...'.format(number, listing, self.subreddit))

        # get posts
        posts = [post for post in listings[listing](limit=number)]

        # extract records from posts
        records = [self._extract(post) for post in posts]

        # retrieve current records
        path = self.subreddit.lower() + '_' + listing + '.json'
        recordsii = self.retrieve(path)

        # combine records and store
        combination = self._combine(records, recordsii)
        self.store(combination, path)

        return None

    # merge all records into one set
    def merge(self):
        """Merge all records into one set.

        Arguments:
            None

        Returns:
            None
        """

        # combine all records
        aggregate = []
        for listing in ('hot', 'new', 'top', 'pushshift'):

            # construct path
            path = self.subreddit.lower() + '_' + listing + '.json'
            records = self.retrieve(path)
            aggregate = self._combine(records, aggregate)

        # store
        deposit = self.subreddit.lower() + '_merged.json'
        self.store(aggregate, deposit)

        return None

    # remember records from the past using pushshift to get older titles
    def remember(self, beginning, ending=None, comments=True):
        """Remember past records between two dates using pushshift.

        Arguments:
            beginning: str in 'YYYY-MM-DD' format
            ending, str in 'YYYY-MM-DD' format
            comments=True: boolean, include comments from subreddit?

        Returns:
            None
        """

        # grab the subredit
        subreddit = self.access()

        # get previous pushshift records
        path = self.subreddit.lower() + '_pushshift.json'
        pushshift = self.retrieve(path)

        # get all titles recorded so far
        titles = [record['title'] for record in pushshift]

        # get timestamps, defaulting ending to now
        now = str(datetime.now().date())
        beginning = self._stamp(self._date(beginning))
        ending = self._stamp(self._date(ending or now))

        # define inital start point
        start = beginning

        # scan for records
        records = []
        finished = False
        while not finished:

            # assume finished
            finished = True

            # status
            print('\nstarting at: {}...'.format(self._unstamp(start)))

            # construct pushshift url
            url = self.pushshift + self.subreddit + '&after=' + start + '&before=' + ending
            print('url: {}'.format(url))

            # get data from pushshift
            response = requests.get(url, headers={'User-Agent': 'Redchiver'})
            data = json.loads(response.text)['data']

            # search the subreddit by each data
            print('{} records retrieved.'.format(len(data)))
            for datum in data:

                # search subreddit by title
                title = datum['title']

                # if not yet seen
                if title not in titles:

                    # get comments
                    if comments:

                        # get subreddit records
                        print('searching for title: {}...'.format(title))
                        posts = [post for post in subreddit.search(query=title) if post.title == title]
                        records += [self._extract(post) for post in posts]

                    # otherwise get short records
                    else:

                        # get short records
                        records += [self._distil(datum)]

                # reset for next round
                finished = False
                start = str(int(datum['created_utc']))

            # sleep a bit
            sleep(2)

        # combine with new records and store
        pushshift = self._combine(records, pushshift)
        self.store(pushshift, path)

        return None

    # retrieve stored records
    def retrieve(self, path):
        """Retrieve stored records from a file.

        Arguments:
            path: str, file path

        Returns:
            list of dicts
        """

        # try
        try:

            # to open up file
            with open(path, 'r') as pointer:

                # and get data
                data = json.load(pointer)['data']

        # but if there's no file yet
        except FileNotFoundError:

            # create it
            with open(path, 'w') as pointer:

                # with blank data
                data = []
                json.dump({'data': data}, pointer)

        return data

    # stash all images in a file
    def stash(self, listing='hot', directory=None):
        """Stash content of all possible image urls in an image directory.

        Arguments:
            listing: str, 'hot', 'new', 'top', 'pushshift', 'merged'

        Returns:
            None
        """

        # make directory name
        if not directory:

            # set default
            directory = self.subreddit.lower() + '_content'

        # create directory if needed
        if directory not in os.listdir():

            # create directory
            os.mkdir(directory)

        # get all content so far in directory
        names = os.listdir(directory)

        # get records
        path = self.subreddit.lower() + '_' + listing + '.json'
        records = self.retrieve(path)

        # download each url
        for index, record in enumerate(records):

            # print
            print('record {} of {}'.format(index, len(records)))

            # get url
            url = record['url']
            extension = '.' + url.split('.')[-1]

            # check extension
            if extension in ('.png', '.jpg', '.jpeg', '.gif'):

                # create name and check for presence in directory
                stub = record['title'].encode('ascii', errors='ignore').decode().replace(' ', '_').replace('/', '_')[:50]
                name = stub + extension
                if name not in names:

                    # try to fetch record
                    print('fetching {}...'.format(url))
                    response = requests.get(url)
                    pathii = directory + '/' + name
                    with open(pathii, 'wb') as pointer:

                        # write file
                        pointer.write(response.content)

        return None

    # store record in a file
    def store(self, records, path):
        """Store records in a file.

        Arguments:
            records: list of dicts
            path: str, file path

        Returns:
            None
        """

        # open file
        print('storing {} records in {}...'.format(len(records), path))
        with open(path, 'w') as pointer:

            # and dump records
            json.dump({'data': records}, pointer)

        return None






