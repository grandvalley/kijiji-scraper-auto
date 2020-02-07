# -*- coding: utf-8 -*-
from dynamic.models import Car
from bs4 import BeautifulSoup
from django.db import models
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
from datetime import datetime
from pytz import timezone
import threading
from decimal import Decimal
import time


class Scraper(object):
  def __init__(self, d):
    self.now_dt = datetime.now(timezone('EST')).replace(tzinfo=None)
    self.stop_flag = False
    self.terr_name = next(iter(d))
    self.loc_id = d.get(next(iter(d)))

  special_keywords = {
    'accident': {'weight': 6,'keywords':['accident free', 'accident-free', 'no accident', 'clean history', 'clean record']},
    'warranty': {'weight': 1, 'keywords':['warranty']},
    'mileage': {'weight': 6, 'keywords':['low mileage', 'low km']},
    'rust': {'weight': 6, 'keywords':['zero rust', 'no rust', 'rust free']},
    'maintained': {'weight': 1, 'keywords':['well maintained', 'maintained']},
    'owner': {'weight': 4, 'keywords':['one owner', 'single owner']},
    'driven': {'weight': 4, 'keywords':['lady driven', 'senior driven', 'lady', 'senior']},
    'highway': {'weight': 2, 'keywords': ['highway driven', 'highway']},
    'condition': {'weight': 2, 'keywords':['mint condition', 'great condition', 'good condition', 'amazing condition']},
    'runs': {'weight': 2, 'keywords':['runs like new', 'like new']},
    'engine': {'weight': 2, 'keywords':['no engine light', 'no check engine']},
    'certified': {'weight': 6, 'keywords':['certified']},
    'emission': {'weight': 6, 'keywords':['e-tested', 'emission tested']},
    'negotiable': {'weight': 6, 'keywords': ['obo', 'o.b.o', 'or best offer', 'negotiable', 'is negotiable', 'negotiable']}
  }

  @property
  def payload(self):
    return {
      'formSubmit': 'true',
      'adIdRemoved': '',
      'adPriceType': '',
      'brand': '',
      'carproofOnly': 'false',
      'categoryId': 27,
      'categoryName': 'Buy+&+Sell',
      'cpoOnly': 'false',
      'dc': 'false',
      'gpTopAd': 'false',
      'highlightOnly': 'false',
      'll': '',
      'locationId': int(self.loc_id),
      'minPrice': '',
      'maxPrice': '',
      'origin': '',
      'pageNumber': 2,
      'searchView': 'LIST',
      'sortByName': 'dateDesc',
      'userId': '',
      'urgentOnly': 'false',
      'keywords': '',
      'SearchCategory': 27,
      'SearchSubmit': ''
    }

  def find_target_uri(self, links):
    res = list(filter(lambda x: "cars & trucks" in x.text.strip().lower(), links))
    return res[0] if res else None

  def get_response(self, url, **kwargs):
    content = None
    try:
      response = requests.get(url, **kwargs)
      if response.status_code == requests.codes.ok:
        content = response.content
        print response.history[0].url
    except:
      pass

    return content

  def render_listings(self, listings):
    for listing in listings:
      if 'regular-ad' not in listing.attrs['class']:
        continue

      listing_id = None
      try:
        listing_id = int(listing.attrs['data-ad-id'])
      except Exception as e:
        pass

      if not listing_id:
        continue

      image_html = listing.findAll("div", {"class": "image"})
      img_url = None
      if image_html:
        img_url = image_html[0].findNext('img')['src']

      info_tag = listing.findAll("div", {"class": "info"})[0]
      title_tag = info_tag.findAll('div', {"class": "title"})[0]
      a_tag = title_tag.findNext('a')
      car_link = 'https://www.kijiji.ca%s' % (a_tag['href'])

      content = self.get_response(car_link)
      if content:
        page_soup = BeautifulSoup(content, 'html.parser')
      else:
        self.stop_flag = True
        break

      description = None
      description_html = page_soup.select("div[class*=descriptionContainer]")
      if description_html:
        description = description_html[0].text

      item = {
        'year': None,
        'make': None,
        'model': None,
        'transmission': None,
        'drivetrain': None,
        'kilometers': None,
        'condition': None
      }

      AttributeList_html = page_soup.find('div', {"id": 'AttributeList'})
      if AttributeList_html:
        item_attrs = AttributeList_html.select("dl[class*=itemAttribute-]")
        if item_attrs:
          for ia in item_attrs:
            label_text = None
            value_text = None
            attributeLabel_html = ia.select("dt[class*=attributeLabel-]")
            if attributeLabel_html:
              label_text = attributeLabel_html[0].text
              if label_text:
                label_text = label_text.strip().lower()
            attributeValue_html = ia.select("dd[class*=attributeValue-]")
            if attributeValue_html:
              value_text = attributeValue_html[0].text
              if value_text:
                value_text = value_text.strip().lower()
            if (label_text and value_text) and (label_text in item):
              if label_text == 'kilometers':
                value_text = int(value_text.replace(',', ''))
                print value_text
              item.update({
                label_text: value_text
              })

      item_condition = item.get('condition', None)
      if item_condition and 'lease' in item_condition.strip().lower():
        continue

      address = None
      address_html = page_soup.select("span[class*=address-]")
      if address_html:
        address = address_html[0].text

      title = None
      title_html = page_soup.select("h1[class*=title-]")
      if title_html:
        title = title_html[0].text

      amount = None
      currentPrice_html = page_soup.select("span[class*=currentPrice-]")
      if currentPrice_html:
        price_span = currentPrice_html[0].findAll('span')
        if price_span:
          try:
            amount = int(str(price_span[0]['content']).replace(",", ""))
          except:
            pass
      weight = 0
      search_description = None
      if description:
        search_description = description.strip().lower()

      search_title = None
      if title:
        search_title = title.strip().lower()
      for k, v in self.__class__.special_keywords.iteritems():
        keywords = v.get('keywords')
        for keyword in keywords:
          if (search_description and keyword in search_description) or (search_title and keyword in search_title):
            weight += v.get('weight')
            break
      item.update({
        'image': '%s' % (img_url),
        'title': title,
        'description': description,
        'listing_id': listing_id,
        'link': car_link,
        'territory': self.terr_name,
        'weight': weight,
        'amount': amount,
        'address': address
      })
      q = Car.objects.filter(listing_id=listing_id)
      if q.exists():
        car = q.first()
        for attr, value in item.iteritems(): 
          setattr(car, attr, value)
        car.save()
      else:
        car = Car(**item)
        car.save()

  def start_script(self, page_link=None):
    if page_link is None:
      content = self.get_response('https://www.kijiji.ca/b-search.html', params=self.payload)
      if not content:
        raise Exception('Initial content not found')
      soup = BeautifulSoup(content, 'html.parser')
      srp_nav = soup.findAll("div", {"class": "srp-navigation"})
      if not srp_nav:
        raise Exception('SRP Navigation not found')
      links = srp_nav[0].findAll("li")
      if not links:
        raise Exception('Links not found')
      initial_uri = self.find_target_uri(links)
      if not initial_uri:
        raise Exception('Link not found')

      page_link = 'https://www.kijiji.ca%s' % (initial_uri)
    content = self.get_response(page_link)
    if not content:
      raise Exception('Initial content not found')

    soup = BeautifulSoup(content, 'html.parser')

    listings = soup.findAll("div", {"class": "search-item"})

    self.render_listings(listings)
    time.sleep(2)

    self.start_script(page_link=page_link)


locations_map = [
  {'Alberta': 9003},
  {'British Columbia': 9007},
  {'Manitoba': 9006},
  {'New Brunswick': 9005},
  {'Newfoundland and Labrador': 9008},
  {'Nova Scotia': 9002},
  {'Ontario': 9004},
  {'OntarioB': 100009004},
  {'Prince Edward Island': 9011},
  {'Quebec': 9001},
  {'Saskatchewan': 9009},
  {'Northwest Territories': 9010}
]


def main():
  threads = [threading.Thread(target=Scraper(d).start_script) for d in locations_map]

  for thread in threads:
    thread.start()

  for thread in threads:
    thread.join()
