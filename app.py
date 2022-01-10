import functools

from flask import Flask, Response, request, abort, redirect
import boto3


app = Flask("seancoates")
app.url_map.strict_slashes = False

s3 = boto3.client("s3")
BUCKET = "seancoates-site-content"

REDIRECT_HOSTS = ["www.seancoates.com"]


def fetch_from_s3(path):
    k = f"output/{path}"
    obj = s3.get_object(Bucket=BUCKET, Key=k)
    return obj["Body"].read()


def wrapped_s3(path, content_type="text/html; charset=utf-8"):
    if request.headers.get("Host") in REDIRECT_HOSTS:
        return redirect("https://seancoates.com/")

    try:
        data = fetch_from_s3(path)
        return Response(data, headers={"Content-Type": content_type}, status=200,)
    except s3.exceptions.NoSuchKey:
        abort(404)


def check_slash(handler):
    @functools.wraps(handler)
    def slash_wrapper(*args, **kwargs):
        path = request.path
        if path[-1] == "/":
            return redirect(path[0:-1])
        return handler(*args, **kwargs)

    return slash_wrapper


@app.route("/")
def index():
    return wrapped_s3("index.html")


@app.route("/assets/css/<filename>")
def assets_css(filename):
    return wrapped_s3(f"assets/css/{filename}", "text/css")


@app.route("/blogs/<slug>")
@check_slash
def blogs_slug(slug):
    return wrapped_s3(f"blogs/{slug}/index.html")


@app.route("/brews")
@app.route("/shares")
@app.route("/is")
@check_slash
def pages():
    return wrapped_s3(f"{request.path.lstrip('/')}/index.html")


@app.route("/archive")
@app.route("/blogs")
def no_page():
    return redirect("/")


@app.route("/archive/<archive_page>")
@app.route("/archive/<archive_page>/index.html")
@check_slash
def archive(archive_page):
    return wrapped_s3(f"archive/{archive_page}/index.html")


@app.route("/rss.xml")
def rss():
    return wrapped_s3("rss.xml", "application/xml")


@app.route("/assets/xml/rss.xsl")
def rss_xsl():
    return wrapped_s3("assets/xml/rss.xsl", "application/xml")


@app.route("/feed.atom")
def atom():
    return wrapped_s3("feed.atom", "application/atom+xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
