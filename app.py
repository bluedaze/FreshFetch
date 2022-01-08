import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import views
from apiRequests import send_request

app = Flask(__name__)
app.add_url_rule('/', view_func=views.render_table)
app.add_url_rule('/login', methods=['GET', 'POST'], view_func=views.login)

if __name__ == "__main__":
    send_request()
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(send_request, "interval", minutes=60)
    sched.start()
    atexit.register(lambda: sched.shutdown())
    app.run(debug=True, use_reloader=False)