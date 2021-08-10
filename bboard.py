import os

from jinja2 import Environment
from jinja2 import FileSystemLoader
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from db_settings import Announcement, Comment, Session, connect_db


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
        self.session.close()
        return self.render_template("index.html", **context)

    def on_delete(self, request, id_):
        announcement = self.session.query(Announcement).get(id_)
        if announcement:
            self.session.delete(announcement)
            self.session.commit()
        self.session.close()
        return redirect("/")

    def _announcement_is_valid(self, values):
        try:
            author = str(values["author"]).strip()
            title = str(values["title"]).strip()
            text = str(values["text"]).strip()
            author_len = len(author)
            title_len = len(title)
            text_len = len(text)
            is_valid = (
                author_len >= 1
                and author_len <= 100
                and title_len >= 1
                and title_len <= 100
                and text_len >= 1
                and text_len <= 1000
            )
            if is_valid:
                return {"author": author, "title": title, "text": text}
        except:
            pass
        return False

    def on_add_announcement(self, request):
        if request.method == "POST":
            announcement = self._announcement_is_valid(request.values)
            if announcement:
                new_announcement = Announcement(
                    author=f"{announcement['author']}",
                    title=f"{announcement['title']}",
                    text=f"{announcement['text']}",
                )
                self.session.add(new_announcement)
                self.session.commit()
                self.session.close()
                return redirect("/")
            context = {"error": "Validation error! Try again."}
        return self.render_template("add_announcement.html", **context)

    def _comment_is_valid(self, values, announcement_id):
        announcement = (
            self.session.query(Announcement)
            .filter_by(id=announcement_id)
            .first()
        )
        if not announcement:
            self.session.close()
            return False
        try:
            author = str(values["author"]).strip()
            text = str(values["text"]).strip()
            author_len = len(author)
            text_len = len(text)
            is_valid = (
                author_len >= 1
                and author_len <= 100
                and text_len >= 1
                and text_len <= 200
            )
            if is_valid:
                self.session.close()
                return {"author": author, "text": text, "id": announcement_id}
        except:
            pass
        self.session.close()
        return False

    def on_announcement(self, request, id_):
        context = {}
        if request.method == "POST":
            comment = self._comment_is_valid(request.values, id_)
            if comment:
                new_comment = Comment(
                    author=f"{comment['author']}",
                    text=f"{comment['text']}",
                    announcement_id=f"{comment['id']}",
                )
                self.session.add(new_comment)
                self.session.commit()
                self.session.close()
                return redirect(f"/{id_}/")
            context["error"] = "Validation error! Try again."
        announcement = (
            self.session.query(Announcement).filter_by(id=id_).first()
        )
        if not announcement:
            self.session.close()
            return redirect("/")
        comments = announcement.comments[::-1]
        context["announcement"] = announcement
        context["comments"] = comments
        self.session.close()
        return self.render_template("announcement.html", **context)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def application(environ, start_response):
    app = BBoard(Session())
    return app(environ, start_response)


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
