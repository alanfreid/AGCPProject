'''
Created on Mar 12, 2018

@author: alanf
'''
import webapp2
import urllib
import urllib2
import json
import time
import logging
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import mail

# Book defines the data model for the Books
# as it extends db.model the content of the class will automatically stored
class BookModel(db.Model):
    author       = db.UserProperty(required=True)
    shortDescription = db.StringProperty(required=True)
    longDescription  = db.StringProperty(multiline=True)
    url          = db.StringProperty()
    created          = db.DateTimeProperty(auto_now_add=True)
    updated      = db.DateTimeProperty(auto_now=True)
    dueDate          = db.StringProperty(required=True)
    finished         = db.BooleanProperty()

class Book(object):
    def __init__(self, data):
        self.__dict__ = json.loads(data)

# The main page where the user can login and logout
# MainPage is a subclass of webapp.RequestHandler and overwrites the get method
class FindBooks(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'

        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
# GQL is similar to SQL
#        books = BookModel.gql("WHERE author = :author and finished=false",
#               author=users.get_current_user())
#
        values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext
        }
        logging.warning('finished with main page')
        self.response.out.write(template.render('findbooks.html', values))

# This class creates a new Todo item
class ListBooks(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'

        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            
        author = self.request.get('authorName')
        logging.warning('author: ' + author)
        start = time.time()
        books, errors = GetGoogleBooksData(author)
        numberofbooks = len(books['items'])
        end = time.time()
        logging.warn("call took: " + str(end - start))
        
        values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'books': books,
            'numberofbooks': numberofbooks,
            'errors': errors
        }
        #logging.warn("help")
        self.response.out.write(template.render('listbooks.html', values))     
        

# This class creates a new Todo item
class New(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            testurl = self.request.get('url')
        if not testurl.startswith("http://") and testurl:
            testurl = "http://"+ testurl
            book = BookModel(
                author  = users.get_current_user(),
                shortDescription = self.request.get('shortDescription'),
                longDescription = self.request.get('longDescription'),
                dueDate = self.request.get('dueDate'),
                url = testurl,
        finished = False)
            book.put();

            self.redirect('/')

# This class deletes the selected Book
class Remove(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            raw_id = self.request.get('id')
            id = int(raw_id)
            todo = BookModel.get_by_id(id)
            todo.delete()
            self.redirect('/')


#This class emails the task to yourself
class Email(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            raw_id = self.request.get('id')
            id = int(raw_id)
            book = BookModel.get_by_id(id)
        message = mail.EmailMessage(sender=user.email(),
                            subject=book.shortDescription)
        message.to = user.email()
        message.body = book.longDescription
        message.send()
        self.redirect('/')

# Register the URL with the responsible classes
application = webapp2.WSGIApplication(
                                     [('/', FindBooks),
                                      ('/list', ListBooks)],
                                        debug=True)

# Register the wsgi application to run
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
    
COUNTRY = "US"
BOOK_LG = "en"
BOOK_FIELDS = (
  "items("
    "id"
    ",accessInfo(epub/isAvailable)"
    ",volumeInfo(title,subtitle,language,pageCount)"
  ")"
  )


def GetGoogleBooksData(author):
    books = []
    errors = None
    pageBookIdx = 0
    pageBookCnt = 40  # Default: 10, Max: 40

    while True:
    
    # Request paginated data from Google Books API
        url = (
            "https://www.googleapis.com/books/v1/volumes?"
            "q={}"
            "&startIndex={}"
            "&maxResults={}"
            "&country={}"
            "&langRestrict={}"
            "&download=epub"
            "&printType=books"
            "&showPreorders=false"
            "&fields={}"
            ).format(
                urllib.quote_plus('inauthor:"%s"' % (author)),
                pageBookIdx,
                pageBookCnt,
                COUNTRY,
                BOOK_LG,
                urllib.quote_plus(BOOK_FIELDS)
                )
        logging.warning('url:' + url)
    
        reqPageData = None
        try:
            jsonData = '{"name": "Frank", "age": 39}'
            jsonToPython = json.loads(jsonData)
            logging.warning(jsonToPython['name'])
            
            response = urllib2.urlopen(url)
            decoded_response = response.read().decode("UTF-8")
            books=json.loads(decoded_response)
            logging.warning(books['items'])
            for element in books['items']:
                logging.warning(element)
            
            #reqPageData = json.load(response)
            
            
        except urllib2.HTTPError, err:
            errors = err.read()
            print "HTTPError = ", str(err.code)
        except:
            print "Error when handling\n", url
    
        #if reqPageData is None:
        #    logging.warning('reqPageData is none')
        #   break

        #pageBookItems = reqPageData.get("items", None)
        #if pageBookItems is None:
        #   logging.warning('pageBookItems is none')
        #   break

        #books += pageBookItems
        #itemCnt = len(pageBookItems)
        #logging.warning('itemCnt: ' + str(itemCnt))
        #if itemCnt < pageBookCnt:
        # Do not issue another HTTP request
        #   break

        #pageBookIdx += pageBookCnt
        #print pageBookIdx
# Loop and request next page data

        return books, errors  
