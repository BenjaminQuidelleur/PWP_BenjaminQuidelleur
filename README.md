# PWP SPRING 2021
# In-Stadium API
# Group information
* Student 1. Benjamin Quidelleur email : bquidell20@student.oulu.fi
* Student 2. Djamel Ramzi Nasri email : dnasri20@student.oulu.fi
* Student 3. ///

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__




## Usage
# Installing dependencies
* (Install virtualenv) (virtualenv is not in requirements) (in case with problems on Windows, try first installing with): 
  python -m pip install virtualenv --user
* Activate python virtual environment in command line: 
  virtualenv pwp
* install dependencies: 
  pip install -r requirements.txt
* Run the API: 
  flask run
  
## Database population 
the method db_populate is included in both tests

## Database testing
go in the folder ORM
run pytest
the database is populated at the beginning of the test file.


## API Testing

API testing: stadium_test.py
