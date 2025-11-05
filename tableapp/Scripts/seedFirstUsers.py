from main.models import Users
def run():
    User = Users(first_name="Kristian", last_name="Solovic", username="djzub", password = "megakokot", gender="M", height=186, activity_level = 3, role = "user", table_id=None)
    User.save()
    adminUser = Users(first_name="Kristian", last_name="Solovic", username="kamen04", password = "megakokot", gender="M", height=186, activity_level = 3, role = "admin", table_id=None)
    adminUser.save()
