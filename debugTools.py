import pickle
# The pickle stuff is pretty useful for rapid prototyping
# if you don't want to go through the effort of setting up
# a database.

# It's also useful for debugging when you don't want to make
# tons of requests to the API.

# Debug variable.
# "save" to go fetch data from the api
# "load" to use a pickle that you already have
def debug_status():
    status = "save"
    return status

def save_pickle(response):
    file_to_store = open("stored_object.pickle", "wb")
    pickle.dump(response, file_to_store)
    file_to_store.close()


def load_pickle():
    file_to_read = open("stored_object.pickle", "rb")
    response = pickle.load(file_to_read)
    file_to_read.close()
    return response