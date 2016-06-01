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

Install python3, [virtualenv](https://virtualenv.pypa.io) and sqlite3.

```
virtualenv -p python3 venv
. venv/bin/activate
pip install -r requirements.txt

sqlite3 transcript.db < scraping/schema.sql
```

If `fr_FR.utf8` is not in `locale -a`, you have to install this locale on you system. `sudo dpkg-reconfigure locales` should do the trick. Then, select `fr-FR.UTF-8` on the list. Select `None` for the default locale.

### Crawl

> The fun starts!
> 
> — well, maybe not

```
cd scraping
scrapy crawl tf1 --logfile log_tf1.txt --loglevel INFO
scrapy crawl frtv --logfile log_frtv.txt --loglevel INFO
```

### Notes on the data

* No `speaker` for TF1
* No `duration` for FranceTV

## Text Mining

> Let's play with our data now!
> 
> — The NSA

## TODO

> How many hours are you ready to spend there?
> 
> — my sleeping time

- [ ] check duplicate in dates. Some TV news links are duplicated on pages. Create an emission table? 
- [x] ~~Is TF1 speaker field reliable?~~ NO: http://lci.tf1.fr/jt-we/videos/2012/le-13heures-du-1er-juillet-7394672.html

## License

GPLv3

> Data is <3 