import requests

session = requests.Session()

session.headers.update({
    "Content-Type": "application/json",
})
#should we be hiding this?
api_key = "E9Y2LxT4g1hQZ7aD8nR3mWx5P0qK6pV7"

apiUrl = f"http://127.0.0.1:8001/api/v2/{api_key}/"


def get_all_desks():
    url = apiUrl + "desks/"
    response = session.get(url)
    return response.json()

def get_desk_by_id(id):
    url = apiUrl + "desks/" + id
    response = session.get(url)
    return response.json()

def get_desk_category(id, category):
    url = apiUrl + "desks/" + id + "/" + category
    response = session.get(url)
    return response.json()

def update_desk_category(id, category, jsonValue):
    url = apiUrl + "desks/" + id + "/" + category 

    response = session.put(url,json=jsonValue)

    return response.json()


def update_desk_height(id, value):
    #checks
    return update_desk_category(id,"state", {'position_mm': value})

