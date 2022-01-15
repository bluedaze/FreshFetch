import pickle
# The pickle stuff is pretty useful for rapid prototyping
# if you don't want to go through the effort of setting up
# a database.

# It's also useful for debugging when you don't want to make
# tons of requests to the API.

# Debug variable.
# "save" to go fetch data from the api
# "load" to use a pickle that you already have
class Debugger():
    def __init__(self, status):
        self.status = status

    def save_pickle(self, response):
        with open("stored_object.pickle", "wb") as file_to_store:
            pickle.dump(response, file_to_store)

    def load_pickle(self):
        with open("stored_object.pickle", "rb") as file_to_read:
            return pickle.load(file_to_read)