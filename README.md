# Scraping and Statistical Text Analysis of French TV News Transcript

Personal project to analyse how TV deals with news. Statistics can be used to debunk or confirm our opinions.

> Have a critical eye
> 
> — the sceptical unicorn 

**This code is for an educational use only.** You should have the appropriate legal authorization to run it. I'm not responsible of your use (I'm not your mother).

## Scraping TV news websites

> I'm not evil, I just love data
> 
> — my router

### Install

> That's the boring part
> 
> — me 30 seconds ago

```
virtualenv -p python3 venv
. venv/bin/activate
pip install -r requirements.txt
```

### Crawl

> The fun starts!
> 
> — well, maybe not

```
cd scraping
scrapy crawl tf1 -o test.json --logfile log.txt --loglevel INFO
```

## Text Mining

> Let's play with our data now!
> 
> — The NSA

## TODO

> How many hours are you ready to spend there?
> 
> — my sleeping time

* check duplicate in dates. Some TV news links are duplicated on pages

## License

GPLv3

> Data is <3 