import os

from jinja2 import Environment
from jinja2 import FileSystemLoader
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from db_settings import Announcement, Comment, Session


class BBoard:
    def __init__(self, session):
        self.session = session
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=True,
        )
        self.url_map = Map(
            [
                Rule("/", endpoint="index"),
                Rule("/add-announcement/", endpoint="add_announcement"),
                Rule("/<int:id_>/", endpoint="announcement"),
                Rule("/delete/<int:id_>/", endpoint="delete"),
            ],
        )

    def render_template(self, template_name, **context):
        template = self.jinja_env.get_template(template_name)
        return Response(template.render(context), mimetype="text/html")

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, f"on_{endpoint}")(request, **values)
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def on_index(self, request):
        announcements = self.session.query(Announcement).all()[::-1]
        context = {"announcements": announcements}
        return self.render_template("index.html", **context)

    def on_delete(self, request, id_):
        announcement = self.session.query(Announcement).get(id_)
        if announcement:
            self.session.delete(announcement)
            self.session.commit()
            self.session.close()
        return redirect("/")

    def on_add_announcement(self, request):
        if request.method == "POST":
            new_announcement = Announcement(
                author=f"{request.values['author']}",
                title=f"{request.values['title']}",
                text=f"{request.values['text']}",
            )
            self.session.add(new_announcement)
            self.session.commit()
            self.session.close()
            return redirect("/")
        return self.render_template("add_announcement.html")

    def on_announcement(self, request, id_):
        if request.method == "POST":
            new_comment = Comment(
                author=f"{request.values['author']}",
                text=f"{request.values['text']}",
                announcement_id=id_,
            )
            self.session.add(new_comment)
            self.session.commit()
            self.session.close()
            return redirect(f"/{id_}/")
        announcement = (
            self.session.query(Announcement).filter_by(id=id_).first()
        )
        if not announcement:
            return redirect("/")
        comments = announcement.comments[::-1]
        context = {"announcement": announcement, "comments": comments}
        return self.render_template("announcement.html", **context)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


# if __name__ == "__main__":
#     from werkzeug.serving import run_simple
#
#     run_simple(
#         "127.0.0.1",
#         5000,
#         BBoard(Session()),
#         use_debugger=True,
#         use_reloader=True,
#     )
def application(environ, start_response):
    app = BBoard(Session())
    return app(environ, start_response)
