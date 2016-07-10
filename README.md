**This is the project for the sell or exchange Instructions**

**
Installing mysql**

* pip install mysqlclient

**
Installing moneyd**

* pip install py-moneyed django-money

**
Installing summernotes**

* pip install django-summernote


**Installing widget tweaks**

* pip install django-widget-tweaks

**
Installing PIL**

* sudo apt-get install libjpeg8-dev
* pip install pillow

**Node JS**

* Install node js
* Go to sell_or_exchange and type 
```
#!shell script

npm install

```

**Configurations**

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

**Database**

* database is mysql
* create a empty database 'sell_or_exchange' 

```
#!properties

user name = root
password = admin
```


if you have different database name , then need to change the my.cnf accordingly