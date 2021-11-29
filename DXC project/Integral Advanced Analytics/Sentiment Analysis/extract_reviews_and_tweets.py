# This code is a webcrawler to extract user reviews on Insurance Policies.
# In this code data is retrieved from two sources :
    # policybazaaar.com - Reviews posted by users who own Motor Insurance
    # Twitter : API based retrival of tweets posted to twitter handles of 28 Different Insurance Companies 
    # operating in India

# Developer : Tanmay Bhardwaj
# Dated : 11 February 2020
# Team : Integral Business Analytics

# Import the packages and methods for webcrawler
from bs4 import BeautifulSoup
import requests
import pandas as pd

#Import the necessary methods from tweepy library
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from datetime import datetime
from tweepy import Stream
import tweepy as tw
import pandas as pd

# Arrays
car_insurance_url_list = list()
car_insurance_company_list = list()

# Lists 

# Dataframes
web_list = pd.DataFrame()
social_media_data = pd.DataFrame()

# Enter Twitter API Keys, replace them with latest keys
access_token = ****
access_token_secret = ****
consumer_key = ****
consumer_secret = ****

# Autheticate Twitter API Keys
auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth,search_root="",  search_host='search.twitter.com', wait_on_rate_limit=True)

# Dictionary of companies with their twitter handles and name
companies = { 'BajajAllianz' : 'Bajaj Allianz Car Insurance', 'BhartiAXAGI' :'Bharti Axa Car Plan',  
              'CholaMS': 'Cholamandalam Car Insurance Plan', 'Future_Generali': 'Future Generali Car Insurance Plan',
              'HDFCERGOGIC': 'Hdfc Ergo Car Insurance Plan', 'iffco_tokio': 'Iffco Tokio Car Insurance Insurance', 
              'LibertyGILtd': 'Liberty Videocon Car Insurance', 'NICLofficial': 'National Insurance Car Insurance', 
              'NewIndAssurance' : 'New India Assurance Car Insurance', 'oiclinsurance': 'Oriental Insurance Car Insurance', 
              'rahejaqbe' : 'Raheja Qbe Car Insurance', 'RelianceGenIn': 'Reliance General Car Insurance', 
              'royalsundaram': 'Royal Sundaram Car Insurance', 'sbigeneral': 'Sbi General Car Insurance',
              'Shriram_GI': 'Shriram General Car Insurance', 'TATAAIGIndia' : 'Tata AIG Car Insurance Insurance',
              'UIIC_Ltd': 'United India Car Insurance', 'Universal_Sompo':'Universal Sompo Car Insurance',
              'AvivaIndia' : 'Aviva Life Insurance', 'relnipponlife':'Reliance Nippon Life Insurance',
              'LICIndiaForever':'LIC India', 'ICICIPruLife':'ICICI Prudential Life Insurance', 'SBILife':'SBI Life Insurance',
              'HDFCLIFE':'HDFC Life Insurance', 'HDFCLife_Cares' : 'HDFC Life Insurance', 'MAXLifeIns':'MAX Life Insurance',
              'TataAIA_Life': 'Tata AIA Life Insurance' } 
           

# Function to reach landing page of company (passed in URL), then call another function to 
# reach 'review' page for the company. From there get all the reviews and return them in a dataframe
# to the calling function
def get_company(company_url):
    reviews_url = ''        
    company_url = company_url
    company_request = requests.get(company_url, headers=headers)
    
    # Use BeautifulSoup to parse HTML page
    company_page = BeautifulSoup(company_request.content, "html.parser")
    # Get URL of Car Insurance Company Review Web Page
    company_review_url = company_page.findAll('div', {"class": "rate-it-now"})
    
    if len(company_review_url) > 0:
        # Read Car Insurer Company Name and save URL of Review Page
        for a in company_review_url:
            for link in a.findAll('a'):                
                if link.get('id') != "hrefwritereview":
                    reviews_url = link.get('href')

        # Call second function to access the URL which has all the reviews, scrap them and send back as a dataframe
        all_reviews = get_reviews(reviews_url)
        return(all_reviews)

def get_reviews(url):
    reviews_url = requests.get(url, headers=headers)

    # # Use BeautifulSoup to parse HTML page
    reviews_soup = BeautifulSoup(reviews_url.content, "html.parser")
    # Get Company Name
    company = reviews_soup.find('h1')
    # Get Rater Information
    rater_info = reviews_soup.findAll('div', {"class": "rater-info"})
    # Get all reviews for the company
    all_reviews = reviews_soup.findAll('div', {"class": "revie-descr"})
    # Initialise list to store data
    serial_number_list = list()
    company_list = list()
    review_list = list()
    review_date_list = list()
    rater_location_list = list()
    # Initialise row counter
    serial_number = 1
    # Array to save rater Details
    rater_array = []
    # Dataframe Columns to store details
    df_bs_columns=['Serial Number', 'Source', 'Tweet Source', 'Company', 'Review Date', 'User Location', 'Review']

    # Function to check if a string has digits in it, needed to separate review date and user location
    # as they are present in same HTML tag
    def count_digit(input_string):
        digit_count = 0
        digit_count = sum(list(map(lambda x:1 if x.isdigit() else 0,set(input_string))))
        return(digit_count)

    # Loop through each review and save to the list
    for review_class in all_reviews:
        review = review_class.findAll('p')    
        for i in review:
            review_text = i.text        
            serial_number_list.append(serial_number) 
            # remove words ' Reviews & Rating' from company name
            company_name = company.text.replace('Reviews & Rating','')  
            print(company_name)
            company_list.append(company_name)
            review_list.append(review_text)        
            serial_number +=1 
    
    df_bs = pd.DataFrame(serial_number_list,columns=['Serial Number'])
    df_bs['Source'] = 'Web'
    df_bs['Tweet Source'] = 'Not Applicable'
    df_bs['Company'] = pd.DataFrame(company_list)
    df_bs['Review'] = pd.DataFrame(review_list)

    # Loop through each Rater and save Review Date and Rater location
    for rater_class in rater_info:
        rater = rater_class.get_text(separator = '\n')    
        countX = count_digit(rater)    
        if countX > 2:
        # Add rater Location and Review Date to Array    
            rater_array.append(rater)    

        # Loop through the rater Array, extract Rater Location and Date of Review and save to the list
    for data in rater_array:
        rater_data = data
        # Get rater location
        rater_location = rater_data.splitlines()[0]
        # Get date of review
        review_date = rater_data.splitlines()[1]
        # Save rater details
        rater_info = [rater_location, review_date]
        review_date_list.append(review_date)
        rater_location_list.append(rater_location)
            
    # Add data to dataframe
    df_bs['Review Date'] = pd.DataFrame(review_date_list)
    df_bs['User Location'] = pd.DataFrame(rater_location_list)

    # Set Index for the dataframe
    df_bs = df_bs.reindex(columns = df_bs_columns)
    return(df_bs)


# function to get company name from 'companies' dictionary
def get_company_name(twitter_handle):
    twitter_handle = twitter_handle.replace('@','')  
    company_name = companies[twitter_handle]
    return (company_name)

# fuction to extract data from tweet object
def extract_tweet_attributes(tweeter_handle,tweet_object):
    # create empty list
    tweet_list =[]
    i = 1
    twitter = 'Twitter'
    company_handle = tweeter_handle    
    company = get_company_name(company_handle)

# loop through tweet objects
    for tweet in tweet_object:       
        source = twitter
        text = tweet.text # utf-8 text of tweet
        created_at = tweet.created_at # utc time tweet created
        source = tweet.source # utility used to post tweet
        location = tweet.user.location # loation of user who made the tweet
        
        # append attributes to list
        tweet_list.append({'Serial Number':i,
                          'Source':twitter,
                          'Company':company, 
                          'Review Date':created_at,
                          'User Location':location,
                          'Review':text,
                          'Tweet Source':source})
        #i=i+1                  
    # create dataframe   
    df = pd.DataFrame(tweet_list, columns=['Serial Number',
                                           'Source',
                                           'Tweet Source',
                                           'Company',
                                           'Review Date',
                                           'User Location',
                                           'Review'])
    return df

# Dataframe to save all the tweets
all_tweets = pd.DataFrame()

# Set URL to fetch data for car insurance
# We have used policbazar.com website to get reviews and ratings
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'}
car_insurance_url = "https://www.policybazaar.com/motor-insurance/car-insurance/"
car_insurance_request = requests.get(car_insurance_url, headers=headers)

# Use BeautifulSoup to parse HTML page
car_insurance_soup = BeautifulSoup(car_insurance_request.content, "html.parser")
# Get Car Insurance Company Names
car_insurance_info = car_insurance_soup.findAll('div', {"id": "pbNewsss"})

# Read Car Insurer details and save their names and URLs
for li in car_insurance_info:
    for link in li.findAll('a'):        
        car_insurance_url_list.append(link.get('href'))
        car_insurance_company_list.append(link.text)

for url in car_insurance_url_list:
    review_list = get_company(url)        
    review_pd = pd.DataFrame(review_list)    
    web_list = web_list.append(review_pd, ignore_index = True)   

web_list.to_csv('policy_bazaar_car_insurance_reviews.csv', index = True)

# Date since which tweets are to be collected
date_since = '2010-01-01'
# List of companies to get their tweets
twitter_accounts = ['@BajajAllianz', '@BhartiAXAGI','@CholaMS','@Future_Generali','@HDFCERGOGIC','@iffco_tokio','@LibertyGILtd',
'@NICLofficial', '@NewIndAssurance','@oiclinsurance','@rahejaqbe','@RelianceGenIn','@royalsundaram','@sbigeneral','@Shriram_GI',
'@TATAAIGIndia','@UIIC_Ltd','@Universal_Sompo', '@AvivaIndia', '@relnipponlife','@LICIndiaForever', '@ICICIPruLife', '@SBILife',
'@HDFCLIFE', 'HDFCLife_Cares', '@MAXLifeIns', '@TataAIA_Life']


# Retrieve tweets for all the companies since 1 Jan 2019
for i in twitter_accounts:
    company_tweets = tw.Cursor(api.search, q=i, lang="en", since=date_since).items(1000) 
    all_tweets = all_tweets.append(extract_tweet_attributes(i,company_tweets))


# Write to csv
all_tweets.to_csv('insurance_companies_tweets.csv', index = False)


#web_list.columns = tweet_list.columns
web_list.columns = all_tweets.columns

# Add both dataframes
social_media_data = pd.concat([web_list,all_tweets], ignore_index = True)

# Drop Serial Number from the dataframe
social_media_data = social_media_data.drop(['Serial Number'], axis = 1)

# Write to csv
social_media_data.to_csv('all_social_media_data.csv', index = False, encoding="utf-8")
