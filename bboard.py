"""A simple URL shortener using Werkzeug and redis."""
import os

from jinja2 import Environment
from jinja2 import FileSystemLoader
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from db_settings import Announcement, Comment, Session


session = Session()


class BBoard(object):
    def __init__(self):
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path), autoescape=True
        )
        self.url_map = Map(
            [
                Rule("/", endpoint="index"),
                Rule("/add-announcement/", endpoint="add_announcement"),
                Rule("/announcement/<int:id_>/", endpoint="announcement"),
            ]
        )

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype="text/html")

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, f"on_{endpoint}")(request, **values)
        except NotFound:
            return self.error_404()
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def on_index(self, request):
        context = {"announcements": session.query(Announcement).all()}
        return self.render_template("index.html", **context)

    def on_add_announcement(self, request):
        if request.method == "POST":
            new_announcement = Announcement(
                author=f"{request.values['author']}",
                title=f"{request.values['title']}",
                text=f"{request.values['text']}",
            )
            session.add(new_announcement)
            session.commit()
        context = {}
        return self.render_template("add_announcement.html", **context)

    def on_announcement(self, request, id_):
        print(id_)
        announcement = session.query(Announcement).filter_by(id=id_).first()
        context = {
            "announcement": announcement,
        }
        return self.render_template("announcement.html", **context)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def application(environ, start_response):
    app = BBoard()
    return app(environ, start_response)


if __name__ == "__main__":
    from werkzeug.serving import run_simple

    # run_simple("127.0.0.1", 5000, BBoard(), use_debugger=True, use_reloader=True)
