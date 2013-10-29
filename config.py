### time between actions - some imposed by rate limiting ###
FOLLOW_INTERVAL = 60 # one minute
FAVE_INTERVAL = 10 * 60 # 10 minutes
FOLLOW_SEARCH_INTERVAL = 30 * 60 # 30 minutes
TWEET_INTERVAL = 3 * 60 * 60 # 3 hours
TWEET_PERTURBATION = 60 * 60 # if you will; 1 hour

### defaults - configurable as properties on an instance of Bot ###
LOCATION = 23424977 # place ID - USA
LANGUAGE = 'en'
INTERESTS = ["follow", "follow back", "retweet", "teamfollowback"]
INTEREST_DIST = [.6, .4] # [interests array, current top trends]
FAVE_DIST = [.3, .7] # [fave from following, fave from search]
TWEET_DIST = [.15, .5, .35] # [rt following, rt from search, borrow from search]
USE_TRENDS_FOR_FOLLOWS = False
USE_TRENDS_FOR_TWEETS = True
USE_TRENDS_FOR_RETWEETS = True
USE_TRENDS_FOR_FAVES = True
SEARCH_TYPE_FOR_FOLLOWS = 'recent'
SEARCH_TYPE_FOR_TWEETS = 'recent'
SEARCH_TYPE_FOR_RETWEETS = 'mixed'
SEARCH_TYPE_FOR_FAVES = 'mixed'