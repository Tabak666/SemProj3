import requests
from core.api_client.models import Desk
# from models import Desk
session = requests.Session()
from time import sleep
session.headers.update({
    "Content-Type": "application/json",
})
#should we be hiding this?
api_key = "E9Y2LxT4g1hQZ7aD8nR3mWx5P0qK6pV7"

apiUrl = f"http://127.0.0.1:8001/api/v2/{api_key}/"

def test():
    print("jello")
def get_all_desks():
    url = apiUrl + "desks/"
    response = session.get(url)
    return response.json()

def get_desk_by_id(id):
    url = apiUrl + "desks/" + id
    response = session.get(url)
    return Desk.from_dict(response.json(),id)

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


def toggle_clean_mode():
    deskList  = loadDesks()
    if (sum([(desk.state.position_mm) for desk in deskList])/len(deskList)) < 1200:

        for desk in deskList:
            update_desk_height(desk.mac_address,132)
    else:
        for desk in deskList:
            update_desk_height(desk.mac_address,68)
        #block the simulator from randomly moving the desks 

def check_height_all():
    deskList = loadDesks()

    for desk in deskList:
        print(f"Desk id:{desk.mac_address} height: {desk.state.position_mm}")
# #min height 680mm
#max height 1320mm


