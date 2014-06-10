test_sites.php
===
[![Build Status](https://travis-ci.org/unframed/test_sites.php.svg?branch=master)](https://travis-ci.org/unframed/test_sites.php)

Continuously test acceptance of PHP/MySQL sites.

Synopsis
---
Specify the MySQL `root` user's password and the test MySQL user name by adding a `test_sites.json` configuration file in the directory `priv`.

When no `priv/test_sites.json` configuration file exist the defaults are :

~~~json
{
    "mysqlRootPass": "",
    "mysqlTestUser": "test"
}
~~~

### Status

To get the test sites status :

~~~bash
./lamp
~~~

### Init

Create a `test/sites/mysite` directory with a `test_sites.json` default configuration once :

~~~bash
./lamp init mysite
~~~

Note that there is a WordPress extension for `lamp` called `press` that takes care of the particularities of WordPress beyond PHP/MySQL.

~~~bash
./press
~~~

You can cook your own extension and maybe address Drupal's or Joomla specifics by looking in `test_press.py` how to extend `test_sites.py`. 

This project includes a WordPress sample site in `test/sites/wordpress` :

~~~json
{
    "httpHost": "127.0.0.1:8089",
    "gitSource": "deps/wordpress",
    "gitBranch": "3.9",
    "testUnits": [
        "wp_install.js"
        ]
}
~~~

With this configuration the site will: use a shared repository found in `deps/wordpress` to checkout branch `3.9` as its `run` directory; which will be served by a PHP built-in server listening on `127.0.0.1:8089`; and the script `test/units/wp_install.js` will be executed by Casperjs when testing the site.

### Run

Setup a site, start its server, run its test units, stop the server, dump its full database and its test site's `run` repository changes to zip archives and finally tear down the site.

~~~bash
./press run wordpress
~~~

Use this command for continuous integration.

### Test

Setup a site and start its server if not allready up, run its test units.

~~~bash
./press test wordpress
~~~

Use this command if you want to test a site repeatedly or inspect its files and database afterwards.

### Dump

Dump the compressed database in `out/mysql.zip`, compress the new or updated files in in `out/run.zip`.

~~~bash
./press test wordpress
./press dump wordpress
~~~

Use this command to dump a site's state for further testing

### Step

Test a site and merge its input and output into a new site  

~~~bash
./press test wordpress
./press dump wordpress
./press step wordpress wp39-installed
~~~

Use this command to build one or more test cases step by step.

### Up

Create the site's database, if the file exists decompress and import `mysql.zip` into that new database, create a `run` directory, check out a branch of a shared git repository if specified in the configuration, if it exists decompress the content of `run.zip` :

~~~bash
./press up wordpress
~~~

Use this command if you want to inspect a site before testing it.

### Start

Start the builtin PHP server. For instance, to restart the `wordpress` site :

~~~bash
./press start wordpress
~~~

Returns an error if the site is already running or has not been setup.

### Stop

Stop the builtin PHP server :

~~~bash
./press stop wordpress
~~~

Returns an error if the site is not running.

### Down

Teardown the site :

~~~bash
./press down wordpress
~~~

...
