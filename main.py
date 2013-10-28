import Bot
import signal
import sys

bot1 = None

def quit_handler(signal, frame):
  global bot1
  bot1.teardown()
  sys.exit(0)

def main():
  global bot1
  bot1 = Bot.Bot()
  bot1.authWithCredsFile("creds")
  bot1.startLoops()

if __name__ == "__main__":
    main()
    signal.signal(signal.SIGINT, quit_handler)
    signal.pause()