import twitter
import requests
import json
import arrow
import time
import configparser
import sys
import os


# builds our tweets
def build_tweets(theater, movies):
    # adding theater name
    tweet = "{}\n\n".format(hash_it(theater))

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


# remove spaces in theater name and add a hash tag
def hash_it(title):
    return "#"+"".join(map(lambda x: x[0].upper() + x[1:], title.split()))


# format the movie name and time together
def title_and_time_fmt(title, times):
    return "{title}\n  {times}".format(title=title, times=times[:-2])


# we just want hours and minutes for movie times
def time_fmt(t):
    return arrow.get(t).format('h:mma')


# fire the tweet
def fire(t): twitter_api.PostUpdate(t)


if __name__ == '__main__':
    PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
    CONF_FILE = os.path.join(PATH, 'config')
    CONFIG = configparser.ConfigParser()
    CONFIG.read(CONF_FILE)

    # grab the theaters we're interested in from the config
    THEATERS = json.loads(CONFIG.get('Settings', 'Theaters'))

    twitter_api = twitter.Api(consumer_key=CONFIG.get('Twitter', 'ConsumerKey'),
                              consumer_secret=CONFIG.get('Twitter', 'ConsumerSecret'),
                              access_token_key=CONFIG.get('Twitter', 'AccessTokenKey'),
                              access_token_secret=CONFIG.get('Twitter', 'AccessTokenSecret'))

    movie_api = "http://data.tmsapi.com/v1.1/movies/showings?startDate={date}&numDays=1&"\
                "zip={zipcode}&api_key={key}".format(
                    date=arrow.now().format('YYYY-MM-DD'),
                    zipcode=CONFIG.get('Settings', 'ZipCode'),
                    key=CONFIG.get('OnConnect', 'ApiKey')
                )

    # we'll store our movies here organized by theater
    MOVIES = {}

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
        if not good_theater:
            continue

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
