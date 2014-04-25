test: ugly
	php src/test_sites.php run wordpress

ugly: pull

DEPS = \
	deps \
	deps/wordpress \
	deps/test-more-php \
	deps/casperjs

pull: ${DEPS}
	cd deps/wordpress && git pull origin
	cd deps/casperjs && git pull origin

deps:
	mkdir deps

deps/wordpress:
	git clone \
		https://github.com/WordPress/WordPress.git \
		deps/wordpress

deps/test-more-php:
	svn checkout http://test-more-php.googlecode.com/svn/trunk/ deps/test-more-php

deps/casperjs:
	git clone git@github.com:n1k0/casperjs.git deps/casperjs

clean:
	rm deps/* -rf
	rm test/sites/*/run -rf
	rm test/sites/*/out -rf

install:
	sudo apt-get install \
		wget git php5 python \
		mysql-client php5-mysql mysql-server \
		# nodejs npm phantomjs
	sudo mysql_secure_installation
	sudo npm install uglify-js -g
