/**
 * login WordPress with user name 'admin' and password 'dummy'.
 */

casper.test.begin('Login as admin', 5, function suite (test) {
    var test_sites_name = casper.cli.options["name"],
        test_sites_host = casper.cli.options["host"],
        test_sites_mysqluser = casper.cli.options["mysqluser"],
        test_sites_root = 'http://'+test_sites_host;
    casper.start();
    casper.wait(1000);
    casper.thenOpen(test_sites_root+'/wp-login.php', function () {
        test.assertHttpStatus(200, this.getCurrentUrl());
    });
    casper.then(function () {
        test.assertExists('form#loginform');
        test.assertExists('input#user_login');
        test.assertExists('input#user_pass');
        this.fillSelectors('form#loginform', {
            'input#user_login': 'admin',
            'input#user_pass': 'dummy'
        }, true);
    });
    casper.then(function(){
        test.assertHttpStatus(200, this.getCurrentUrl());
    });
    casper.run(function () {
        this.test.done();
    });
});