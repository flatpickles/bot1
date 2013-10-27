import Queue
import tweepy
import multiprocessing
import time

class Bot:
  def __init__(self):
    self.toFollowQueue = Queue.Queue()

  # initiates the api reference with keys & secrets in a file named credsPath
  def authWithCredsFile(self, credsPath):
    f = open(credsPath)
    # authenticate
    credsList = [l.replace('\n', '') for l in f.readlines()]
    auth = tweepy.OAuthHandler(credsList[0], credsList[1])
    auth.set_access_token(credsList[2], credsList[3])
    self.api = tweepy.API(auth)
    # setup instance
    self.recentlyFollowed = set(self.api.friends_ids())

  # start a loop to follow a new follower at each interval
  def startFollowBackLoop(self, interval):
    followBackProcess = multiprocessing.Process(target=self._followBackLoop, args=(interval,))
    followBackProcess.start()
    print "followback process started"
    return followBackProcess

  def teardownBot(self):
    pass # todo

  def _followBackLoop(self, interval):
    while True:
      try:
        self._getNewFollows()
        self._followEarliest()
        time.sleep(interval)
      except Exception as e:
        print "encountered exception:"
        print e

  def _getNewFollows(self):
    recentFollows = self.api.followers_ids()
    for uid in reversed(recentFollows):
      if not uid in self.recentlyFollowed:
        self.toFollowQueue.put(uid)
        self.recentlyFollowed.add(uid)
        print "adding %d to queue" % uid

  def _followEarliest(self):
    try:
      earliestFollowId = self.toFollowQueue.get_nowait()
      self.api.create_friendship(user_id=earliestFollowId)
      print "following %d" % earliestFollowId
    except Queue.Empty:
      pass