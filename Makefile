test: ugly
	./press step wordpress wp39installed
	./press run wp39installed

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
	rm deps/* -rf
	rm test/sites/*/run -rf
	rm test/sites/*/out -rf

install:
	sudo apt-get install \
		wget zipmerge git php5 python python-mysqldb \
		mysql-client php5-mysql mysql-server \
		# nodejs npm phantomjs
	sudo mysql_secure_installation
	sudo npm install uglify-js -g
