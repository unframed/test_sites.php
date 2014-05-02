import os, json, subprocess, MySQLdb, re

# PHP lookalikes 

def file_exists(filename):
    return os.path.exists(filename)

def shell_exec(command):
    return subprocess.check_output(command, shell=True)

# project's private configuration

if file_exists('priv/test_sites.json'):
    _CONFIG = json.loads(open('priv/test_sites.json').read())
else:
    _CONFIG = {}

# functions: Units (than can be tested simply)

def mysql_create (name, user, password):
    db = MySQLdb.connect(
        host = "localhost", 
        user = "root", 
        passwd = _CONFIG.get(u'mysqlRootPass', u'')
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

def mysql_import (path, user, password, name, pipe='|'):
    return shell_exec(
        'unzip -p {0}/mysql.zip {4} mysql -u {1} --password="{2}" {3}'
        .format(path, user, password, name, pipe)
        )

def mysql_dump (path, user, password, name, pipe='|'):
    return shell_exec(
        'mysqldump -u {1} -p{2} {3} {4} zip {0}/out/mysql.zip - '
        .format(path, user, password, name, pipe)
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
    for updated in re.findall(r"(?:A |M | A| M) (.+?)\n", status):
        shell_exec('cd {0}/run; git add {1}'.format(path, updated))

def git_commit (path):
    status = shell_exec('cd {0}/run; git status -s'.format(path))
    if status:
        shell_exec('cd {0}/run; git commit -m "setup"'.format(path))

def run_dump (path):
    git_add_untracked(path)
    status = shell_exec('cd {0}/run; git status -s'.format(path))
    for updated in re.findall(r"(?:A |M | A| M) (.+?)\n", status):
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
            self.path, self.getMySQLUser(), 'dummy', self.name, 
            ' | sed s,TEST_SITES_HOST,{0},g | '.format(self.getHttpHost())
            )

    def mysqlDump (self):
        return mysql_dump(
            self.path, self.getMySQLUser(), 'dummy', self.name, 
            ' | sed s,{0},TEST_SITES_HOST,g | '.format(self.getHttpHost())
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
        git_add_untracked(self.path)
        git_add_updated(self.path)
        git_commit(self.path)

    def runTeardown (self):
        return shell_exec('rm {0}/run -rf'.format(self.path))

    def getHttpHost (self):
        return self.options.get(u'httpHost', u'localhost:8089')

    def phpServerStart (self):
        pid = server_start(self.path, self.getHttpHost())
        if pid:
            open(self.path+'/pid', 'w').write('{0}'.format(pid))
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

def error (code, message):
    print ("! "+message+"\r\n")
    exit (code)

def help ():
    print ("see: https://github.com/unframed/test_sites.php\n")

def exists (name):
    if not file_exists('test/sites/'+name):
        error(1, 'site does not exist')

    else:
        return name;

def up (site):
    run_dir = site.path+'/run'
    if file_exists(run_dir):
        error(2, 'site is already up')

    site.mysqlSetup()
    site.runSetup()

def start (site):
    if file_exists(site.path+'/pid'):
        error(3, 'site may be running, cannot start')

    if not file_exists(site.path+'/run'):
        error(4, 'site is down, cannot start')

    if not site.phpServerStart():
        error(5, 'could not fork a PHP server')

def stop (site):
    if not file_exists(site.path+'/run'):
        error(6, 'site is down, cannot stop')

    pid_file = site.path+'/pid';
    if not file_exists(pid_file):
        error(7, 'site has already stopped')

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
        error(8, 'site is already down')

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
    error(9, 'unknwon command')

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

def cli(factory):
    import sys
    if not len(sys.argv) > 1:
        error(10, 'missing command')

    if not len(sys.argv) > 2:
        error(11, 'missing site name')

    command = sys.argv[1]
    site = factory(exists(sys.argv[2]))
    COMMANDS.get(command, unknown)(site)
    sys.exit(0);

if __name__ == '__main__':
    cli(TestSite)
