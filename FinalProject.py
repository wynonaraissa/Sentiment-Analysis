# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 21:27:18 2019

@author: Wynona Raissa
"""
#JANGAN LUPA:
#-bantu download library baru
import pandas as pd
import tweepy
import re
import nltk
import datetime
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from textblob import TextBlob
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
nltk.download('punkt')
nltk.download('stopwords')

#Authentication keys from Twitter.developer website
AccessToken='131425793-Ht2Q7g9zD0EdPkNHdhtffAfH0WIT31k6tmc316xj'
AccessTokenSecret= '44bvdQQEA7mb1Cq00VAkYJpeTvwqakxWNqYns1lVkhFts'
ConsumerKey= 'v8wA4vBhbfLYMzfi8jLptT3CY'
ConsumerSecret='DFRQnpQx9DqJLdgQSkWxGHny8EpGA4FMVgkOr5u83X5w1j8Zfc'


#Authorizing the keys
Authorization = tweepy.OAuthHandler(ConsumerKey, ConsumerSecret)
Authorization.set_access_token(AccessToken, AccessTokenSecret)
API=tweepy.API(Authorization, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
#Creating a dataframe to store tweets that are extracted through the API
TwitterData=pd.DataFrame(columns = ['TweetDate','UserLocation','Tweets', 'Username',
                                    'FavoriteCount', 'RTCount'])

def MainProgram():
    """
    The function to run the program. Calls all other functions. Program will ask if User wants to extract data by through Twitter API 
    or upload his own file. If Twitter API is chosen, program will ask User's preference by calling UserPreference() function. Program 
    will also ask number of data to be extracted. Data will be saved in a csv file and will be read and saved as a dataframe.
    Reading from a csv file will be more efficient.
    If uploading a file is chosen, User will be asked the filename and the file will be read and saved as a dataframe.
    Dataframe will then be cleaned by applying CleaningTweets() function and measured its polarity and sentiment by applying 
    Analysing Sentiment() function.
    
    Returns DashboardApp() function with the dataframe as its input. It will generate a web link: http://127.0.0.1:4050. 
    The web link will show a simple dashboard of the data visualization made from the data that the program generate.
    """
    Dummy=False
    while Dummy!=True:
        print('How dou you want to get your data? From Twitter API or upload your own file?')
        DataExtraction=input('Type API or UPLOAD:')
        if DataExtraction.lower()=='api':
            User=UserPreference() #Ask User's preferrence.
            Keyword=User[0]
            FileName=User[1]
            StartDate=User[2]
            EndDate=User[3]
            Dummy=False
            while Dummy!=True:
                try:
                    N=int(input("Number of data:")) #Ask User to input number of data to be extracted.
                    if N>0: #Make sure User input a positive number.
                        Dummy=True
                except ValueError: #Make sure User input an integer.
                    print("Your input is not an integer.")
            TwitterData=StreamTwitter(Keyword, StartDate, EndDate,N) #Extracting data.
            TwitterData.to_csv('{}.csv'.format(FileName)) #Saving data as a csv file.
            TwitterDataFrame = pd.read_csv('{}.csv'.format(FileName)) #Create a dataframe by reading the csv file.
            Dummy=True
        elif DataExtraction.lower()=='upload':
            FileName=input('Enter your filename:') #Ask User to enter a file name to be uploaded.
            TwitterDataFrame = pd.read_csv(FileName) #Create a dataframe by reading the csv file.
            Dummy=True
        else:
            print('WRONG INPUT! You can only enter either API or UPLOAD') #Make sure User input either API or UPLOAD only.

    TwitterDataFrame['CleanedTweet'] = TwitterDataFrame['Tweets'].apply(lambda x: CleaningTweets(x)) #Cleaning the tweets.
    TwitterDataFrame['TweetPolarity']=TwitterDataFrame['Tweets'].apply(lambda x: AnalysingSentiment(x)[0]) #Measuring each tweets polarity.
    TwitterDataFrame['TweetSentiment']=TwitterDataFrame['Tweets'].apply(lambda x: AnalysingSentiment(x)[1]) #In weach sentiment group is each tweet belongs to.
    #Optional: check the dataframe
    #print(TwitterDataFrame)
    return DashboardApp(TwitterDataFrame)

    
def UserPreference():
    """
    Asking User about his preference of keyword, filename, year, month and date of starting and ending date of tweets creation and store them as lists
    as it will be easier to retrieve the information back through its index. Then combine the year, month and date using datetime module.
    Datetime is a module that can manipulate date and time data.
    
    Returns the keyword, filename, start date and end date that User input.
    
    """
    Dummy=False
    while Dummy!=True:
        Keyword=[]
        FileName=[]
        UserKeyword=input('Keyword (in English): ') #Cannot check if Keyword in English because if User input a name, then it may not be detected as English
        Keyword.append(UserKeyword)
        UserFileName=input('Enter name for your file: ')
        FileName.append(UserFileName)
        Dummy2=False
        while Dummy2!=True:
            try:
                Year=[]
                Month=[]
                Date=[]
                UserStartYear=input('Enter Start Year:')
                UserStartMonth=input('Enter Start Month:')
                UserStartDate=input('Enter Start Date:')
                UserEndYear=input('Enter End Year:')
                UserEndMonth=input('Enter End Month:')
                UserEndDate=input('Enter End Date:')
                Year.append(UserStartYear)
                Year.append(UserEndYear)
                Month.append(UserStartMonth)
                Month.append(UserEndMonth)
                Date.append(UserStartDate)
                Date.append(UserEndDate)
                #Convert strings of numbers to integers so it will be accessible by the datetime modules.
                Year= [ int(x) for x in Year ]
                Month= [ int(x) for x in Month ]
                Date= [ int(x) for x in Date ]
                #Combine year, month and date using datetime module 
                StartDate = datetime.datetime(Year[0], Month[0], Date[0])
                EndDate = datetime.datetime(Year[1], Month[1], Date[1])
                if StartDate<=EndDate: #Make sure that StartDate is earlier than EndDate
                    Dummy2=True
                else: 
                    print('Your start time should be earlier than your end time!')
            except ValueError: #Make sure if the date entered exist (not out of range). For example Nov 31 2019 does not exist and return a ValueError.
                print('Date entered does not exist (out of range)!' )
        
        if Keyword[0]!='' and FileName[0]!='': #Make sure that User does not enter an empty string.
            Dummy=True
    
    return Keyword, FileName, StartDate, EndDate


#cari web untuk tweepy.Cursor
def StreamTwitter(KeyWord, StartDate, EndDate, N):
    """
    Performing twitter API calls to extract the tweets and data such as the creation date, location, username, and number of 
    likes and retweets. It will give an error if API calls limit has been reached. Catching the error and then sleep it for 5
    seconds to maintain TCP connection. After sleeping for 5 seconds, it will keep performing API calls limit even though limit has been reached.
    After 15 minutes, then there will be more tweets extracted.
    
    Returns a dataframe which consist of twitter data extracted through the API calls. 
    """
    Count=0 
    # Iterating through all tweets containing a specific keyword that User preferred, api search mode, also specifying tweets in English
    Tweets=tweepy.Cursor(API.search, q=KeyWord, lang='en').items()
    while True:
        try: 
            Tweet=Tweets.next()
            if Tweet.user.created_at<=EndDate and Tweet.user.created_at>=StartDate: #Extract data on a specific period
                TwitterData.loc[Count, 'TweetDate'] = Tweet.user.created_at   #Extract tweet's creation date and time 
                TwitterData.loc[Count, 'UserLocation'] = Tweet.user.location #Extract tweet's location
                TwitterData.loc[Count, 'Tweets'] = Tweet.text #Extract each tweets (text)
                TwitterData.loc[Count, 'Username'] = Tweet.user.name #Extract username
                TwitterData.loc[Count, 'FavoriteCount'] = Tweet.favorite_count #Extract number of likes 
                TwitterData.loc[Count, 'RTCount'] = Tweet.retweet_count #Extract number of retweets
                Count+=1 
                print(Count) #to check how many tweets has been streamed
                if Count==N: #Stop iterating when it reached the specific number of tweets that User preferred.
                    break
        except tweepy.TweepError as e: #Catching error when twitter API calls limit reached.
            print(e) #Print the error
            time.sleep(5) #Sleep so that it keeps on performing API calls every minute to maintain TCP connection
            continue
        except StopIteration:
            break
    return TwitterData

            
def CleaningTweets(Tweet):
    """
    Cleaning the tweets by removing any URLs, RTs (Retweets), usernames, hashtags (#), emojis,
    repeated characters, punctuations and stopwords from the raw tweets as they are unnecessary 
    for the sentiment analysis. Removing them will not affect the analysis. Note that stopwords 
    are common words such as 'a', 'an', 'the', etc. The sentence will be tokenized which means 
    splitting them to words. 
    
    Returns the joinned words (as strings)
    """
    UnwantedLetters=set(stopwords.words('english')+list(punctuation)+['AT_USER', 'URL']) #creating a set that contains english stopwords, punctuation, 'AT_USER', 'URL'
    Tweet = Tweet.lower() #Convert tweets into lower case.
    Tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', Tweet) #Removing URLs.
    Tweet = re.sub('\s*rt\s', '', Tweet) #Removing RTs.
    Tweet = re.sub('@[^\s]+', 'AT_USER', Tweet) #Removing any usernames.
    Tweet = re.sub(r'#([^\s]+)', r'\1', Tweet) #Removing any '#' signs.
    Tweet = Tweet.encode('ascii', 'ignore').decode('ascii') #Removing emojis as they may be missleading.
    Tweet = word_tokenize(Tweet) #Split sentence to words and remove repeated characters(eg: helloooooooo into hello).
    return ' '.join([Word for Word in Tweet if Word not in UnwantedLetters])


def AnalysingSentiment(Tweet):
    """
    Doing sentiment analysis of the tweets (cleaned) using TextBlob library which has sentiment.polarity method.
    TextBlob is a library for processing textual data that have a simple API to dive into common natural language
    processing tasks such as sentiment analysis. Variable Polarity is a float between -1 and 1. 
    Tweet has a positive sentiment if its polarity is between 0 and 1 (exclude 0, include 1), neutral sentiment if polarity 
    is 0 and negative sentiment if polarity between -1 and 0 (include -1, exclude 0). 
    
    Returns the tweet's polarity as floats and its Sentiment (Positive, Neutral or Negative) as strings.
    """
    Analysis=TextBlob(Tweet)
    Polarity=Analysis.sentiment.polarity
    if Analysis.sentiment.polarity==0:
        Sentiment='Neutral'
    elif Analysis.sentiment.polarity>0:
        Sentiment='Positive'
    else:
        Sentiment='Negative'
    return Polarity, Sentiment


def OverallSentiment(DataFrame):
    """
    Preparing data for plotting a pie chart in the dashboard. Data about number of total tweets
    that has positive, neutral and negative sentiment.
    
    Returns the total number of tweets in each of the sentiment groups (Positive, Neutral and Negative) 
    and the Sentiment groups.
    """
    Frequency=DataFrame['TweetSentiment'].value_counts()
    Sentiment=['Positive', 'Neutral', 'Negative']
    return Frequency, Sentiment


def LineChart(DataFrame):
    """
    Preparing data for plotting a line chart in the dashboard. Data about number of total tweets for each sentiment group, grouped by the dates.
    
    Returns the data for negative, neutral and positive sentiment and dataframe.
    """
    DataFrame['TweetDate']= pd.to_datetime(DataFrame['TweetDate']) #Convert to datetime format.
    DataFrame['TweetDate']=DataFrame['TweetDate'].dt.strftime('%Y-%m-%d') #Convert to date format to YYYY-MM-DD, removing timestamp
    SubsetData=DataFrame[['TweetDate', 'TweetSentiment']] #Creating a new dataframe consisting only TweetDate and TweetSentiment column
    GroupedData=SubsetData.groupby('TweetDate')['TweetSentiment'].value_counts().unstack().fillna(0) #Group by TweetDate and count number of tweets that are included in each sentiment group in each date. If there is no tweet, then it will be 0.
    #Preparing data for line chart, specifying the data for x and y axis, color, legend and also mode of chart.
    #Negative sentiment data
    Trace1=go.Scatter(
            x=GroupedData.index,
            y=GroupedData.Negative,
            marker=dict(color='red'),
            mode='markers+lines',
            name='Negative Sentiment')
    #Neutral sentiment data
    Trace2=go.Scatter(
            x=GroupedData.index,
            y=GroupedData.Neutral,
            mode='markers+lines',
            name='Neutral Sentiment')
    #Postitive sentiment data
    Trace3=go.Scatter(
            x=GroupedData.index,
            y=GroupedData.Positive,
            mode='markers+lines',
            name='Positive Sentiment')
    return Trace1, Trace2, Trace3, GroupedData
 
    
def FrequencyDist(CleanedTweetColumn): #dipanggil FrequencyDist[Twitterdata['CleanedTweet']]
    """
    Preparing data for plotting in dashboard. Data about the number of occurences of each cleaned words.
    Cleaned tweets will be tokenized (split into words) and frequency of words (number of occurence) 
    is counted using nltk.FreqDist. Natural Language Toolkit (NLTK) is a library for Natural Language 
    Processing. Generally, a frequence distribution (FreqDist) records the number of times each outcome of an experiment
    occurred, which here applied to count the frequency of each word in a document/data frame.
    It will create a new data frame Result that only generate the most 20 common words from the original data frame.
    The data frame will include 2 columns, the words and its frequency. 
    
    Returns a list of words and frequency. Converted to list as it will be easier to retrieve each
    word and its frequency through the lists index.
    """
    #CleanedTweetColumn is a series.
    Standardized=CleanedTweetColumn.str.cat(sep=' ') #Converting series to strings. Note that str.cat concatenates strings.
    Words=word_tokenize(Standardized) #Splitting strings into words.
    WordDist=nltk.FreqDist(Words)
    Result = pd.DataFrame(WordDist.most_common(20),
                    columns=['Word', 'Frequency']) #Create a new data frame of words and its frequency.
    return Result['Word'].tolist(), Result['Frequency'].to_list() #Converted to list so it will be easier to retrieve each word and its frequency through its index.


def DashboardApp(DataFrame):
    """
    Creating a dashboard using Dash and Plotly to plot the data visualization. 
    In the dashboard the program will answer 3 questions:
        1. How is the overall sentiment analysis distribution? How much (in percentage) of the tweets has a positive, neutral and negative sentiment?
        2. How is the sentiment analysis distribution based on each day? 
        3. What are the most 20 common words mentioned in the tweet data? What are each of its frequency?
    
    When running the program, there will be a link mentioned in the console. If the web does not appear, User can click or copy and run the link in his browser.
    Link: http://127.0.0.1:4050
    """
    NumberOfData=DataFrame.shape[0] #Extracting number of data by finding out number of rows of dataframe.
    StartDate=LineChart(DataFrame)[3].index.min() #Finding out the starting (first) date of data
    EndDate=LineChart(DataFrame)[3].index.max() #Finding out the ending (last) date of data
    #Note that we could not extract the data above from UserPreference() as the function will only be called if User choose to 
    #extract tweets through Twitter API. This is to accomodate if User chose to upload his own file.
    
    #Creating the app
    App=dash.Dash()
    App.layout=html.Div([
            html.H1(children='Twitter Sentiment Analysis',
                    style = {'textAlign':'center'}), 
            html.Div(children="This dashboard shows the sentiment analysis of {} tweets which were made within period {} & {}.".format(NumberOfData, StartDate, EndDate), 
                     style={'textAlign': 'center'}),
            
            dcc.Graph(
                    id='OverallSentiment',
                    figure={
                            'data': [
                                    go.Pie(labels= OverallSentiment(DataFrame)[1], values=OverallSentiment(DataFrame)[0],hole=0.3,
                                    marker=dict(colors=['green','orange','red']))
                                    
                                    ],
                            'layout': go.Layout(
                                    title= 'Overall Sentiment Analysis')
                                    }),
            dcc.Graph(
                    id='LineChart',
                    figure={
                            'data': [LineChart(DataFrame)[0], LineChart(DataFrame)[1], LineChart(DataFrame)[2]],
                            'layout': go.Layout(
                                    title= 'Sentiment Analysis Based on Tweets Date',
                                    xaxis_title= 'Tweets Date',
                                    yaxis_title='Number of Tweets')
                                    }),                        
                            
            
            dcc.Graph(
                    id='FrequencyDist',
                    figure={
                            'data':[
                                    go.Bar(x=FrequencyDist(DataFrame['CleanedTweet'])[0], y=FrequencyDist(DataFrame['CleanedTweet'])[1])
                                    ],
                            'layout': go.Layout(
                                    title='Most 20 Common Words Frequency',
                                    xaxis_title='Most 20 Common Words',
                                    yaxis_title='Frequency')
                                    })
            ])
    
    if __name__=='__main__':
        App.run_server(port=4050) #Running the app with a specified port.
    #Do not quit CTRL+C to see the app running.

#Calling the main program
MainProgram()      

