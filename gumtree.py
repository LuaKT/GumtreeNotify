import json, re, sys
import urllib2
from bs4 import BeautifulSoup
import smtplib
import time
import random
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import pprint

sleepTime = 10 * 60 # 10 Minutes

try:
    email_username = sys.argv[1]
    email_password = sys.argv[2]
    email_server = sys.argv[3]
    email_from = sys.argv[4]
    email_to = sys.argv[5]
    searchURL = sys.argv[6]

except IndexError:
    exit("Missing arguments")

listings = []
listingCache = []
newListings = []

def getListings():
    tmpListings = []
    content = urllib2.urlopen(searchURL).read()
    bs = BeautifulSoup(content, 'html.parser')
    #bs = BeautifulSoup(open("test.html"), 'html.parser')


    #Get each lisiting
    for listing in bs.find("ul", {"data-q":"naturalresults"}).find_all("article", class_="listing-horizontal"):
        content = listing.find("div", class_="listing-content")
        adId = listing['data-q'][3:]
        link = listing.find("a", class_="listing-link").get('href')

        title = content.find("h2", class_="listing-title", text=True).get_text(strip=True)
        description = content.find("p", {"itemprop" : "description"}, text=True).get_text(strip=True)
        price = content.find("strong", {"itemprop" : "price"}, text=True).get_text(strip=True)
        location = re.findall(r'[ \w]+, [ \w]+', content.find("div", class_="listing-location").get_text(strip=True))[0]

        #Append dictionary to listings array
        tmpListings.append(dict(AdID=adId, Name=title, Description=description, Price=price, Location=location, Link=link))
    printArray(tmpListings)		
    return tmpListings

def checkListings():
    hashes = []
    cachedHashes = []
    tmpNewListings = []
    differences = [x for x in listings if x not in listingCache]
    
    for d in differences:
        tmpNewListings.append(d)

    return tmpNewListings

def send_mail():

    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = "Gumtree Listings (%s)" % len(newListings)
    message = 'New gumtree listings for URL: ' + searchURL + "\n\n"
    for listing in newListings:
        message = message + "%s - %s" % (listing["Name"], listing["Price"]) + "\n"
        message = message + "http://gumtree.com%s" % (listing["Link"]) + "\n\n"
    message = message + ''

    msg.attach(MIMEText(message.encode('utf-8'), 'plain', 'UTF-8'))

    mailserver = smtplib.SMTP(email_server,587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(str(email_username), str(email_password))

    mailserver.sendmail(email_from, email_to, msg.as_string())

    print "** Mail sent!"

    mailserver.quit()

def printArray(arr):
    for item in arr:
        print item["Name"].encode("utf-8")


if __name__ == '__main__':
    print "Checking for listings at: " + searchURL
    #Populate result array with new listings
    listings = getListings()

    while True:
        print "Checking gumtree now"
        try:
            #Move old results to cache
            listingCache = listings
            #Clear listings table for new fetch
            listings = []
            #Fetch new listings
            listings = getListings()
            #If page broken, use old listings
            if not listings:
                listings = listingCache

            #Compare listings with cache, check for new results, send mail
            newListings = checkListings()
            if newListings:
                print "New listings! Sending mail"
                send_mail()
            else:
                print "No new listings"
        except Exception, e:
            print str(e) + '\n!Failed!'
        print "Sleeping for %d seconds" % sleepTime
        time.sleep(sleepTime + random.randint(0, 20)) #Sleep for set time + random between 0 and 20 seconds
