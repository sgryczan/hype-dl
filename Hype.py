import unicodedata
from time import time
import sys
import urllib2
import urllib
from time import time
from bs4 import BeautifulSoup
import json
import string
import os
import eyed3

global thumb
##############AREA_TO_SCRAPE################
# This is the are that you'd like to scrape
# i.e 'popular', 'latest', '<username>'
############################################
AREA_TO_SCRAPE = 'corkscore'
NUMBER_OF_PAGES = 1

###
DEBUG = False
HYPEM_URL = 'http://hypem.com/{}'.format(AREA_TO_SCRAPE)



validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def removeDisallowedFilenameChars(filename):
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)


class HypeScraper:

  def __init__(self):
    pass

  def start(self):
    print "--------STARTING DOWNLOAD--------"
    print "\tURL : {} ".format(HYPEM_URL)
    print "\tPAGES: {}".format(NUMBER_OF_PAGES)

    my_range = range(1, NUMBER_OF_PAGES + 1)
    #my_range.reverse()
    #for i in range(1, NUMBER_OF_PAGES + 1):
    for i in my_range:

      print "PARSING PAGE: {}".format(i)

      page_url = HYPEM_URL + "/{}".format(i)
      html, cookie = self.get_html_file(page_url)

      if DEBUG:
        html_file = open("hypeHTML.html", "w")
        html_file.write(html)
        html_file.close()

      tracks = self.parse_html(html)

      print "\tPARSED {} SONGS".format(len(tracks) )

      self.download_songs(tracks, cookie)


  def get_html_file(self, url):
    data = {'ax':1 ,
              'ts': time()
          }
    data_encoded = urllib.urlencode(data)
    complete_url = url + "?{}".format(data_encoded)
    request = urllib2.Request(complete_url)
    response = urllib2.urlopen(request)
    #save our cookie
    cookie = response.headers.get('Set-Cookie')
    #grab the HTML
    html = response.read()
    response.close()
    return html, cookie

  def parse_html(self, html):
    track_list = []
    soup = BeautifulSoup(html)
    html_tracks = soup.find(id="displayList-data")

##################THUMBNAILING##########

    # URL for the thumbnail file is in the style tag:

    # thumbnails[0].attrs['style']
    # thumb_url = thumbnails[0].attrs['style'].split("(")[1].split(")")[0]

    # href tag contains the track ID also, lets make a hashtable where key = id, value=url
    # thumbs[0].attrs['href']
    #>>> thumbs[0].attrs['href'].split("/")
    #[u'', u'track', u'2ege4', u'GRiZ+-+A+Fine+Way+To+Die+%28GRiZ+Remix%29']
    #>>> thumbs[0].attrs['href'].split("/")[2]

    #Parse Thumbnail info
    thumbnails = soup.find(id="track-list").find_all(class_="thumb")
#    print thumbnails
    #Create a global dictionary where id -> url
    global thumb_urls
    thumb_urls = {}
    print len(thumbnails)
    for i in range(0,20):
        thumb_id = thumbnails[i].attrs['href'].split("/")[2]
        thumb_url = thumbnails[i].attrs['style'].split("(")[1].split(")")[0]
        thumb_urls[thumb_id] = thumb_url
        if DEBUG:
          print thumb_id, thumb_url
          print len(thumb_urls)

############################################

    if html_tracks is None:
      return track_list
    try:
      track_list = json.loads(html_tracks.text)
      if DEBUG:
        print json.dumps(track_list, sort_keys=True,indent=4, separators=(',', ': '))
      return track_list[u'tracks']
    except ValueError:
      print "Hypemachine contained invalid JSON."
      return track_list

  #tracks = id, title, artist, key
  def download_songs(self, tracks, cookie):

    print "\tDOWNLOADING SONGS..."
    for track in tracks:

      key = track[u"key"]
      id = track[u"id"]
      artist = removeDisallowedFilenameChars(track[u"artist"])
      title = removeDisallowedFilenameChars(track[u"song"])
      thumb = thumb_urls[id]
      type = track[u"type"]

      print "\tFETCHING SONG...."
      if DEBUG:
        print id
      print u"\t{} by {}".format(title, artist)

      if type is False:
        print "\tSKIPPING SONG SINCE NO LONGER AVAILABLE..."
        continue

      try:
        serve_url = "http://hypem.com/serve/source/{}/{}".format(id, key)
        request = urllib2.Request(serve_url, "" , {'Content-Type': 'application/json'})
        request.add_header('cookie', cookie)
        response = urllib2.urlopen(request)
        song_data_json = response.read()
        response.close()
        song_data = json.loads(song_data_json)
        url = song_data[u"url"]

        download_response = urllib2.urlopen(url)
        filename = "{} - {}.mp3".format(artist, title)
        if os.path.exists(filename):
          print("File already exists , checking for a tag...")

          if has_id3_tag(filename):
            print("File already has a tag.")
          else:
            print("File has no tag, adding one...")
            add_id3_tag(filename, artist, title, thumb)

        else:
          mp3_song_file = open(filename, "wb")
          mp3_song_file.write(download_response.read() )
          mp3_song_file.close()

          add_id3_tag(filename, artist, title, thumb)

      except urllib2.HTTPError, e:
            print 'HTTPError = ' + str(e.code) + " trying hypem download url."
      except urllib2.URLError, e:
            print 'URLError = ' + str(e.reason)  + " trying hypem download url."
      except Exception, e:
            print 'generic exception: ' + str(e)

def add_id3_tag(filename, artist, title, thumb):
          mp3 = eyed3.load(filename)
          mp3.initTag()
          mp3.tag.artist = u"{}".format(artist)
          mp3.tag.title = u"{}".format(title)
          mp3.tag.album = u'HypeMachine'
          mp3.tag.setTextFrame('TCMP',u'1')
          #TODO: Add thumbnail file
          imageData = None
          imageType = eyed3.id3.frames.ImageFrame.FRONT_COVER
          mp3.tag.images.set(imageType, imageData, 'image/jpeg', description=u"Hype", img_url=thumb)
          mp3.tag.save()

def has_id3_tag(filename):
          mp3 = eyed3.load(filename)
          if mp3.tag:
              return True
          else:
              return False

def main():
  scraper = HypeScraper()
  scraper.start()

if __name__ == "__main__":
    main()
