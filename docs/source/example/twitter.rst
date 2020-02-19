###########################################################
retrieval and pos tagging of tweets
###########################################################

This project can be found on GitHub as well:
https://github.com/Alioun/twitter/

The following example shows a simple and easy way of how you can use core to
realize a wide variety of tasks, in this case retrieving tweets from a
particular place and then running a Part of Speech (POS) tagger over the
retrieved tweets to build a base for further analyses on them.

* Third-party packages used in this example:
    * tweepy: Tweepy is an easy-to-use, yet powerful way to use the various
      twitter APIs. In our case tweepy is only used to access the "Geo Search"
      API and the standard "Search" API.
      https://github.com/tweepy/tweepy
    * nltk: NLTK is short for "Natural Language Toolkit" and is a library combining
      many different libraries used for NLP into one convenient package.
      In this example, we only use the TweetTokenizer provided by NLTK to try to
      clean up the tweets while also tokenizing them for the POS tagger. 
      https://github.com/nltk/nltk , https://www.nltk.org/
    * pattern: Another library for NLP and much more. We will only use the POS
      tagger from its German module.
      https://github.com/clips/pattern

Imports::

    import tweepy
    from core4.queue.job import CoreJob
    from nltk.tokenize.casual import TweetTokenizer
    from pattern.text.de import parsetree

The first part is to retrieve the tweets.

To be able to retrieve any tweets, you need to have Twitter Developer account
and need to create an app within that account. If you don't have these already,
you can create them over at https://developer.twitter.com/ and 
https://developer.twitter.com/en/apps respectively.
After you are done, go into the app's "Details" and then to the "Keys and tokens"
tab. Here, you can find your Consumer API keys. Note that you have to generate a
access token and its secret if you have never generated it before and regenerate
the two if you don't have previously generated values saved anywhere.

Copy all four - consumer API key, consumer API secret key, access token and access
token secret - into your local.yaml. You can find example twitter.yaml and
local.yaml files below.

With the authorization requirements cleared, we will query the Geo Search API to
get the place ID for a specific region (Germany in this case). Using that place ID,
we can query Twitter for all tweets coming from that region.

The job is set up to stop execution and terminate when it encounters a rate
limit error. Twitter's rate limit timeframe is 15 minutes, so the job is scheduled
to get as much data as it can until being rate-limited every 20 minutes.

All retrieved tweets are written into a MongoDB collection for easy access
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


For the POS tagging, the tweets found in the previous tweet collection are tokenized,
POS tagged and then written into a seperate MongoDB collection to make them available
for later analyses::

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

Example of the project yaml (twitter.yaml)::

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

Example of the local.yaml file::

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
