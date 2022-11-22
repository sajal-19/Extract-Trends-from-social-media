#!/usr/bin/env python
# coding: utf-8

# In[1]:


#importing libaries
import tweepy
import pandas
from wordcloud import WordCloud 
from textblob import TextBlob
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import os
from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt')
import csv
from collections import Counter
from nltk.corpus import stopwords
nltk.download('stopwords')
import string
stop_words = stopwords.words()
import time
import random


# In[2]:


# selfmade dataset of stop words for more accurate result
newdf=pd.read_csv("fashion.csv")
newdf['hashtags']=newdf['hashtags'].str.lower()
hashtags=newdf['hashtags'].to_list()


# In[3]:


# twitter api keys and tokens (reading from a Access csv file)
twt=pd.read_csv("Access.csv")

consumerKey=twt['consumerKey'][0]
consumerKeySecret=twt['consumerKeySecret'][0]
accessToken=twt['accessToken'][0]
accessTokenSecret=twt['accessTokenSecret'][0]


# In[4]:


# twitter authentication
auth=tweepy.OAuthHandler(consumerKey,consumerKeySecret) #create OAuthHandler object

auth.set_access_token(accessToken,accessTokenSecret) #set access token and secret

api=tweepy.API(auth,wait_on_rate_limit=True) #create tweepy API object to fetch tweets


# In[5]:


# Data cleaning (removing special characters,urls etc)
def cleanTxt(text):
    text=re.sub(r'@[A-Za-z0-9]+','',text)
    text=re.sub(r'#','',text)
    text=re.sub(r'RT[\s]+','',text)
    text=re.sub(r'https?:\/\/\S+','',text)
    return text 


# In[6]:


#polarity (finding the polarity of tweets)
def getPolarity(text): 
    return TextBlob(text).sentiment.polarity


# In[7]:


# extract tweets from hashtags for a particular period of time
def scrape(words, date_since, numtweet,n):
   
        db = pd.DataFrame(columns=['username',
                                   'description',
                                   'location',
                                   'following',
                                   'followers',
                                   'retweetcount',
                                   'text',
                                   'hashtags','polarity'])# Creating dataframe using pandas library
        tweets = tweepy.Cursor(api.search_tweets,
                               words, lang="en",
                               since_id=date_since,
                               tweet_mode='extended').items(numtweet) #tweet extraction
        list_tweets = [tweet for tweet in tweets]
        i=1
        for tweet in list_tweets:
                username = tweet.user.screen_name 
                description = tweet.user.description 
                location = tweet.user.location
                following = tweet.user.friends_count
                followers = tweet.user.followers_count
                retweetcount = tweet.retweet_count
                hashtags = tweet.entities['hashtags']
                try:
                        text = tweet.retweeted_status.full_text
                except AttributeError:
                        text = tweet.full_text
                polarity=getPolarity(text)
                print(polarity)
                hashtext = list()
                for j in range(0, len(hashtags)):
                        hashtext.append(hashtags[j]['text'])
                ith_tweet = [username, description,
                             location, following,
                             followers,
                             retweetcount, text, hashtext,polarity]
                if(polarity>=0):   #collecting tweets having polarity greater than zero(Neutarl and positive tweets)
                    db.loc[len(db)] = ith_tweet 
 
                i = i+1
        db['text']=db['text'].apply(cleanTxt) #clean tweets
        db['text']=db['text'].apply(word_tokenize)  #tokenize tweets
        row=len(db)
        field_names =['hashtags','tweets']
        dict = {"hashtags":words,"tweets":row}

        with open('tweets.csv', 'a') as csv_file:
            dict_object = csv.DictWriter(csv_file, fieldnames=field_names) 
            dict_object.writerow(dict) # stroing frequency of tweets for products in a csv file(tweets)
        filename ="twitterdata.csv"
        db.to_csv(filename,mode='a')# stroing tweets in a csv file(twitterdata)
        print(db)


# In[8]:


#reading  fashion products dataset and extarcting tweets for all products
products=pd.read_csv("product.csv")
n=len(products)
print(n)
for i in range(0,n):
    word="#"+products['Fashion'][i]
    #scrape(word,20-6-2022,10000,i) #scraping already done


# In[9]:


#reading  tweets dataset(having frequency counts of all products) to find all trending products
dt=pd.read_csv("tweets.csv")
sortedframe=dt.sort_values(by=['tweets'],ascending=False)  #sort the dataframe on the basis of no of tweets
sortedframe.head(10) # top 10 products


# In[10]:


#analysing top ten products tweet prequency with graph using matplotlib
text=sortedframe.head(10)
text.plot(x="hashtags", y="tweets", kind="bar")


# In[11]:


#data cleaning for hashtags
def cleaning(text):        
    text = re.sub('https?://\S+|www\.\S+', '', str(text))
    text = re.sub('<.*?>+', '', str(text))
    text = re.sub('[%s]' % re.escape(string.punctuation), '', str(text))
    text = re.sub('\n', '', str(text))
    text = re.sub('[’“”…]', '', str(text))     

    emoji= re.compile("["
                           u"\U0001F600-\U0001F64F" 
                           u"\U0001F300-\U0001F5FF"
                           u"\U0001F680-\U0001F6FF" 
                           u"\U0001F1E0-\U0001F1FF" 
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    text = emoji.sub(r'', text)          
    text_tokens = word_tokenize(text) # tokenization
    new_words= [word for word in text_tokens if not word in stop_words] #removing stopwords
    related_words= [word for word in new_words if not word in hashtags] # removing stopwords (self made dataset of stopwords) 
    filtered_text= (" ").join(related_words)
    text = filtered_text
    
    return text


# In[12]:


#find sub-products using hashtags analysis of tweets 
dt=pd.read_csv("hashtags.csv")
text=dt['watches'].str.lower()
text=text.apply(cleaning)
p = Counter(" ".join(text).split()).most_common(20) #frequecy analysis of words (finding most occuring words)
rslt = pd.DataFrame(p, columns=['Word', 'Frequency'])
print(rslt)


# In[13]:


# analyze with help of graph using matplotlib
rslt.plot(x="Word", y="Frequency", kind="bar")


# In[14]:


# analyze with help of graph using matplotlib
rslt.plot(x="Word", y="Frequency", kind="line")


# In[15]:


# extracting tweet url for a particular sub products
def get_tweet_url(tweet):
    tweet_id = tweet.id_str
    screen_name = tweet.user.screen_name

    tweet_url = "https://twitter.com/{screen_name}/status/{tweet_id}"
    tweet_url = tweet_url.format(screen_name=screen_name,tweet_id=tweet_id)
    
    return tweet_url


# In[16]:


# extracting tweet url for a particular sub products and media url
hashtags = ["#rolex Watch"]
folder_name = "downloaded_media"
for i in hashtags:
    query=i
    print("Query: ",query)
    
    new_tweets=api.search_tweets(q=query,tweet_mode='extended')
    for tweet in new_tweets: 
        tweet_url=get_tweet_url(tweet)
        print("tweet_url:",tweet_url)
        if not tweet.retweeted:
            print("ID:",tweet.id)
            if 'media' in tweet.entities:
                for image in  tweet.entities['media']:
                    print("Mediaurl:",image['media_url'])
                else:
                    pass


# In[ ]:





# In[ ]:




