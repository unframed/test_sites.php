test_sites.php
===
[![Build Status](https://travis-ci.org/unframed/test_sites.php.svg?branch=master)](https://travis-ci.org/unframed/test_sites.php)

Continuously test acceptance of PHP/MySQL sites.

Synopsis
---
Create a the `test/sites` and `test/units` directories.

You can specify the MySQL `root` user's password and the test MySQL user name by adding a `test_sites.json` configuration file in the directory `priv`.

For instance :

~~~json
{
    "mysqlRootPass": "password",
    "mysqlTestUser": "test"
}
~~~

For each site, create a directory in `test/sites` and add a  `test_sites.json` configuration file in it.

This project includes a WordPress sample site in `test/sites/wordpress` :

~~~json
{
    "httpHost": "127.0.0.1:8089",
    "gitSource": "deps/wordpress",
    "gitBranch": "3.8.3",
    "testUnits": [
        "wp_install.js"
        ]
}
~~~

This site will: use a shared repository found in `deps/wordpress` to checkout branch `3.8.3` as the `run` directory; be served by a PHP built-in server listening on `127.0.0.1:8089`; and the script `test/units/wp_install.js` will be executed by Casperjs when testing the site.

### Run

Setup a site, start its server, run its test units, stop the server, dump its database and tear down the site.

~~~bash
./test_sites run wordpress
~~~

Use this command for continuous integration.

### Test

Setup a site and start its server if not allready up, run its test units.

~~~bash
./test_sites test wordpress
~~~

Use this command if you want to test a site repeatedly or inspect its files and database afterwards.

### Up

Create the site's database, if the file exists decompress and import `mysql.zip` into that new database, create a `run` directory, check out a branch of a shared git repository if specified in the configuration, if it exists decompress the content of `run.zip` :

~~~bash
./test_sites up wordpress
~~~

Use this command if you want to inspect a site before testing it.

### Start

Start the builtin PHP server. For instance, to restart the `wordpress` site :

~~~bash
./test_sites start wordpress
~~~

Returns an error if the site is already running or has not been setup.

### Stop

Stop the builtin PHP server :

~~~bash
./test_sites stop wordpress
~~~

Returns an error if the site is not running.

### Dump

Dump the compressd database in `out/mysql.zip`, compress the new or updated files in in `out/run.zip`.

~~~bash
./test_sites dump wordpress
~~~

Use this command to dump a site's state for further testing.

### Down

Teardown the site :

~~~bash
./test_sites down wordpress
~~~

...

