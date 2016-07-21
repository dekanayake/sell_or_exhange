# This is the project for the sell or exchange Instructions #

## Installing python ##

We are using python 2.7


## Installing virtual environment ##

we are using python venv , so we can keep all the project dependencies in a single virtual machine.

### installing and using venv in ubuntu ###

sudo apt-get install virtualenv
pip install --user virtualenvwrapper
source venv/bin/activate

### installing and using venv in windows ###

Go to CMD and type

```
#!powershell

powershell –ExecutionPolicy Bypass
```

type 


```
#!powershell

Import-Module virtualenvwrapper
```


```
#!powershell

workon [venvname]
```


## Installing mysql ##

* pip install mysqlclient


## Installing moneyd ##

* pip install py-moneyed django-money

## Installing summernotes ##

* pip install django-summernote

## Installing widget tweaks ##

* pip install django-widget-tweaks


## Installing PIL ##

* sudo apt-get install libjpeg8-dev
* pip install pillow

## Node JS ##

* Install node js
* Go to sell_or_exchange and type 
```
#!shell script

npm install

```

## Configurations ##

* Need to apply following configurations to the settings.py


```
#!properties

MEDIA_ROOT='[Change to the physical folder of the media folder in your project]'
```



```
#!properties

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': '[Change to my.cnf physical location in project]',
        },
    }
}
```

* Change the my.cnf file to reflect the database

## Database ##

* database is mysql
* create a empty database 'sell_or_exchange' 

```
#!properties

user name = root
password = admin
```


if you have different database name , then need to change the my.cnf accordingly

## Setting up the system ##

* Go to the project base directory
* cd mysite
* type

```
#!shell script

python manage.py migrate
```

This will migrate all the database scripts

* Type

```
#!shell script

python manage.py runserver
```
# Intergrating  SOLR #

**Install and configuring SOLR**

Download SOLR from http://www.apache.org/dyn/closer.lua/lucene/solr/6.1.0 and unzip
**
Create SOLR core** 

Go to [SOLR BASE]/bin and tyoe ./solr create -c products

run solr instance by 
```
#!python

./solr start
```



**Installing rabbitmq**


```
#!python

sudo apt-get install rabbitmq
```

**Installing celery**


```
#!python

pip install celery
```

run 
```
#!python

celery -A mysite worker -l debug
```




**Installing haystack**

```
#!python


pip install haystack
```
**Installing celery haystack**

```
#!python


pip install celery-haystack

```

**
Creating the schema**

go to mysite base folder and type



```
#!python

 python manage.py build_solr_schema --filename=[SOLR base folder]/server/solr/product/conf/schema.xml && curl 'http://localhost:8983/solr/admin/cores?action=RELOAD&core=product&wt=json&indent=true'
```
**
how to delete documents in SOLR**

Run 

```
#!python


curl http://localhost:8983/solr/product/update?commit=true -H "Content-Type: text/xml" --data-binary '<delete><query>*:*</query></delete>'
```