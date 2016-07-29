# Scraping and Statistical Text Analysis of French TV News Transcript

Personal project to analyze how TV deals with news. Statistics can be used to debunk or confirm our opinions.

> Have a critical eye
> 
> — the skeptical unicorn 

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

You can safely re-run the previous commands to add the new transcripts.

### Notes on the data

* `speaker` for TF1 is rarely available (extracted from the description of the emission, because the information inside the speaker `<div>` isn't reliable)
* No `duration` for FranceTV
* For TF1, `<h2>` titles inside the description of a subject are merged with the content of the description

## Text Mining

> Let's play with our data now!
> 
> — The NSA

```
cd analysis
```

**TODO**

## TODO

> How many hours are you ready to spend there?
> 
> — my sleeping time

- [x] check duplicates in dates. Some TV news are duplicated (2 URL for the same emission). Create an emission table with unique constraint on `(channel, type, date)`
- [x] ~~Is TF1 speaker field reliable?~~ NO: [Counterexample](http://lci.tf1.fr/jt-we/videos/2012/le-13heures-du-1er-juillet-7394672.html)
- [x] Night edition of fr3 have 2 hours. ~~Need to change the `soir` type, because it fails with the unique contraint on `(channel, type, date)`~~ Sunday night edition is indicated as saturday. Fix by changing the date of the 2nd consecutive saturday in the list of emission.
- [ ] Collect ideas of nice descriptive stats, data viz and data analysis
- [ ] Code them
- [ ] Read text-mining references
- [ ] Read the doc of `nltk`
- [ ] Code the text-mining

## License

GPLv3

> Data is <3 
