import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import os.path
import pymongo


from tornado.options import define, options
define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/recommended/", RecommendedHandler),
            (r"/discussion/", DiscussionHandler),
            (r"/add", BookEditHandler),
            (r"/edit/([0-9Xx\-]+)", BookEditHandler),
            (r"/delete/", BookDeleteHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Book": BookModule},
            debug=True,
        )
        conn = pymongo.Connection("localhost", 27017)
        self.db = conn["bookstore"]
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "index.html",
            page_title="Alice's Books | Home Page",
            header_text="Welcome to Alice's Books!",
        )


class RecommendedHandler(tornado.web.RequestHandler):
    def get(self):
        coll = self.application.db.books
        books = coll.find()
        self.render(
            "recommended.html",
            page_title="Alice's Books | Recommended Reading",
            header_text="Recommended Reading",
            books=books
        )


class BookModule(tornado.web.UIModule):
    def render(self, book):
        return self.render_string(
            "modules/book.html",
            book=book,
        )

    def css_files(self):
        return "/static/css/recommended.css"

    def javascript_files(self):
        return "/static/js/recommended.js"


class DiscussionHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "discussion.html",
            page_title="Alice's Books | Discussion",
            header_text="Talkin' About Books With Alice",
            comments=[
                {
                    "user": "Alice",
                    "text": "I can't wait for the next version of Programming Collective Intelligence!"
                },
                {
                    "user": "Burt",
                    "text": "We can't either, Alice.  In the meantime, be sure to check out RESTful Web Services too."
                },
                {
                    "user": "Melvin",
                    "text": "Totally hacked ur site lulz <script src=\"http://melvins-web-sploits.com/evil_sploit.js\"></script><script>alert('RUNNING EVIL H4CKS AND SPL0ITS NOW...');</script>"
                }
            ]
        )


class BookEditHandler(tornado.web.RequestHandler):
    INPUTS = [("isbn", "ISBN"), ("title", "Title"), ("subtitle", "Subtitle"), ("image", "Image"),
    ("author", "Author"), ("date_released", "Date released")]

    def getValue(self, book, k):
        print book, k
        return book.get(k, "")

    def get(self, isbn=None):
        book = dict()
        if isbn:
            coll = self.application.db.books
            book = coll.find_one({"isbn": isbn})
        self.render(
            "book_edit.html",
            page_title="Alice's Books",
            header_text="Edit book",
            book=book,
            inputs = self.INPUTS,
            getValue = self.getValue)

    def post(self, isbn=None):
        import time
        book_fields = [
            'isbn', 'title', 'subtitle', 'image', 'author',
            'date_released', 'description'
        ]
        coll = self.application.db.books
        book = dict()
        if isbn:
            book = coll.find_one({"isbn": isbn})
        for key in book_fields:
            book[key] = self.get_argument(key, None)

        print book, "================"
        if isbn:
            coll.save(book)
        else:
            book['date_added'] = int(time.time())
            coll.insert(book)
        self.redirect("/recommended/")


class BookDeleteHandler(tornado.web.RequestHandler):
    def get(self):
        coll = self.application.db.books
        books = coll.find()
        self.render(
            "book_delete.html",
            page_title="Alice's Books",
            header_text="All books",
            delete_path="/delete/",
            books=books)

    def post(self):
        isbn = self.get_argument("isbn")
        coll = self.application.db.books
        coll.remove({"isbn": isbn})
        self.redirect("/delete/")

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()