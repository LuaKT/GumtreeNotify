from __future__ import print_function
import json, re, sys
from bs4 import BeautifulSoup
import smtplib
import time
import random
import pprint

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

try:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
except:
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
sleepTime = 1 * 60 # 1 Minute(s)

listings = []
listings_old = []
listings_new = []

def parse_results(search_url):
    results = []
    soup = BeautifulSoup(urlopen(search_url).read(), "html.parser")
    listings = soup.find('ul', {"data-q":"naturalresults"}).find_all("article", class_="listing-maxi")
    
    for listing in listings:
        id = listing['data-q'][3:]
        url = "https://gumtree.com" + listing.find("a", class_="listing-link").get('href')
        title = listing.find("h2", class_="listing-title", text=True).get_text(strip=True)
        price = listing.find("strong", class_="listing-price", text=True).get_text(strip=True)
        
        results.append({'id': id, 'url': url, 'title': title, 'price': price})
    #print(results)
    return results

def new_listings(results_old, results):
    listings_new = []
    check = set([d['id'] for d in results_old])
    differences = [d for d in results if d['id'] not in check]
    
    for d in differences:
        listings_new.append(d)

    return listings_new

def send_mail(listings):

    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = "Gumtree Listings (%s)" % len(listings)
    message = 'New gumtree listings for URL: ' + searchURL + "\n\n"
    for listing in listings:
        message = message + "%s - %s" % (listing["title"], listing["price"]) + "\n"
        message = message + listing["url"] + "\n\n"
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

    print("** Mail sent!")

    mailserver.quit()


if __name__ == '__main__':
    try:
        email_username = sys.argv[1]
        email_password = sys.argv[2]
        email_server = sys.argv[3]
        email_from = sys.argv[4]
        email_to = sys.argv[5]
        searchURL = sys.argv[6]

    except IndexError:
        exit("Missing arguments")

    print("Checking for listings at: " + searchURL)
    #Populate result array with new listings
    listings = parse_results(searchURL)

    while True:
        print("Checking gumtree now")
        try:
            #Move old results to cache
            listings_old = listings
            #Clear listings table for new fetch
            listings = []
            #Fetch new listings
            listings = parse_results(searchURL)
            #If page broken, use old listings
            if not listings:
                listings = listingCache

            #Compare listings with cache, check for new results, send mail
            listings_new = new_listings(listings_old, listings)
            if listings_new:
                print("New listings! Sending mail")
                send_mail(listings_new)
            else:
                print("No new listings")
        except Exception as e:
            print(str(e) + '\n!Failed!')
        print("Sleeping for %d seconds" % sleepTime)
        time.sleep(sleepTime + random.randint(0, 20)) #Sleep for set time + random between 0 and 20 seconds
