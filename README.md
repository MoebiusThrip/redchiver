# Redchiver
For archiving a reddit sub.

This code began as some thrown together snippets motivated by the desire to archive a valuable Reddit sub before it got banned and the content was lost forever.  It's presented here in a hopefully more functional form in the hopes that it may serve the same purpose for other subs.

### Special thanks
Special thanks to u/SometimesJaka and u/TrainingBluejay for their advice and code snippets on which this is built.

### Intended Use
The intended use is as such, for example with the r/DoubleBass subredditt:

```import archivers```

Initialize an instance for the particular subReddit:

```bass = archivers.Archive('DoubleBass')```

There are three main intened functions:
#### 1) Gather recent records from the subreddit

This uses the praw module, and requires credentials as described here:
https://praw.readthedocs.io/en/latest/getting_started/authentication.html

Open the credentials.txt file and apply your credentials.

Grab the first 100 records from, for example, the hot list:

```bass.grab('hot', number=100)```

They will be stored in a json file.

#### 2) Gather older records using pushshift

Unfortunately there is a limit to how many records you may readily retrieve in this way.  Thanks to the pushshift.io project, older records may also be gathered.

For instance, grab the records from January through February of this year:

```bass.remember('2020-01-01', '2020-02-29')``` 

This is a slow process, as the records must be grabbed only 25 at a time from pushshift, to get the titles, and then must be grabbed individual from the praw api.

#### 3) Archive the websites at archive.is

Merge all record sets together:

```bass.merge()```

Submit the top 100 records to archive.is:

```bass.archive(100)```

This is also a slow process.  A 10 second delay is built into each call, as the service will only accept so many submissions at once.  The subreddit must have a public status for it to work.

### Other functions

You may access the subreddit instance itself with:

```bass.access()```

This enables you to explore the api.

You may grab all the image files from a record set with:

```bass.stash('hot', 'images')```

This will attempt to grab the associated jpeg or png if there is one, and stash it in a directory called 'images'

Also, the contents of any file is retrievable with:

```bass.retrieve('doublebass_hot.json')```

### Thanks! Happy Archiving!




