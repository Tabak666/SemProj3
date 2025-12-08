git clone https://github.com/Tabak666/SemProj3.git
cd tableapp

pip install django-livereload-server 
pip install livereload  
pip install django-extensions  

python manage.py runserver

docker build -t tablemanager .
docker run -p 8000:8000 tablemanager
