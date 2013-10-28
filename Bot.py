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
    self._log("spinning up")
    self.toFollowQueue = multiprocessing.Queue()
    self.setInterestedTopics(config.DEFAULT_INTERESTS)

  # initiates the api reference with keys & secrets in a file named credsPath
  def authWithCredsFile(self, credsPath):
    try:
      f = open(credsPath)
      credsList = [l.replace('\n', '') for l in f.readlines()]
      auth = tweepy.OAuthHandler(credsList[0], credsList[1])
      auth.set_access_token(credsList[2], credsList[3])
      self.api = tweepy.API(auth)
      f.close()
      self._log("authentication succeeded")
    except Exception as e:
      self._log("authentication failed")
      traceback.print_exc()

  def setInterestedTopics(self, topicsArray):
    self.topicsArray = topicsArray

  def startLoops(self):
    # start a loop to follow a new follower at each interval
    self.followBackProcess = multiprocessing.Process(target=self._followLoop, args=(config.FOLLOW_INTERVAL,))
    self.followBackProcess.start()
    self._log("follow-back process started")
    # start a loop to find new users to follow periodically
    self.followSearchProcess = multiprocessing.Process(target=self._followSearchLoop, args=(config.FOLLOW_SEARCH_INTERVAL,))
    self.followSearchProcess.start()
    self._log("follow search process started")

  # kill all processes, etc
  def teardown(self):
    self.followBackProcess.terminate()
    self.followSearchProcess.terminate()
    self._log("termination succeeded")

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
    tweet = self._getTopicalTweet()
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
      earliestFollowId = self.toFollowQueue.get(block=False)
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
      self.toFollowQueue.put(user.id)
      return True
    return False

  def _getTopicalTweet(self):
    currTopic = random.choice(self.topicsArray)
    results = self.api.search(q=currTopic)
    return random.choice(results)

  # print a message to stdout with a timestamp
  def _log(self, message):
    timestamp = datetime.datetime.now().strftime("[%m-%d-%Y %H:%M]")
    print "%s %s" % (timestamp, message)