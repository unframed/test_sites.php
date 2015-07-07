test: ugly
	#./press startup wordpress
	./press test wordpress
	./press stop wordpress
	#./press step wordpress wp39installed
	#./press startup wp39installed
	#./press test wp39installed
	#./press dump wp39installed
	#./press step wp39installed
	#./press up wp39nginx
	#./press startup wp39nginx
	#./press test wp39nginx
	#./press down wp39nginx
	./press startup wp39apache
	./press test wp39apache
	./press down wp39apache

ugly: pull
	uglifyjs test/units/wp_install.js --lint > /dev/null
	uglifyjs test/units/wp_login.js --lint > /dev/null

DEPS = \
	deps \
	deps/wordpress \
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

deps/casperjs:
	git clone https://github.com/n1k0/casperjs.git deps/casperjs

clean:
	rm -rf deps/*
	rm -rf test/sites/*/run
	rm -rf test/sites/*/out

install:
	sudo apt-get update
	sudo apt-get install \
		wget curl zip unzip zipmerge git python php5 \
		apache2 libapache2-mod-php5 \
		nginx php5-fpm php5-mysql \
		mysql-client mysql-server \
		nodejs npm phantomjs
	sudo mysql_secure_installation
	# curl --insecure https://www.npmjs.org/install.sh | sudo sh
	sudo npm install uglify-js -g
