import twitter
import requests
import json
import arrow
import sys
import time
import configparser

config = configparser.ConfigParser()
config.read('config')

api = twitter.Api(consumer_key=config['Twitter']['ConsumerKey'],
        consumer_secret=config['Twitter']['ConsumerSecret'],
        access_token_key=config['Twitter']['AccessTokenKey'],
        access_token_secret=config['Twitter']['AccessTokenSecret'])

movie_api = "http://data.tmsapi.com/v1.1/movies/showings?startDate=2016-10-02&numDays=1&zip={zip}&api_key={key}".format(
        zip=config['Boop']['ZipCode'],
        key=config['OnConnect']['ApiKey']
    )

r = requests.get(movie_api)
data = json.loads(r.content.decode('utf8'))

# the only theaters we care about in our result set
theaters = ['State Theatre', 'Bijou by the Bay']

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
        if len(tweet) + len(movies[0]) <= 140:
            # only if < 140 characters, add a movie/time to the tweet
            tweet += "{}\n\n".format(movies.pop(0))
        else:
            if len(movies) > 0:
                # start a new tweet cause we would go over 140 characters
                build_tweets(theater, movies)

    fire(tweet)
    # api rates so we're extra safe
    time.sleep(2)

state_movies = []
bijou_movies = []

for movie in data:
    good_theater = False
    showtimes = movie['showtimes']
    times = ''

    # determine if movie is playing at state or bijou
    for showing in showtimes:
        if showing['theatre']['name'] in theaters:
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

    if theater == 'State Theatre':
        state_movies.append(m)
    else:
        bijou_movies.append(m)

build_tweets('Bijou by the Bay', bijou_movies)
build_tweets('State Theater', state_movies)
