#!/usr/bin/env python3

import unicodedata
from time import time
import sys
import urllib
from bs4 import BeautifulSoup
import json
import string
import os
import requests
from urllib.parse import urlencode
import shutil

global thumb
##############AREA_TO_SCRAPE################
# This is the are that you'd like to scrape
# i.e 'popular', 'latest', '<username>'
############################################
AREA_TO_SCRAPE = 'corkscore'
NUMBER_OF_PAGES = 1

###
DEBUG = True
HYPEM_URL = 'https://hypem.com/{}'.format(AREA_TO_SCRAPE)



validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def removeDisallowedFilenameChars(filename):
    if DEBUG:
      print("+ Attempting to sanitze text: '{}'".format(filename))
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    if DEBUG:
      print("+ Cleaned file name: {}".format(cleanedFilename))
    return ''.join(c for c in cleanedFilename.decode() if c in validFilenameChars)


class HypeScraper:

  def __init__(self):
    pass

  def start(self):
    print("--------STARTING DOWNLOAD--------")
    print("\tURL : {} ".format(HYPEM_URL))
    print("\tPAGES: {}".format(NUMBER_OF_PAGES))

    my_range = range(1, NUMBER_OF_PAGES + 1)
    #my_range.reverse()
    for i in my_range:

      print("PARSING PAGE: {}".format(i))

      page_url = HYPEM_URL + "/{}".format(i)
      html, cookie = self.get_html_file(page_url)

      if DEBUG:
        html_file = open("hypeHTML.html", "w")
        html_file.write(html)
        html_file.close()

      tracks = self.parse_html(html)

      print("\tPARSED {} SONGS".format(len(tracks)))

      self.download_songs(tracks, cookie)


  def get_html_file(self, url):
    data = {'ax':1 ,
              'ts': time()
          }
    data_encoded = urlencode(data)
    complete_url = url + "?{}".format(data_encoded)
    if DEBUG:
      print("Url to get: {}".format(complete_url))
    res = requests.get(complete_url)

    cookie = res.headers['Set-Cookie']
    html = res.text
    return html, cookie

  def parse_html(self, html):
    track_list = []
    soup = BeautifulSoup(html)
    html_tracks = soup.find(id="displayList-data")

    if html_tracks is None:
      return track_list
    try:
      track_list = json.loads(html_tracks.text)
      if DEBUG:
        print(json.dumps(track_list, sort_keys=True,indent=4, separators=(',', ': ')))
      return track_list[u'tracks']
    except ValueError:
      print("Hypemachine contained invalid JSON.")
      return track_list

  #tracks = id, title, artist, key
  def download_songs(self, tracks, cookie):

    print("\tDOWNLOADING SONGS...")
    for track in tracks:

      key = track[u"key"]
      id = track[u"id"]
      artist = removeDisallowedFilenameChars(track[u"artist"])
      title = removeDisallowedFilenameChars(track[u"song"])
      #thumb = thumb_urls[id]
      type = track[u"type"]

      print("\tFETCHING SONG....")
      if DEBUG:
        print(id)
      print(u"\t{} by {}".format(title, artist))

      if type is False:
        print("\tSKIPPING SONG SINCE NO LONGER AVAILABLE...")
        continue

      try:
        serve_url = "https://hypem.com/serve/source/{}/{}".format(id, key)
        if DEBUG:
          print(" + Serve URL: {}".format(serve_url))
        response = requests.get(
          serve_url, headers={
            'Content-Type': 'application/json',
            'cookie': cookie
        })

        song_data_json = response.text
        song_data = json.loads(song_data_json)
        url = song_data[u"url"]
        if DEBUG:
          print(" + GET to song URL: {}".format(url))
        download_response = requests.get(url, stream=True)

        filename = "{} - {}.mp3".format(artist, title)
        if os.path.exists(filename):
          print("File already exists")

        else:
          with open(filename, "wb") as mp3_song_file:
            shutil.copyfileobj(download_response.raw, mp3_song_file)
          del response
          #mp3_song_file = open(filename, "wb")
          #mp3_song_file.write(download_response.read() )
          mp3_song_file.close()

      except Exception as e:
            print('generic exception: ' + str(e))

def main():
  scraper = HypeScraper()
  scraper.start()

if __name__ == "__main__":
    main()
