from flask import Flask, render_template, redirect, url_for, request
import uuid
import sys
sys.path.append("..")
from Refetcher.psdb import DB
from Refetcher.environment import get_env
app = Flask(__name__)


@app.route("/")
@app.route("/index")
def index():
    config = get_env()
    db = DB(config["db_password"])
    response = db.query()
    # The list of tracks is almost always larger than tracks
    # so we delete them so that the lists are the same size.
    # We find the absolute value between the two lists
    # then we delete that number from the end of the list.
    # We delete from the end of the list so the most popular
    # items are still displayed.
    difference =  abs(len(response["tracks"]) - len(response["albums"]))
    del response["tracks"][-difference:]
    return render_template(
        "base.html",
        videos=response["videos"],
        tracks=response["tracks"],
        albums=response["albums"],
        zip=zip,
        uuid=uuid,
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


def data_json():
    config = get_env()
    db = DB(config["db_password"])
    response = db.query()
    response = {"albums": response.albums, "tracks": response.tracks}
    if __name__ == "__main__":
        pass
    else:
        return response