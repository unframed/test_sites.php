import os, json, subprocess, MySQLdb

# PHP lookalikes 

def file_exists(filename):
    return os.path.exists(filename)

def shell_exec(command):
    return subprocess.check_output(command, shell=True)

# configuration

if file_exists('priv/test_sites.json'):
    TEST_SITES_CONFIG = json.loads(open('priv/test_sites.json').read())
else:
    TEST_SITES_CONFIG = {}

# functions

def test_sites_mysql_create (name, user, password):
    MySQLdb.connect(
        host = "localhost", 
        user = "root", 
        passwd = TEST_SITES_CONFIG.get(u'mysqlRootPass', u'')
        ).cursor().execute( 
        "DROP DATABASE IF EXISTS {0} ;\n"
        "CREATE DATABASE {0} ;\n"
        "GRANT ALL PRIVILEGES ON {0}.* TO "
        "{1}@localhost IDENTIFIED BY '{2}' ;\n"
        "FLUSH PRIVILEGES ;\n"
        .format(name, user, password)
        )

def test_sites_mysql_import (path, user, password, name):
    return shell_exec(
        'unzip -p {0} | mysql -u {1} --password="{2}" {3}'
        .format(path, user, password, name)
        )

def test_sites_mysql_dump (path, user, password, name):
    return shell_exec(
        'mysqldump -u {1} -p{2} {3} | zip {0}/out/mysql.zip - '
        .format(path, user, password, name)
        )

def test_sites_git_checkout (path, source, branch):
    return shell_exec(
        'git clone --shared --no-checkout {0} {1}/run ;'
        ' cd {1}/run ;'
        ' git checkout -q {2}'
        .format(source, path, branch)
        )

def test_sites_run_dump (path):
    if file_exists(path+'/run/.git'):
        return shell_exec(
            'cd {0}/run; git status > ../out/git_status_down'
            .format(path)
            )

def test_sites_run_teardown (path):
    return shell_exec('rm {0}/run -rf'.format(path))

def test_sites_server_start (path, host):
    return subprocess.Popen([
        '/usr/bin/php',
        '-S', host, 
        '-t', path + '/run'
        ]).pid

def test_sites_server_stop (pid):
    os.kill(pid, 9)
    return True

# OOP

class TestSite:

    def __init__(self, name):
        self.name = name
        self.path = 'test/sites/' + self.name
        self.options = {
            u"httpHost": u"127.0.0.1:8089",
            u"testUnits": []
        }
        config = self.path + '/test_sites.json'
        if file_exists(config):
            self.options.update(json.loads(open(config).read()))

    def getMySQLUser (self):
        return self.options.get('mysqlTestUser', 'test')

    def mysqlCreate (self):
        return test_sites_mysql_create(
            self.name, 
            self.getMySQLUser(), 
            'dummy'
            )

    def mysqlImport (self):
        return test_sites_mysql_import(
            self.path, self.getMySQLUser(), 'dummy', self.name
            )

    def mysqlDump (self):
        return test_sites_mysql_dump(
            self.path, self.getMySQLUser(), 'dummy', self.name
            )

    def mysqlSetup (self):
        self.mysqlCreate()
        if file_exists(self.path+'/mysql.zip'):
            self.mysqlImport()

    def runSetup(self):
        out_dir = self.path + '/out'
        if not file_exists(out_dir):
            os.mkdir(out_dir)
        if self.options.has_key('gitSource'):
            test_sites_git_checkout(
                self.path, 
                self.options['gitSource'], 
                self.options.get('gitBranch', 'HEAD')
                )
        else:
            os.mkdir(self.path+'/run')
        if file_exists(self.path+'/www'):
            shell_exec('cp -r {0}/www/* {0}/run'.format(self.path))
        if file_exists(self.path+'/run/.git'):
            shell_exec(
                'cd {0}/run; git status > ../out/git_status_up'
                .format(self.path)
                )

    def runTeardown (self):
        return shell_exec('rm {0}/run -rf'.format(self.path))

    def getHttpHost (self):
        return self.options.get(u'httpHost', u'localhost:8089')

    def phpServerStart (self):
        return test_sites_server_start(self.path, self.getHttpHost())

    def phpServerStop (self, pid):
        return test_sites_server_stop(pid)


# commands

def test_sites_error (message):
    print ("! "+message+"\r\n")

def test_sites_help ():
    print (
        "usage : \r\n"
        "\r\n"
        "\tphp test_sites.php (up|stop|start|test|dump|down|help) [name]\r\n"
        "\r\n"
        "\tphp test_sites.php run name\r\n"
        "\r\n"
        )

def test_sites_exists (argv):
    if not len(argv) > 2:
        test_sites_error('missing site name')
        exit(1)

    elif not file_exists('test/sites/'+argv[2]):
        test_sites_error('site does not exist')
        exit(2)

    else:
        return argv[2];

def test_sites_up (site):
    run_dir = site.path+'/run'
    if file_exists(run_dir):
        test_sites_error('site is already up')
        exit(3)

    site.mysqlSetup()
    site.runSetup()
    """
    pid = test_sites_server_start(site.path, site.getHttpHost())
    if pid == False:
        test_sites_error('could not fork a PHP server')
        exit(4);

    else:
        open(site.path+'/pid', 'w').write('{0}'.format(pid))
    """

def test_sites_start (site):
    if file_exists(site.path+'/pid'):
        test_sites_error('site is running, cannot start')
        exit(6)

    if not file_exists(site.path+'/run'):
        test_sites_error('site is down, cannot start')
        exit(7)

    pid = test_sites_server_start(site.path, site.getHttpHost())
    if (pid == False):
        test_sites_error('could not fork a PHP server')
        exit(8)

    else:
        open(site.path+'/pid', 'w').write('{0}'.format(pid))

def test_sites_stop (site):
    if not file_exists(site.path+'/run'):
        test_sites_error('site is down, cannot stop')
        exit(9)

    pid_file = site.path+'/pid';
    if not file_exists(pid_file):
        test_sites_error('site has already stopped')
        exit(10)

    test_sites_server_stop(int(open(pid_file).read()))
    os.unlink(pid_file)

def test_sites_dump (site):
    out_dir = site.path + '/out'
    if not file_exists(out_dir):
        os.mkdir(out_dir)
    site.mysqlDump()
    test_sites_run_dump(site.path)

def test_sites_down (site):
    if not file_exists(site.path+'/run'):
        test_sites_error('site is already down')
        exit(5)

    pid_file = site.path+'/pid'
    if file_exists(pid_file):
        test_sites_server_stop(int(open(pid_file).read()))
        os.unlink(pid_file)
    test_sites_run_teardown(site.path)

def test_sites_test (site):
    run_dir = site.path+'/run'
    if not file_exists(run_dir):
        test_sites_up(site)
    if not file_exists(site.path+'/pid'):
        test_sites_start(site)
    units = site.options.get(u'testUnits', [])
    for script in units:
        if script.endswith('.js'):
            shell_exec(
                'deps/casperjs/bin/casperjs test/units/{0} --name={1} --host={2} --mysqluser={3}'
                .format(script, site.name, site.getHttpHost(), site.getMySQLUser())
                )
        else:
            shell_exec(script)

def test_sites_run (site):
    test_sites_test(site)
    test_sites_stop(site)
    test_sites_dump(site)
    test_sites_down(site)

def test_sites_unknown (site):
    test_sites_error('unknwon command')
    exit(11)

test_sites_commands = {
    'up': test_sites_up,
    'start': test_sites_start,
    'stop': test_sites_stop,
    'test': test_sites_test,
    'dump': test_sites_dump,
    'down': test_sites_down,
    'run': test_sites_run,
    'help': test_sites_help 
}

if __name__ == '__main__':
    import sys
    if not len(sys.argv) > 1:
        test_sites_error('missing command')
        exit(12)

    command = sys.argv[1]
    site = TestSite(test_sites_exists(sys.argv))
    test_sites_commands.get(command, test_sites_unknown)(site)
    exit(0);
