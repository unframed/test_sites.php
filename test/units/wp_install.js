/**
 * Setup and install WordPress.
 */

casper.test.begin('Install WordPress', 2, function suite (test) {
    var test_sites_name = casper.cli.options["name"],
        test_sites_host = casper.cli.options["host"],
        test_sites_mysqluser = casper.cli.options["mysqluser"],
        test_sites_root = 'http://'+test_sites_host;
    // test_sites_out = 'test/sites/'+test_sites_name+'/out/'
    casper.start();
    casper.wait(1000);
    /*
    casper.thenOpen(test_sites_root+'/wp-admin/setup-config.php?step=1', function () {
        // this.capture(test_sites_out+'wp_config_form.png');
        test.assertHttpStatus(200, 'GET '+this.getCurrentUrl());
        test.assertExists('form');
        test.assertExists('input[name="dbname"]');
        test.assertExists('input[name="uname"]');
        test.assertExists('input[name="pwd"]');
        test.assertExists('input[name="dbhost"]');
        test.assertExists('input[name="prefix"]');
    });
    casper.then(function () {
        this.fillSelectors('form', {
            'input[name="dbname"]': test_sites_name,
            'input[name="uname"]': test_sites_mysqluser,
            'input[name="pwd"]': 'dummy',
            'input[name="dbhost"]': 'localhost',
            'input[name="prefix"]': 'wp_'
        }, true);
    });
    */
    casper.thenOpen(test_sites_root+'/wp-admin/setup-config.php?step=2', {
        'method': 'post',
        'data': {
            'dbname': test_sites_name,
            'uname': test_sites_mysqluser,
            'pwd': 'dummy',
            'dbhost': 'localhost',
            'prefix': 'wp_'
        }
    }, function () {
        test.assertHttpStatus(200, 'POST '+this.getCurrentUrl());
    });
    /*
    casper.then(function () {
        // this.capture(test_sites_out+'wp_config_response.png');
        test.assertHttpStatus(200, 'POST '+this.getCurrentUrl());
    });
    casper.thenOpen(test_sites_root+'/wp-admin/install.php', function () {
        // this.capture(test_sites_out+'wp_install_form.png');
        test.assertHttpStatus(200, 'GET '+this.getCurrentUrl());
        test.assertExists('form#setup');
        test.assertExists('input#weblog_title');
        test.assertExists('input#user_login');
        test.assertExists('input#pass1');
        test.assertExists('input#pass2');
        test.assertExists('input#admin_email');
        test.assertExists('input[name="blog_public"]');
    });
    casper.then(function () {
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
    */
    casper.thenOpen(test_sites_root+'/wp-admin/install.php?step=2', {
        'method': 'post',
        'data': {
            'weblog_title': test_sites_name,
            'user_name': test_sites_mysqluser,
            'admin_password': 'dummy',
            'admin_password2': 'dummy',
            'admin_email': 'staff@mailpoet.com',
            'blog_public': '0'
        }
    }, function () {
        test.assertHttpStatus(200, 'POST '+this.getCurrentUrl());
    });
    casper.run(function () {
        this.test.done();
    });
});