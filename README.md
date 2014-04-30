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

For instance :

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

### test_sites run

Setup a site, run its test units, dump its database and tear it down.

~~~bash
./test_sites run wordpress
~~~

This is equivalent to :

~~~bash
./test_sites test wordpress
./test_sites stop wordpress
./test_sites dump wordpress
./test_sites down wordpress
~~~

...

### test_sites test

...

~~~bash
./test_sites test wordpress
~~~

...


### test_sites up

Create the site's database and setup its `run` directory :

~~~bash
./test_sites up wordpress
~~~

...

### test_sites start

Start the builtin PHP server :

~~~bash
./test_sites start wordpress
~~~

...

### test_sites stop

Stop the builtin PHP server :

~~~bash
./test_sites stop wordpress
~~~

...

### test_sites dump

Dump the database to a compressed archive named `mysql.zip`in the site's `out` folder.

~~~bash
./test_sites dump wordpress
~~~

If the site's `run` folder is a git repository, saves the ouput of `git status` to `out/git_status`.

### test_sites down

Teardown the site :

~~~bash
./test_sites down wordpress
~~~

...

