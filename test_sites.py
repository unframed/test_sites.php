import os, json, subprocess, MySQLdb, re

# PHP lookalikes 

def file_exists(filename):
    return os.path.exists(filename)

def shell_exec(command):
    return subprocess.check_output(command, shell=True)

# configuration

if file_exists('priv/test_sites.json'):
    CONFIG = json.loads(open('priv/test_sites.json').read())
else:
    CONFIG = {}

# functions: Units (than can be tested simply)

def mysql_create (name, user, password):
    db = MySQLdb.connect(
        host = "localhost", 
        user = "root", 
        passwd = CONFIG.get(u'mysqlRootPass', u'')
        )
    db.cursor().execute( 
        "DROP DATABASE IF EXISTS {0} ;\n".format(name)
        )
    db.cursor().execute( 
        "CREATE DATABASE {0} ;\n"
        "GRANT ALL PRIVILEGES ON {0}.* TO "
        "{1}@localhost IDENTIFIED BY '{2}' ;\n"
        "FLUSH PRIVILEGES ;\n"
        .format(name, user, password)
        )

def mysql_import (path, user, password, name, host):
    return shell_exec(
        'unzip -p {0}/mysql.zip'
        ' | sed s,127.0.0.1:80,{4},g'
        ' | mysql -u {1} --password="{2}" {3}'
        .format(path, user, password, name, host)
        )

def mysql_dump (path, user, password, name, host):
    return shell_exec(
        'mysqldump -u {1} -p{2} {3}'
        ' | sed s,{4},127.0.0.1:80,g'
        ' | zip {0}/out/mysql.zip - '
        .format(path, user, password, name, host)
        )

def git_checkout (path, source, branch):
    return shell_exec(
        'git clone --shared --no-checkout {0} {1}/run ;'
        ' cd {1}/run ;'
        ' git checkout -q {2}'
        .format(source, path, branch)
        )

def git_add_untracked (path):
    status = shell_exec('cd {0}/run; git status -s'.format(path))
    for untracked in re.findall(r"[?]{2} (.+?)\n", status):
        shell_exec('cd {0}/run; git add {1}'.format(path, untracked))

def git_add_updated (path):
    status = shell_exec('cd {0}/run; git status -s'.format(path))
    for updated in re.findall(r"(?:A|M)  (.+?)\n", status):
        shell_exec('cd {0}/run; git add {1}'.format(path, updated))

def git_commit (path):
    status = shell_exec('cd {0}/run; git status -s'.format(path))
    if status:
        shell_exec('cd {0}/run; git commit -m "setup"'.format(path))

def run_dump (path):
    git_add_untracked(path)
    status = shell_exec('cd {0}/run; git status -s'.format(path))
    for updated in re.findall(r"(?:A|M)  (.+?)\n", status):
        shell_exec('cd {0}; zip out/run.zip run/{1}'.format(path, updated))

def run_teardown (path):
    shell_exec('rm {0}/run -rf'.format(path))
    return True

def server_start (path, host):
    return subprocess.Popen(['php', '-S', host, '-t', path + '/run']).pid

def server_stop (pid):
    os.kill(pid, 9)
    return True

# API

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
        return mysql_create(
            self.name, 
            self.getMySQLUser(), 
            'dummy'
            )

    def mysqlImport (self):
        return mysql_import(
            self.path, self.getMySQLUser(), 'dummy', self.name, self.getHttpHost()
            )

    def mysqlDump (self):
        return mysql_dump(
            self.path, self.getMySQLUser(), 'dummy', self.name, self.getHttpHost()
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
            git_checkout(
                self.path, 
                self.options['gitSource'], 
                self.options.get('gitBranch', 'HEAD')
                )
        else:
            os.mkdir(self.path+'/run')
            shell_exec('cd {0}/run; git init')
        if file_exists(self.path+'/run.zip'):
            shell_exec('cd {0}; unzip run.zip'.format(self.path))
        git_add_untracked(site.path)
        git_add_updated(site.path)
        git_commit(site.path)

    def runTeardown (self):
        return shell_exec('rm {0}/run -rf'.format(self.path))

    def getHttpHost (self):
        return self.options.get(u'httpHost', u'localhost:8089')

    def phpServerStart (self):
        pid = server_start(self.path, self.getHttpHost())
        if pid:
            open(site.path+'/pid', 'w').write('{0}'.format(pid))
            return True

        return False

    def phpServerStop (self):
        pid_file = self.path+'/pid'
        if file_exists(pid_file):
            server_stop(int(open(pid_file).read()))
            os.unlink(pid_file)
            return True

        return False

# commands

def error (message):
    print ("! "+message+"\r\n")

def help ():
    print ("see: https://github.com/unframed/test_sites.php\n")

def exists (argv):
    if not len(argv) > 2:
        error('missing site name')
        exit(1)

    elif not file_exists('test/sites/'+argv[2]):
        error('site does not exist')
        exit(2)

    else:
        return argv[2];

def up (site):
    run_dir = site.path+'/run'
    if file_exists(run_dir):
        error('site is already up')
        exit(3)

    site.mysqlSetup()
    site.runSetup()

def start (site):
    if file_exists(site.path+'/pid'):
        error('site may be running, cannot start')
        exit(6)

    if not file_exists(site.path+'/run'):
        error('site is down, cannot start')
        exit(7)

    if not site.phpServerStart():
        error('could not fork a PHP server')
        exit(8)

def stop (site):
    if not file_exists(site.path+'/run'):
        error('site is down, cannot stop')
        exit(9)

    pid_file = site.path+'/pid';
    if not file_exists(pid_file):
        error('site has already stopped')
        exit(10)

    site.phpServerStop()

def dump (site):
    out_dir = site.path + '/out'
    if file_exists(out_dir):
        shell_exec('rm {0}/out -rf'.format(site.path))
    os.mkdir(out_dir)
    site.mysqlDump()
    run_dump(site.path)

def down (site):
    if not file_exists(site.path+'/run'):
        error('site is already down')
        exit(5)

    pid_file = site.path+'/pid'
    if file_exists(pid_file):
        server_stop(int(open(pid_file).read()))
        os.unlink(pid_file)
    run_teardown(site.path)

def test (site):
    run_dir = site.path+'/run'
    if not file_exists(run_dir):
        up(site)
    if not file_exists(site.path+'/pid'):
        start(site)
    units = site.options.get(u'testUnits', [])
    for script in units:
        if script.endswith('.js'):
            shell_exec(
                'deps/casperjs/bin/casperjs test/units/{0} --name={1} --host={2} --mysqluser={3}'
                .format(script, site.name, site.getHttpHost(), site.getMySQLUser())
                )
        else:
            shell_exec(script)

def run (site):
    test(site)
    stop(site)
    dump(site)
    down(site)

def unknown (site):
    error('unknwon command')
    exit(11)

COMMANDS = {
    'up': up,
    'start': start,
    'stop': stop,
    'test': test,
    'dump': dump,
    'down': down,
    'run': run,
    'help': help 
}

if __name__ == '__main__':
    import sys
    if not len(sys.argv) > 1:
        error('missing command')
        exit(12)

    command = sys.argv[1]
    site = TestSite(exists(sys.argv))
    COMMANDS.get(command, unknown)(site)
    exit(0);
