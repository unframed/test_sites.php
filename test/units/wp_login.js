/**
 * login WordPress with user name 'admin' and password 'dummy'.
 */
var casper = require("casper").create(),
	test_sites_name = casper.cli.options["name"],
	test_sites_host = casper.cli.options["host"],
	test_sites_mysqluser = casper.cli.options["mysqluser"],
	test_sites_root = 'http://'+test_sites_host;

function wp_login (username, password) {
    return function () {
        this.fillSelectors('form#loginform', {
            'input#user_login': username,
            'input#user_pass': password
        }, true);
    }
}

casper.start(
    test_sites_root+'/wp-login.php', 
    wp_login('admin', 'dummy')
    );

casper.run(function() {
    this.echo(this.getCurrentUrl()).exit();
});
