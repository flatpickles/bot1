### time between actions - some imposed by rate limiting ###
FOLLOW_INTERVAL = 60 # one minute
FAVE_INTERVAL = 3 * 60 # 3 minutes +/- 10%
FOLLOW_SEARCH_INTERVAL = 20 * 60 # 20 minutes
TWEET_INTERVAL =  1.25 * 60 * 60 # 1 hour, 15 mins - baseline increased up to 2 hours depending on time of day
TWEET_PERTURBATION = 45 * 60 # if you will; 45 mins

### defaults - configurable as properties on an instance of Bot ###
LOCATION = 23424977 # place ID - USA
LANGUAGE = 'en'
INTERESTS = ["follow", "follow back", "teamfollowback", "retweet", "fave", "maplight"]
BLACKLIST = ["unfollow"]
INTEREST_DIST = [.7, .3] # [interests array, current top trends]
FAVE_DIST = [.15, .85] # [fave from following, fave from search]
TWEET_DIST = [.15, .5, .35] # [rt following, rt from search, borrow from search]
USE_TRENDS_FOR_FOLLOWS = False
USE_TRENDS_FOR_TWEETS = True
USE_TRENDS_FOR_RETWEETS = True
USE_TRENDS_FOR_FAVES = True
SEARCH_TYPE_FOR_FOLLOWS = 'recent'
SEARCH_TYPE_FOR_TWEETS = 'recent'
SEARCH_TYPE_FOR_RETWEETS = 'mixed'
SEARCH_TYPE_FOR_FAVES = 'mixed'