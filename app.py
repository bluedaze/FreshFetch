import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from views import app
from apiRequests import send_request
import logging

logging.basicConfig(level=logging.INFO, format='%(lineno)d:\n %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.info("Starting")

if __name__ == "__main__":
    send_request()
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(send_request, "interval", minutes=60)
    sched.start()
    atexit.register(lambda: sched.shutdown())
    app.run(debug=True, use_reloader=False)