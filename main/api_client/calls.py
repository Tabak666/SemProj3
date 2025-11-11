import requests
import models
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
    return models.Desk.from_dict(response.json(),id)

def get_desk_category(id, category):
    url = apiUrl + "desks/" + id + "/" + category
    response = session.get(url)
    return response.json()

def update_desk_category(id, category, jsonValue):
    url = apiUrl + "desks/" + id + "/" + category 

    response = session.put(url,json=jsonValue)

    return response.json()
def loadDesks():
    deskList = []
    deskIDS = get_all_desks()
    for id in deskIDS:
        deskList.append(get_desk_by_id(id))
    
    return deskList


def update_desk_height(id, value):
    #checks
    return update_desk_category(id,"state", {'position_mm': value*10})

allDeskData:[models.Desk]= loadDesks()


for desk in allDeskData:
    print(desk.state.position_mm)
# update_desk_height('ee:62:5b:b8:73:1d',0)
#max height 132cm
#min height 

# print(get_all_desks())

print(get_desk_by_id("00:ec:eb:50:c2:c8"))

