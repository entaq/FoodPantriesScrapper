import requests
from bs4 import BeautifulSoup
from bs4 import Tag
import re
import csv

class KitchenRecord:
    pass

kitchens_records = []

def printKitchenDetails(kitchen_record):
    response = requests.get(kitchen_record.url)
    soup = BeautifulSoup(response.content, "html.parser")
    address_div = soup.find('div',{'class':'grid_8'})

    script_div = soup.find_all('script')[12]
    m = re.search('data: "(.*?)"', script_div.text)
    query_string = m.group(1)

    #trickery here as the address details is hidden behind an ajax call that requires a manual cick
    response = requests.get('http://www.foodpantries.org/address/get_address.php?'+query_string,
                            headers={'Referer':'http://www.foodpantries.org'})

    mini_soup = BeautifulSoup(response.content,'html.parser')
    # print kitchen_record.url
    if isinstance(mini_soup.contents[1],Tag):
        website_line = mini_soup.contents[1].text.strip()
    else:
        website_line = mini_soup.contents[1].strip()

    m = re.search('^Website: (.*?)$', website_line)
    website = m.group(1)
    kitchen_record.street_address = mini_soup.contents[4].strip()
    kitchen_record.city_state = address_div.contents[12].strip()
    kitchen_record.phone_number = address_div.contents[14].strip()
    kitchen_record.website = website
    kitchens_records.append(kitchen_record)


def printKitchensInCity(state_name, state_url, state_count,listing_url,city_name,city_record_count):
    response = requests.get(listing_url)
    soup = BeautifulSoup(response.content, "html.parser")

    listing_soup = soup.find_all('div', {'class':'grid_8'})[0]
    listings = listing_soup.find_all('h2')
    #skip the first two links as they're not for the kitchens
    #use the count from the city listing as we don't want "nearby"
    count = int(city_record_count) + 2
    i = 1
    for x in range(2,count) :
        kitchen = listings[x].find('a')
        kitchen_record = KitchenRecord()
        kitchen_record.state_name = state_name
        kitchen_record.state_url = state_url
        kitchen_record.state_count = state_count
        kitchen_record.city_name = city_name
        kitchen_record.city_listing_url = listing_url
        kitchen_record.city_record_count = city_record_count
        kitchen_record.number = str(i)
        kitchen_record.name = kitchen.text
        kitchen_record.url = kitchen['href']
        printKitchenDetails(kitchen_record)
        i = i + 1


response = requests.get('http://www.foodpantries.org/')
soup = BeautifulSoup(response.content,'html.parser')
states = soup.find('div',{'class':'multicolumn'}).find_all('li')


for state in states:
    state_url = state.find('a')['href']
    state_name = state.find('a').text
    state_count = str(state.find('em').text).translate(None,'()')
    response = requests.get(state_url)
    soup = BeautifulSoup(response.content, "html.parser")
    state_soup = soup.find_all('div', {'class':'widget'})[1]
    for links in state_soup.find('ul').find_all('a'):
        listing_url = links['href']
        m = re.search('^(.*?) \((.*?)\)$', links.text)
        city_name = m.group(1)
        count = m.group(2)
        printKitchensInCity(state_name, state_url, state_count, listing_url,city_name,count)


with open('kitchens.csv', 'wb') as csvfile:
    headers = ['State','State URL','State count','City','City URL','City Count','Index in City','Kitchen Name','Listing URL','Street Address','City and State','Phone Number','Kitchen Website']
    kitchen_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
    kitchen_writer.writerow(headers)
    for k in kitchens_records:
        row = [k.state_name,k.state_url,k.state_count,k.city_name,k.city_listing_url,k.city_record_count,k.number,k.name,k.url,k.street_address,k.city_state,k.phone_number,k.website]
        # print row
        kitchen_writer.writerow([s.encode('utf8') if type(s) is unicode else s for s in row])