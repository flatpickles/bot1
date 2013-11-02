import config
import datetime
import multiprocessing
import Queue
import random
import time
import traceback
import tweepy

class Bot:
  ### external methods ###

  def __init__(self):
    self._name = None
    self._log("spinning up a new bot")
    self._toFollowQueue = multiprocessing.Queue() # contains user IDs
    self.running = False

    # configure this instance with defaults (these fields can be configured on a bot-by-bot basis)
    self.location = config.LOCATION
    self.language = config.LANGUAGE
    self.interests = config.INTERESTS
    self.useTrendsForFollows = config.USE_TRENDS_FOR_FOLLOWS
    self.useTrendsForTweets = config.USE_TRENDS_FOR_TWEETS
    self.useTrendsForRetweets = config.USE_TRENDS_FOR_RETWEETS
    self.useTrendsForFaves = config.USE_TRENDS_FOR_FAVES
    self.searchTypeForFollows = config.SEARCH_TYPE_FOR_FOLLOWS
    self.searchTypeForTweets = config.SEARCH_TYPE_FOR_TWEETS
    self.searchTypeForRetweets = config.SEARCH_TYPE_FOR_RETWEETS
    self.searchTypeForFaves = config.SEARCH_TYPE_FOR_FAVES
    self.interestDist = config.INTEREST_DIST
    self.faveDist = config.FAVE_DIST
    self.tweetDist = config.TWEET_DIST

  # initiates the api reference with keys & secrets in a file named credsPath
  def authWithCredsFile(self, credsPath):
    try:
      f = open(credsPath)
      credsList = [l.replace('\n', '') for l in f.readlines()]
      auth = tweepy.OAuthHandler(credsList[0], credsList[1])
      auth.set_access_token(credsList[2], credsList[3])
      self.api = tweepy.API(auth)
      f.close()
      me = self.api.me()
      self._name = me.screen_name
      self._id = me.id
      self._log("authentication succeeded")
      self.running = True
      return True
    except Exception as e:
      self._log("authentication failed")
      traceback.print_exc()
      return False

  def start(self):
    # start a loop to follow a new follower at each interval
    self.followBackProcess = multiprocessing.Process(target=self._followLoop, args=(config.FOLLOW_INTERVAL,))
    self.followBackProcess.start()\
    # start a loop to find new users to follow periodically
    self.followSearchProcess = multiprocessing.Process(target=self._followSearchLoop, args=(config.FOLLOW_SEARCH_INTERVAL,))
    self.followSearchProcess.start()
    # start a loop to tweet on occasion
    self.tweetProcess = multiprocessing.Process(target=self._tweetLoop, args=(config.TWEET_INTERVAL,config.TWEET_PERTURBATION,))
    self.tweetProcess.start()
    # start a loop to favorite stuff
    self.faveProcess = multiprocessing.Process(target=self._faveLoop, args=(config.FAVE_INTERVAL,))
    self.faveProcess.start()

    self._log("all processes started")

  # kill all processes, etc
  def stop(self):
    self.followBackProcess.terminate()
    self.followSearchProcess.terminate()
    self.tweetProcess.terminate()
    self.faveProcess.terminate()
    self._log("all processes stopped")

  ### fave lots of stuff ###

  def _faveLoop(self, interval):
    while True:
      try:
        if random.random() < self.faveDist[0]:
          # fave a tweet from someone followed by this bot
          self._faveFriendTweet()
        else:
          # fave a tweet from the wilderness
          self._faveSearchTweet()
      except Exception as e:
        self._log("encountered an exception in fave loop")
        traceback.print_exc()
      perturbation = interval * 0.1
      toWait = interval + (random.random() * 2 * perturbation - perturbation)
      time.sleep(int(toWait))

  def _faveFriendTweet(self):
    tweet = self._getFriendTweet()
    self.api.create_favorite(id=tweet.id)
    self._log("faved @%s/%s (from friend)" % (tweet.user.screen_name, tweet.id_str))

  def _faveSearchTweet(self):
    tweet = self._getTopicalTweet(self.useTrendsForFaves, self.searchTypeForFaves)
    self.api.create_favorite(id=tweet.id)
    self._log("faved @%s/%s (from search)" % (tweet.user.screen_name, tweet.id_str))

  ### tweet or retweet occasionally ###

  def _tweetLoop(self, interval, perturbation):
    while True:
      try:
        r = random.random()
        if r < self.tweetDist[0]:
          # retweet a tweet from someone followed by this bot
          self._retweetFriendTweet()
        elif r < self.tweetDist[0] + self.tweetDist[1]:
          # retweet a tweet from a search
          self._retweetSearchTweet()
        else:
          # tweet the text of a tweet from a search
          self._tweetSearchTweet()
      except Exception as e:
        self._log("encountered an exception in tweet loop")
        traceback.print_exc()
      # start out with a random time, add up to 2 hours depending on the time of the day
      toWait = interval + (random.random() * 2 * perturbation - perturbation)
      toWait += 60 * 60 * abs(12-((datetime.datetime.now().hour - 6) % 24))/6.0
      time.sleep(int(toWait))

  def _retweetFriendTweet(self):
    tweet = self._getFriendTweet()
    self.api.retweet(id=tweet.id)
    self._log("retweeted @%s/%s (from friend)" % (tweet.user.screen_name, tweet.id_str))

  def _retweetSearchTweet(self):
    tweet = self._getTopicalTweet(self.useTrendsForRetweets, self.searchTypeForRetweets)
    self.api.retweet(id=tweet.id)
    self._log("retweeted @%s/%s (from search)" % (tweet.user.screen_name, tweet.id_str))

  def _tweetSearchTweet(self):
    tweet = self._getTopicalTweet(self.useTrendsForTweets, self.searchTypeForTweets)
    # never reproduce tweets that mention anyone else
    if '@' in tweet.text:
      self._tweetSearchTweet()
    else:
      self.api.update_status(status=tweet.text)
      self._log("reproduced @%s/%s (from search)" % (tweet.user.screen_name, tweet.id_str))

  ### follow search ###

  def _followSearchLoop(self, interval):
    while True:
      try:
        self._findUserToFollow()
      except Exception as e:
        self._log("encountered an exception in follow search loop")
        traceback.print_exc()
      time.sleep(interval)

  def _findUserToFollow(self):
    # search tweets instead of users for more dynamic results
    tweet = self._getTopicalTweet(self.useTrendsForFollows, self.searchTypeForFollows)
    willFollow = self._queueFollow(tweet.user)
    if not willFollow:
      # find another user if this one wasn't queued
      self._findUserToFollow()

  ### follow-back ###

  # start a process to repopulate queue (if necessary) and follow one user each interval
  def _followLoop(self, interval):
    while True:
      try:
        self._getNewFollows()
        self._followEarliest()
      except Exception as e:
        self._log("encountered an exception in follow loop")
        traceback.print_exc()
      time.sleep(interval)

  # check for new followers who aren't yet followed, add them to the queue
  def _getNewFollows(self):
    recentFollows = self.api.followers() # can respond to 20 follows per interval
    for user in reversed(recentFollows):
        self._queueFollow(user)

  # follow the user at the top of the queue
  def _followEarliest(self):
    try:
      # check if already followed, in case there are duplicate entries in the queue
      # more straightforward to also keep a set of objects in the queue, but not as safe across processes
      earliestFollowId = self._toFollowQueue.get(block=False)
      user = self.api.get_user(id=earliestFollowId)
      if not user.following:
        self.api.create_friendship(user_id=earliestFollowId)
        self._log("following @%s" % user.screen_name)
      else:
        # follow the next user if already following this one
        self._followEarliest()
    except Queue.Empty:
      pass

  ### utility ###

  def _queueFollow(self, user):
    if not user.following:
      self._toFollowQueue.put(user.id)
      return True
    return False

  def _getTopicalTweet(self, useTrends, searchType):
    options = self.interests
    r = random.random()
    if useTrends and r >= self.interestDist[0]:
      options = [trend['name'] for trend in self.api.trends_place(id=self.location)[0]['trends']]
    currTopic = random.choice(options)
    options = self.api.search(q=currTopic, search_type=searchType)
    selection = self._langAppropriateTweet(options, True)
    return selection if selection != None else self._getTopicalTweet(useTrends, searchType)

  def _getFriendTweet(self):
    options = self.api.home_timeline(exclude_replies=True)
    selection = self._langAppropriateTweet(options, False) # api takes care of excluding replies here
    return selection if selection != None else self._getFriendTweet()

  def _langAppropriateTweet(self, tweets, excludeReplies):
    selection = random.choice(tweets)
    maxAttempts = 20
    # make sure this isn't already tweeted and is in desired language
    while (selection.lang != self.language or selection.user.id == self._id \
      or (excludeReplies and selection.in_reply_to_user_id != None)) \
      and maxAttempts > 0:
        selection = random.choice(tweets)
        maxAttempts -= 1
        tweets.remove(selection)
    return selection if maxAttempts > 0 else None

  # print a message to stdout with a timestamp
  def _log(self, message):
    timestamp = datetime.datetime.now().strftime("%m-%d-%Y %H:%M")
    if not self._name:
      print "[%s] %s" % (timestamp, message)
    else:
      print "[%s ~ @%s] %s" % (timestamp, self._name.lower(), message)