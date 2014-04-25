<?php

if (file_exists('priv/test_sites_config.php')) {
    require_once('priv/test_sites_config.php'); // user defined
} else {
    define('TEST_SITES_MYSQL_ROOTPASS', ''); // Travis defined ,-)
}
if (!defined('TEST_SITES_MYSQL_TESTUSER')) {
    define('TEST_SITES_MYSQL_TESTUSER', 'test');
}

function test_sites_path ($name) {
    return 'test/sites/'.$name;
}

// Database Setup and Teardown

/**
 * Return a connection to MySQL with super user privileges, 
 * using the user name 'root' with password MP3_TEST_MYSQL_ROOTPASS.
 *
 * Throws an Exception if the connection failed.
 */
function test_sites_mysqli_root () {
    $mysqli = new mysqli("localhost", "root", TEST_SITES_MYSQL_ROOTPASS);
    if ($mysqli->connect_errno) {
        throw new Exception("Failed to connect to MySQL: ("
            .$mysqli->connect_errno
            .") ".$mysqli->connect_error);
    }
    return $mysqli;
}

/**
 * Return an array with the results of the `$sql` script sent to `$mysqli`
 * connection.
 *
 * Throws an Exception if the connection failed.
 */
function test_sites_mysqli_query ($mysqli, $sql) {
    if (!$mysqli->multi_query($sql)) {
        throw new Exception(
            "Multi query failed: (" . $mysqli->errno . ") " . $mysqli->error
            );
    }
    $result = array(); 
    do {
        if ($res = $mysqli->store_result()) {
            array_push($result, $res->fetch_all(MYSQLI_ASSOC));
            $res->free();
        }
    } while ($mysqli->more_results() && $mysqli->next_result());
    return $result;
}

/**
 * Execute the SQL script to create a database for test site `$name` and 
 * grant all privileges on it the the test use `mp3test@localhost`.
 */
function test_sites_mysqli_create ($name) {
    return test_sites_mysqli_query(
        test_sites_mysqli_root(), 
        "DROP DATABASE IF EXISTS ".$name." ;\n"
        ."CREATE DATABASE ".$name." ;\n"
        ."GRANT ALL PRIVILEGES ON ".$name.".* TO "
            .TEST_SITES_MYSQL_TESTUSER."@localhost IDENTIFIED BY 'dummy' ;\n"
        ."FLUSH PRIVILEGES ;\n"
        );
}

/**
 * Use the shell to import data for test site `$name`
 */
function test_sites_mysql_import ($name) {
    return shell_exec(
        'unzip -p '.test_sites_path($name).'/mysql.zip'
            .' | mysql -u '.TEST_SITES_MYSQL_TESTUSER
            .' --password="dummy" '.$name
        );
}

function test_sites_mysql_dump ($name) {
    $path = test_sites_path($name);
    return shell_exec(
        'mysqldump -u '.TEST_SITES_MYSQL_TESTUSER.' -pdummy '
        .$name.' | zip '.$path.'/out/mysql.zip - '
        );
}

// WWW Setup and Teardown

function test_sites_git_checkout ($name, $source, $branch) {
    $path = test_sites_path($name);
    return shell_exec(
        'git clone --shared --no-checkout '.$source.' '.$path.'/run ;'
        .' cd '.$path.'/run ;'
        .' git checkout -q '.$branch
        );
}

function test_sites_run_setup ($name) {
    $path = test_sites_path($name);
    if (!file_exists($path.'/out')) {
        mkdir($path.'/out');
    }
    if (defined('TEST_SITES_GIT_SOURCE')) {
        if (!defined('TEST_SITES_GIT_BRANCH')) {
            define('TEST_SITES_GIT_BRANCH', 'HEAD');
        }
        test_sites_git_checkout($name, TEST_SITES_GIT_SOURCE, TEST_SITES_GIT_BRANCH);
    } else {
        mkdir($path.'/run');
    }
    if (file_exists($path.'/www')) {
        shell_exec('cp -r '.$path.'/www/* '.$path.'/run');
    }
    if (file_exists($path.'/run/.git')) {
        shell_exec('cd '.$path.'/run; git status > ../out/git_status_up');
    }
    test_sites_mysqli_create($name);
    if (file_exists($path.'/mysql.zip')) {
        test_sites_mysql_import($name);
    }
}

function test_sites_run_dump ($name) {
    $out_dir = test_sites_path($name).'/out';
    if (!file_exists($out_dir)) {
        mkdir($out_dir);
    }
    return test_sites_mysql_dump ($name);
}

function test_sites_run_teardown ($name) {
    $path = test_sites_path($name);
    if (file_exists($path.'/run/.git')) {
        shell_exec('cd '.$path.'/run; git status > ../out/git_status_down');
    }
    return shell_exec('rm '.$path.'/run -rf');
}

// HTTP Start and Stop

/**
 * Start PHP builtin server for test sites `$name`, listen on `$host` name and port.
 *
 * Returns the PID of the forked process or false if the fork failed.
 *
 */
function test_sites_server_start ($name, $host) {
    $pid = pcntl_fork();
    if ( $pid == -1 ) {
        return false; // fork failed
    } else if ( $pid > 0 ) {
        return $pid; // fork succeeded, return the child PID
    } else {
        $args = array(
            '-S', $host, 
            '-t', test_sites_path($name).'/run'
            );
        pcntl_exec('/usr/bin/php', $args);
        // now the PHP built-in server has cloned the forked process ...
    }
}

/**
 * Stop the process identified by `$pid`.
 */
function test_sites_server_stop ($pid) {
    exec(sprintf('kill -9 %d', $pid));
    return true;
}

/**
 * Load the configuration for site `$name`
 */
function test_sites_configure($name) {
    $config = test_sites_path($name).'/test_sites_config.php';
    if (file_exists($config)) {
        include($config);
    }
}

// Commands: up, start, stop, down and run.

function test_sites_help () {
    echo (
        "usage : \r\n"
        ."\r\n"
        ."\tphp test_sites.php (up|start|stop|dump|down) name\r\n"
        ."\r\n"
        ."\tphp test_sites.php run name script\r\n"
        ."\r\n"
        );
}

function test_sites_error ($message) {
    echo ("! ".$message."\r\n");
}

function test_sites_exists ($name) {
    if (!isset($name)) {
        test_sites_error('missing site name');
        test_sites_help();
        exit(1);
    } elseif (!file_exists(test_sites_path($name))) {
        test_sites_error('site does not exist');
        exit(2);
    } else {
        return $name;
    }
}

function test_sites_up ($name) {
    $path = test_sites_path($name);
    $run_dir = $path.'/run';
    if (file_exists($run_dir)) {
        test_sites_error('site is already up');
        exit(3);
    }
    test_sites_configure($name);
    test_sites_run_setup($name);
    $pid = test_sites_server_start($name, TEST_SITES_HTTP_HOST);
    if ($pid === false) {
        test_sites_error('could not fork a PHP server');
        exit(4);
    } else {
        file_put_contents($path.'/pid', sprintf('%d',$pid));
    }
}

function test_sites_down ($name) {
    $path = test_sites_path($name);
    if (!file_exists($path.'/run')) {
        test_sites_error('site is already down');
        exit(5);
    }
    $pid_file = $path.'/pid';
    if (file_exists($pid_file)) {
        test_sites_server_stop((int) file_get_contents($pid_file));
        unlink($pid_file);
    }
    test_sites_run_teardown($name);
}

function test_sites_start ($name) {
    $path = test_sites_path($name);
    if (file_exists($path.'/pid')) {
        test_sites_error('site is running, cannot start');
        exit(6);
    }
    test_sites_configure($name);
    $pid = test_sites_server_start($name, TEST_SITES_HTTP_HOST);
    if ($pid === false) {
        test_sites_error('could not fork a PHP server');
        exit(7); 
    } else {
        file_put_contents($path.'/pid', sprintf('%d',$pid));
    }
}

function test_sites_stop ($name) {
    $path = test_sites_path($name);
    if (!file_exists($path.'/run')) {
        test_sites_error('site is down, cannot stop');
        exit(8);
    }
    $pid_file = $path.'/pid';
    if (!file_exists($pid_file)) {
        test_sites_error('site has already stopped');
        exit(9);
    }
    test_sites_server_stop((int) file_get_contents($pid_file));
    unlink($pid_file);
}

function test_sites_run ($name, $script) {
    if (!file_exists($script)) {
        test_sites_error('script does not exist');
        exit(10);
    }
    test_sites_up($name);
    if (substr($script, -4) === '.php') {
        include ($script);
    } elseif (substr($script, -3) === '.js') {
        shell_exec(
            'deps/casperjs/bin/casperjs '
            .'test/units/'.$script
            .' --name='.$name
            .' --host='.TEST_SITES_HTTP_HOST
            .' --mysqluser='.TEST_SITES_MYSQL_TESTUSER
            );
    } else {
        shell_exec($script);
    }
    test_sites_down($name);
}

// the script

define('TEST_SITES_NAME', test_sites_exists($argv[2]));
switch ($argv[1]) {
    case 'up': test_sites_up(TEST_SITES_NAME); break;
    case 'start': test_sites_start(TEST_SITES_NAME); break;
    case 'stop': test_sites_stop(TEST_SITES_NAME); break;
    case 'dump': test_sites_run_dump(TEST_SITES_NAME); break;
    case 'down': test_sites_down(TEST_SITES_NAME); break;
    case 'run': test_sites_run(TEST_SITES_NAME, $argv[3]); break;
    case 'help': test_sites_help(); break; 
    default:
        test_sites_error('unknown command '.$argv[1]);
        exit(11);
}
exit(0);
