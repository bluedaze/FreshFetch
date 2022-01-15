from flask import render_template, redirect, url_for, request
import uuid
from psdb import *

def index():
    db = DB()
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

def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

# Circular imports issue
# TODO: Fix this
# Created a json api.
def data_json():
    db = DB()
    response = db.query()
    response = {"albums": response.albums, "tracks": response.tracks}
    if __name__ == "__main__":
        pass
    else:
        return response