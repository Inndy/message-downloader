from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore
import webapp2

import time
import logging
from lxml import etree
import sys

from dbmodel import dbUser, dbGroup, dbMessage

reload(sys)
sys.setdefaultencoding("utf-8")


class ParseHandler(blobstore_handlers.BlobstoreDownloadHandler):
    xpathContent = "//div[@class='contents']"
    xpathThread = ".//div[@class='thread']"
    xpathMessage = ".//div[@class='message']"
    xpathAuthor = ".//span[@class='user']//text()"
    xpathTime = ".//span[@class='meta']//text()"


    def post(self):
        blob_key = self.request.get('blob_key')
        url_str = self.request.get('user_key')
        logging.info("blob_key: {}, user_key: {}".format(blob_key, url_str))

        user_key = ndb.Key(urlsafe=url_str)
        # fetch the blob

        blob_reader = blobstore.BlobReader(blob_key)
        parser = etree.HTMLParser(encoding='UTF-8')
        root = etree.parse(blob_reader, parser)

        # process group
        content = root.xpath(self.xpathContent)[0]

        # start processing
        threads = content.xpath(self.xpathThread)
        processed = 0
        print("Process start")
        starttime = time.time()

        for thread in threads:
            print("Process: {}, progress {}/{}".format(thread.text, processed, len(threads)))
            group = dbGroup(
                user_key = user_key,
                group = thread.text)

            group_key = group.put()

            messages = thread.xpath(self.xpathMessage)
            for meta in messages:
                author = meta.xpath(self.xpathAuthor)[0]
                msgtime = meta.xpath(self.xpathTime)[0]
                text = meta.getnext().text

                # print("{} at {}: {}".format(author, time, text))

                msg = dbMessage(
                    group_key = group_key,
                    author = author,
                    time = msgtime,
                    content = text)
                msg.put()

            processed = processed + 1

        # update user info
        endtime = time.time()
        print("Process end, time consumed: {}".format(endtime-starttime))

        userdata = user_key.get()
        userdata.isReady = True
        userdata.put()


app = webapp2.WSGIApplication([
    ('/parse', ParseHandler)
    ], debug=True)

