import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import views
from apiRequests import send_request
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.debug("Starting")
app = Flask(__name__)
app.add_url_rule('/', view_func=views.render_table)
app.add_url_rule('/newTable', view_func=views.render_new_table)
app.add_url_rule('/login', methods=['GET', 'POST'], view_func=views.login)

if __name__ == "__main__":
    send_request()
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(send_request, "interval", minutes=60)
    sched.start()
    atexit.register(lambda: sched.shutdown())
    app.run(debug=True, use_reloader=False)