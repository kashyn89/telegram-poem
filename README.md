# telegram-poem
"You are a good listener"

A Bot that will listen to all stories you share with him.
You can send him text messages and pictures and after a short amount of time (10 seconds) the messages will magically disappear in the chat then.
No one is able to see what you wrote him in your Telegram chats.

You can view it all on a password protected website and even download it.

Selfhosting thing so you handle your own data!

Runs in docker.
You only need a bot token from botfather, invite the bot into a group chat and lets go.

```
version: '3'
services:
  telegram-bot:
    build: .
    volumes:
      - data:/app/db
      - images:/app/images
    ports:
      - "5011:5000"
    environment:
      - TELEGRAM_BOT_TOKEN=set_your_bot_token
      - WEB_PASSWORD=set_webpassword
    restart: always
networks:
  default:
    driver: bridge
volumes:
  data:
  images:
```
