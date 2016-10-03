import twitter
import requests
import json
import arrow
import sys
import time
import configparser

config = configparser.ConfigParser()
config.read('config')

api = twitter.Api(consumer_key=config.get('Twitter', 'ConsumerKey'),
        consumer_secret=config.get('Twitter', 'ConsumerSecret'),
        access_token_key=config.get('Twitter', 'AccessTokenKey'),
        access_token_secret=config.get('Twitter', 'AccessTokenSecret')
    )

movie_api = "http://data.tmsapi.com/v1.1/movies/showings?startDate={date}&numDays=1&zip={zipcode}&api_key={key}".format(
        date=arrow.now().format('YYYY-MM-DD'),
        zipcode=config.get('Settings', 'ZipCode'),
        key=config.get('OnConnect', 'ApiKey')
    )

THEATERS = json.loads(config.get('Settings', 'Theaters'))

# we'll store our movies here organized by theater
MOVIES = {}

# we just want hours and minutes for movie times
def time_fmt(t): return arrow.get(t).format('h:mma')

# format the movie name and time together
def title_and_time_fmt(n, t): 
    return "{title}\n  {times}".format(title=title, times=times[:-2])

# fire the tweet
def fire(t): api.PostUpdate(t)

# builds our tweets
def build_tweets(theater, movies):

    # adding theater name
    tweet = "{}\n\n".format(theater.upper())

    while len(movies) > 0:
        # only add the tweet if tweet length is < 141
        if len(tweet) + len(movies[0]) < 141:
            tweet += "{}\n\n".format(movies.pop(0))
        else:
            # start a new tweet cause we would go over 140 characters
            if len(movies) > 0:
                build_tweets(theater, movies)

    fire(tweet)
    # api rates so we're extra safe
    time.sleep(2)

r = requests.get(movie_api)
data = json.loads(r.content.decode('utf8'))

for movie in data:
    good_theater = False
    showtimes = movie['showtimes']
    times = ''

    # determine if movie is playing at state or bijou
    for showing in showtimes:
        if showing['theatre']['name'] in THEATERS:
            times += "{}, ".format(time_fmt(showing['dateTime']))
            good_theater = True

    # if we didn't see any theaters we care about, peace out
    if not good_theater: continue
        
    # get the theater name
    theater = showtimes[0]['theatre']['name']

    # get the title
    title = movie['title']

    # combine the title and showtimes
    m = title_and_time_fmt(title, times)

    # make sure we can store movies
    if theater not in MOVIES:
        MOVIES[theater] = []

    MOVIES[theater].append(m)

for theater in THEATERS:
    build_tweets(theater, MOVIES[theater])
