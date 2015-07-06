/**
 * login WordPress with user name 'admin' and password 'dummy'.
 */

casper.test.begin('Login as admin', 2, function suite (test) {
    test_sites_name = casper.cli.options["name"],
    test_sites_host = casper.cli.options["host"],
    test_sites_mysqluser = casper.cli.options["mysqluser"],
    test_sites_root = 'http://'+test_sites_host;
    casper.start(test_sites_root+'/wp-login.php');
    casper.then(function () {
        test.assertHttpStatus(200, this.getCurrentUrl());
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