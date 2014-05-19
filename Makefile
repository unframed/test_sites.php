test: ugly
	./press step wordpress wp39installed
	./press up wp39installed
	./press dump wp39installed
	./press step wp39installed
	./press down wp39installed
	./press run wp39installed
	# ./press run wp39nginx

ugly: pull
	uglifyjs test/units/wp_install.js --lint > /dev/null

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
	sudo apt-get install \
		wget curl zip unzip zipmerge git \
		python python-mysqldb \
		nginx php5 php5-fpm php5-mysql \
		mysql-client mysql-server \
		# wheezy-backports : nodejs nodejs-legacy
		# sid: nodejs npm phantomjs
	sudo mysql_secure_installation
	curl --insecure https://www.npmjs.org/install.sh | sudo sh
	sudo npm install uglify-js -g
