import datetime
import multiprocessing
import Queue
import time
import tweepy

class Bot:
  def __init__(self):
    self._log("spinning up")
    self.toFollowQueue = Queue.Queue()
    self.toFollowSet = set()

  # initiates the api reference with keys & secrets in a file named credsPath
  def authWithCredsFile(self, credsPath):
    f = open(credsPath)
    credsList = [l.replace('\n', '') for l in f.readlines()]
    auth = tweepy.OAuthHandler(credsList[0], credsList[1])
    auth.set_access_token(credsList[2], credsList[3])
    self.api = tweepy.API(auth)

  # start a loop to follow a new follower at each interval
  def startFollowBackLoop(self, interval):
    self.followBackProcess = multiprocessing.Process(target=self._followBackLoop, args=(interval,))
    self.followBackProcess.start()
    self._log("followback process started")

  # kill all processes, etc
  def teardown(self):
    self.followBackProcess.terminate()
    self._log("we're done here")

  # start a process to repopulate queue (if necessary) and follow one user each interval
  def _followBackLoop(self, interval):
    while True:
      try:
        self._getNewFollows()
        self._followEarliest()
      except Exception as e:
        self._log("encountered an exception")
        print e
      time.sleep(interval)

  # check for new followers who we don't yet follow, add them to the queue
  def _getNewFollows(self):
    recentFollows = self.api.followers() # can respond to 20 follows per interval
    for user in reversed(recentFollows):
      if not user.following and not user.id in self.toFollowSet:
        self.toFollowQueue.put(user.id)
        self.toFollowSet.add(user.id)
        self._log("adding %d to follow queue" % user.id)

  # follow the user at the top of the queue
  def _followEarliest(self):
    try:
      earliestFollowId = self.toFollowQueue.get_nowait()
      self.api.create_friendship(user_id=earliestFollowId)
      self.toFollowSet.remove(earliestFollowId)
      self._log("following %d" % earliestFollowId)
    except Queue.Empty:
      pass

  # print a message to stdout with a timestamp
  def _log(self, message):
    timestamp = datetime.datetime.now().strftime("[%m-%d-%Y %H:%M]")
    print "%s %s" % (timestamp, message)