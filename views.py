from flask import render_template, redirect, url_for, request
import uuid
from psdb import *

def render_table():
    db = DB()
    response = db.query()
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

# # Circular imports issue
# # TODO: Fix this
# # Created a json api.
# def data_json():
#     request = RedditRequest()
#     response = ParseResponse(request.data)
#     response = {"albums": response.albums, "tracks": response.tracks}
#     if __name__ == "__main__":
#         pass
#     else:
#         return response