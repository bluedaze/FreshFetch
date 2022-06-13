from views import app
import os

os.getcwd()
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)