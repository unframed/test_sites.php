test_sites.php
===
Continuously test acceptance of PHP/MySQL sites.

Synopsis
---
Create a the `test/sites` and `test/units` directories, add a `test_sites.json` configuration file in the directory `priv` if it exists.

### test_sites add

If it does not exists, create a new `wordpress` directory in `test/sites` with a JSON configuration file named `test_sites.json`.

~~~bash
./test_sites add wordpress
~~~

...

~~~json
{
    "httpHost": "127.0.0.1:8089",
    "testUnits": []
}
~~~

...

### test_sites run

Setup a site, run its test units, dump its database and tear it down.

~~~bash
./test_sites run wordpress
~~~

This is equivalent to :

~~~bash
./test_sites up wordpress
./test_sites start wordpress
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

~~~bash
./test_sites up wordpress
./test_sites start wordpress
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

