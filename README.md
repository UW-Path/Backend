<img src="demo.png?raw=true"/>
</br>

<b>UWPath is a website that helps University of Waterloo students plan their future courses according to their majors/minors/specific courses/etc. <b/>


# Set Up#
Refer to requirements.txt for all the Python modules needed. Project is built with Python 3.8.

## Django ##
Make sure local database is setup under django_projects/settings.py under var DATABASES (Verify localhost, port, username password is correct)

open UWPathWebsite on cmd and run the following commands:

python manage.py makemigrations
python manage.py migrate

Run below command to start the webpage:
python manage.py runserver

To set up email notification: 
- Setup env variable for under variable name UWPath_Email_Account and UWPath_Email_Password


## Setting up with PyCharm: ##

Please initialize Django Server under add configuration with the following settings:  

Enviorment Variables: PYTHONUNBUFFERED=1;DJANGO_SETTINGS_MODULE=django_projects.settings

Check Run Browser: http://127.0.0.1:8000/

Python Interpreter: Project Default (Python)

