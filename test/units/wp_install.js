/**
 * Setup and install WordPress.
 */

casper.test.begin('Install WordPress', 4, function suite (test) {
    test_sites_name = casper.cli.options["name"],
    test_sites_host = casper.cli.options["host"],
    test_sites_mysqluser = casper.cli.options["mysqluser"],
    test_sites_root = 'http://'+test_sites_host;
    // test_sites_out = 'test/sites/'+test_sites_name+'/out/'
    casper.start(test_sites_root+'/wp-admin/setup-config.php?step=1');
    casper.then(function () {
        // this.capture(test_sites_out+'wp_config_form.png');
        test.assertHttpStatus(200, 'GET '+this.getCurrentUrl());
        this.fillSelectors('form', {
            'input[name="dbname"]': test_sites_name,
            'input[name="uname"]': test_sites_mysqluser,
            'input[name="pwd"]': 'dummy',
            'input[name="dbhost"]': 'localhost',
            'input[name="prefix"]': 'wp_'
        }, true);
    });
    casper.then(function () {
        // this.capture(test_sites_out+'wp_config_response.png');
        test.assertHttpStatus(200, 'POST '+this.getCurrentUrl());
    });
    casper.thenOpen(test_sites_root+'/wp-admin/install.php', function () {
        // this.capture(test_sites_out+'wp_install_form.png');
        test.assertHttpStatus(200, 'GET '+this.getCurrentUrl());
        this.fillSelectors('form#setup', {
            'input#weblog_title': test_sites_name,
            'input#user_login': 'admin',
            'input#pass1': 'dummy',
            'input#pass2': 'dummy',
            'input#admin_email': 'staff@mailpoet.com',
            'input[name="blog_public"]': false
        }, true);
    });
    casper.then(function () {
        // this.capture(test_sites_out+'wp_install_response.png');
        test.assertHttpStatus(200, 'POST '+this.getCurrentUrl());
    });
    casper.run(function () {
        this.test.done();
    });
});