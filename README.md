# chat-bot-profanity-filter

The chat-bot-profanity-filter uses the [bad-words DoltHub dataset](https://www.dolthub.com/repositories/Liquidata/bad-words) to censor bad words between a user and the ChatBot. Try it for yourself:

[Download Dolt](https://github.com/liquidata-inc/dolt#installation) if you don't already have it.

Requirements

```
pip install python # Version 3.7 or later
pip install doltpy
```

Clone this repository and start the chat bot script

```
git clone https://github.com/liquidata-inc/chat-bot-profanity-filter.git
cd chat-bot-profanity-filter
python chat-boy.py
```

Example:
```
Pulling latest bad-words...
Done pulling.

 Hello! This is a simple chat bot with profanity filter. 
 Respond 'bye', or use CTRL+C to exit. 
 You can type anything you want, and I will censor the bad words.
 Say something: 

> Me: Hey
> ChatBot: Sure
> Me: That's it?
> ChatBot: 👍
> Me: Okay fuck you too!
> ChatBot sees: okay **** you too!
> ChatBot: Cool
> Me: bye
> ChatBot: Thanks for chatting!
```
