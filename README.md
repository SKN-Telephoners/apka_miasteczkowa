# 🍻 Apka Miasteczkowa

**Apka Miasteczkowa** is an app built by students, for students. We made it for anyone who lives, hangs out, or just visits the AGH Student Campus (Miasteczko Studenckie AGH).

Our main goal is to get people out of their dorm. Instead of mindless doom scrolling or chatting for hours, we want our users to step outside, meet up with friends, and actually experience the campus vibe.

### 🏕️ Why no chat? (The "Touch Grass" feature)
There are no direct messages (DMs) in our app - that’s on purpose. We don’t want to keep our users glued to their screens. Apka Miasteczkowa is just the starting point. 

### ✨ Key Features
* **Events are everything:** Any registered user can create an event and invite others.
* **Public & Private:**  The user can choose whether their event is pubic or private.
* **Map & Feed:** Trying to find your friends in the campus crowd? Check the map with event pins. Prefer a classic look? Scroll through the feed of upcoming events.
* **Filtering & Sorting:** Quickly find events that are of interest to you.
* **Quick Interactions:** Drop a comment, hit 'participate', and send invites to your friends.
* **Student Profile:** Set up your bio, uni, faculty, and year of study.

### 🚀 Status
Right now, we're adding finishing touhces and putting together our first working build. The next step is getting everything on a server and dropping the app on the **Google Play Store** so everyone can download it!

## 🛠️ Setting up
This guide will walk you through the installation and configuration of the development environment for the application.  

### Virtual Environment Setup
1. Install the package, create the enviroment and activate it:
``` bash
sudo apt install python3.12-venv
python3 -m venv apka_miasteczkowa
source apka_miasteczkowa/bin/activate
```
2. Install the project requirements: 
```bash
pip install -r requirements.txt
```

### .env file 
You need .env file for the app to run. This is the examle of one:
```bash
# .env file
DATABASE_URL = "postgresql://postgres:postgres@localhost/apka_miasteczkowa?sslmode=require"
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost/apka_miasteczkowa_test?sslmode=require"
JWT_SECRET_KEY = <your_jwt_key>
MAIL_SERVER = <your_mail_server>
MAIL_PORT = <your_port_for_mail>
MAIL_USERNAME = <your_mail_name>
MAIL_PASSWORD = <password_to_mail>
MAX_CONTENT_LENGTH = 16777216 # 16 MB
CLOUDINARY_URL = <cloudinary_url_for_photos>
TESTING = True
```
Your .env file needs to be in root directory.

### Running the Application
To run everything locally, you should open four separate WSL terminal window, 

**Window 1: Backend**
```bash
cd backend
flask run --host=0.0.0.0
```
**Window 2: Frontend**
```bash
sudo apt install npm  
cd frontend 
npm install expo   
npm audit fix      
npx expo start
```
**Window 3: Databases (PostgreSQL & Redis)**
```bash
sudo apt install postgresql postgresql-contrib   
sudo apt install redis-server
```
Start PostgreSQL and set up the default user password:
```bash
sudo service postgresql start   
sudo -u postgres psql   
\password *password*
\q
```
Update authentication methods:  

Find your PostgreSQL version folder, run ```cd /etc/postgresql``` followed by ```ls```. You should see exactly one folder.  
Edit the configuration file: ```sudo nano /etc/postgresql/{your_folder_number}/main/pg_hba.conf```  
Scroll down until you find the line ```local all postgres peer``` and change it to ```local all postgres md5```  
Save and exit the editor by pressing Ctrl+O then Ctrl+X

Restart services and test Redis:
```bash
sudo systemctl reload postgresql   
sudo systemctl start redis-server
```

Create the application databases:
```bash
sudo -i -u postgres   
createdb apka_miasteczkowa   
createdb apka_miasteczkowa_test   
exit
```

Import the schema *(Replace \<username> with your actual Linux username)*:
```bash
psql -U postgres -d apka_miasteczkowa -W /home/<username>/apka_miasteczkowa/schema.sql   
psql -U postgres -d apka_miasteczkowa_test -W /home/<username>/apka_miasteczkowa/schema.sql
```

**Window 4: Celery**   
Start the Celery worker:
```bash
celery -A backend.app.celery_app worker --loglevel=info
```

### Android Studio (Emulator)
Download the Android Studio [installer](https://developer.android.com/studio?hl=pl). The default installation settings are okay.  
Open the program. On the first screen, click: More options -> Device manager -> Phone -> Medium phone.  
Follow [this](https://expo.dev/go?sdkVersion=52&platform=android&device=false) quick tutorial to install the correct version of the Expo Go app on your emulator.  
Open the "Expo Go" app on your  emulator phone and enter the address that was generated in Window 2 (Frontend).