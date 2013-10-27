import Bot

def main():
  bot1 = Bot.Bot()
  bot1.authWithCredsFile("creds")
  followBackProcess = bot1.startFollowBackLoop(60)
  followBackProcess.join()

if __name__ == "__main__":
    main()


# TODO
# - implement killing bot
# - use relationship api call instead of list for follow state