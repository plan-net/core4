###########################################################
retrieval and pos tagging of tweets
###########################################################

This project can be found on GitHub as well:
https://github.com/Alioun/twitter/

The following example shows a simple and easy way of how you can use core to
realize a wide variety of tasks, in this case retrieving tweets from a
particular place and then running a Part of Speech (POS) tagger over the
retrieved tweets to build a base for further analyses on those tweets.

Foreign packages used in this example:

tweepy: Tweepy is used as an easy to use, yet quite powerful way to use the
various twitter apis in our case tweepy is only used to access the "Geo Search"
API and the standard "Search" API. https://github.com/tweepy/tweepy

nltk: short for "Natural Language Toolkit" is a library combining many different
libraries used for natural language processing into one convenient package.
In this example we are only using a TweetTokenizer provided by the nltk to try to
clean up the tweets while also tokenizing them for the POS tagger.
https://github.com/nltk/nltk
https://www.nltk.org/

pattern: another library for natural language processing and much more,
we are only using the pos tagger from the german module
https://github.com/clips/pattern

Imports::

    import tweepy
    from core4.queue.job import CoreJob
    from nltk.tokenize.casual import TweetTokenizer
    from pattern.text.de import parsetree

The first part is to retrieve the Tweets.

To be able to retrieve any tweets you need to have an twitter dev app if you
don't have one yet, you can create one over at
https://developer.twitter.com/en/apps after you've created one, go into the App
Details and then to the "Keys and tokens" tab and copy consumer key, consumer
secret, access token and access token secret into your local.yaml, you can find
an example twitter.yaml and local.yaml down below.

With the authorization requirements cleared we are querying the "Geo Search" to
get the place id for a specific region (Germany in this case).

Using that place id we can query twitter for all tweets coming from that region.
The job is set up to stop execution and terminate when it encounters a rate
limit error.

Twitters rate limit timeframe is 15 minutes, so the job is scheduled to get as
much data until being rate limited every 20 minutes.

All retrieved tweets are written into a mongodb collection for easy access
later on::

    class TweetLoader(CoreJob):
        """
        Loads all tweets coming from a given region or place and saves them into
        a mongodb collection.
        The tweets are retrieved via the Twitter Search API in no particular
        order, this means the latest tweets are not guaranteed.
        """
        author = 'adi'
        schedule = '0,20,40 * * * *'  # runs every 20 minutes

        def execute(self, *args, **kwargs):
            consumer_key = self.config.twitter.api.consumer_key
            consumer_secret = self.config.twitter.api.consumer_secret
            access_token = self.config.twitter.api.access_token
            access_token_secret = self.config.twitter.api.access_token_secret

            self.set_source('Twitter Search API')
            tweet_coll = self.config.twitter.api.tweet_coll

            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)

            api = tweepy.API(
                auth)

            # this code was run once to get the place id, afterwards I saved it to
            # prevent getting rate limited on a part that isn't going to change

            # place = api.geo_search(query='Germany', granularity="country")
            # place_id = place[0].id
            place_id = 'fdcd221ac44fa326'

            # get as many tweets as you can before being rate limited and then end
            # the job
            try:
                while True:
                    tweets = api.search(q="place:%s" % place_id,
                                        lang='de',
                                        count='100',
                                        tweet_mode='extended')
                    for tweet in tweets:
                        tweet_dict = tweet._json
                        tweet_dict['_id'] = tweet_dict['id_str']
                        tweet_coll.find_one_and_update({'_id': tweet_dict['_id']},
                                                       {'$setOnInsert': tweet_dict},
                                                       upsert=True)
            except tweepy.RateLimitError:
                pass  # let the job end normally


For the Pos tagging the tweets found in the previous tweet collection are
tokenized, pos tagged and then written into a seperate mongodb collection to
make them available for later analyses::

    class TweetPOSTagger(CoreJob):
        """
        Tokenizes and POS tags all available tweets in the tweets
        collection and writes them to the mongo collection grouped by word
        lemma, word type and chunk type.
        The tokenizer strips the twitter handles.
        The POS tagger used is for german.
        """
        author = 'adi'

        def execute(self, *args, **kwargs):
            tweet_coll = self.config.twitter.api.tweet_coll
            pos_processed_strip_coll = \
                self.config.twitter.pos.pos_processed_strip_coll
            self.set_source('POS Tagger')

            cur = tweet_coll.find()
            for i, doc in enumerate(cur):
                tokenizer = TweetTokenizer(strip_handles=True)
                tmp_string = tokenizer.tokenize(doc['full_text'])
                s = [' '.join(tmp_string)]
                tokenized_string = [isinstance(s, str) and s.split(" ") or s for s
                                    in s]
                if tokenized_string:
                    try:
                        sentence_list = parsetree(tokenized_string,
                                                  tokenize=False,
                                                  lemmata=True)
                    except TypeError:
                        continue

                    for sentence in sentence_list:
                        for chunk in sentence.chunks:
                            for word in chunk.words:
                                dic = {}
                                dic['_id'] = '{}_{}_{}'.format(word.lemma,
                                                               word.type,
                                                               chunk.type)
                                dic['word'] = word.string
                                dic['word_category'] = word.type
                                dic['word_lemma'] = word.lemma
                                dic['chunk_category'] = chunk.type
                                dic['chunk_lemmata'] = chunk.lemmata
                                pos_processed_strip_coll.update_one(
                                    filter={'_id': dic['_id']},
                                    update={'$setOnInsert': dic},
                                    upsert=True)
                                pos_processed_strip_coll.update_one(
                                    filter={'_id': dic['_id']},
                                    update={'$inc': {'count': 1}},
                                    upsert=True)
                                # TODO: re-enable once the bug is fixed.
                                # requests.append(UpdateOne(filter={'_id':
                                # pos_dic['_id']}, update={'$set': pos_dic},
                                # upsert=True))
                                # requests.append(UpdateOne(filter={'_id':
                                # pos_dic['_id']}, update={'$inc': {'count': 1}},
                                # upsert=True))

                self.progress(i / cur.count())
            # TODO: re-enable once the bug is fixed
            # pos_unprocessed_coll.bulk_write(requests)

twitter.yaml example::

    DEFAULT:
      mongo_database: twitter

    pos:
      pos_processed_strip_coll: !connect mongodb://pos_processed_strip

    api:
      tweet_coll: !connect mongodb://tweets
      consumer_key:         #check local.yaml
      consumer_secret:      #check local.yaml
      access_token:         #check local.yaml
      access_token_secret:  #check local.yaml

local.yaml example::

    DEFAULT:
      mongo_url: mongodb://core:654321@localhost:27017
      mongo_database: core4dev

    logging:
      mongodb: INFO
      stderr: DEBUG
      stdout: ~

    worker:
      min_free_ram: 32

    api:
      setting:
        debug: True
        cookie_secret: hello world
      admin_password: hans

    twitter:
      api:
        consumer_key: #insert your own
        consumer_secret: #insert your own
        access_token: #insert your own
        access_token_secret: #insert your own