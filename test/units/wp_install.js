/**
 * Setup and install WordPress.
 */
var casper = require("casper").create(),
	test_sites_name = casper.cli.options["name"],
	test_sites_host = casper.cli.options["host"],
	test_sites_mysqluser = casper.cli.options["mysqluser"],
	test_sites_root = 'http://'+test_sites_host;

function wp_admin_setup_config () {
    this.fillSelectors('form', {
        'input[name="dbname"]': test_sites_name,
        'input[name="uname"]': test_sites_mysqluser,
        'input[name="pwd"]': 'dummy',
        'input[name="dbhost"]': 'localhost',
        'input[name="prefix"]': 'wp_'
    }, true);
}

function wp_admin_install () {
    this.fillSelectors('form#setup', {
        'input#weblog_title': test_sites_name,
        'input#user_login': 'admin',
        'input#pass1': 'dummy',
        'input#pass2': 'dummy',
        'input#admin_email': 'staff@mailpoet.com',
        'input[name="blog_public"]': false
    }, true);
}

casper.start(
	test_sites_root+'/wp-admin/setup-config.php?step=1', 
	wp_admin_setup_config
	);
casper.thenOpen(
	test_sites_root+'/wp-admin/install.php',
	wp_admin_install
	);
casper.run(function() {
    this.echo(this.getCurrentUrl()).exit();
});
