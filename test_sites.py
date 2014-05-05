import sys, os, json, subprocess, MySQLdb, re

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
    return db.cursor().execute( 
        "CREATE DATABASE {0} ;\n"
        "GRANT ALL PRIVILEGES ON {0}.* TO "
        "{1}@localhost IDENTIFIED BY '{2}' ;\n"
        "FLUSH PRIVILEGES ;\n"
        .format(name, user, password)
        )

def mysql_drop (name, user, password):
    db = MySQLdb.connect(
        host = "localhost", 
        user = user, 
        passwd = password
        )
    return db.cursor().execute( 
        "DROP DATABASE IF EXISTS {0} ;\n".format(name)
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

    def __init__ (self, name):
        self.name = name
        self.path = 'test/sites/' + self.name
        self.options = {
            u"httpHost": u"127.0.0.1:8089",
            u"testUnits": []
        }
        config = self.path + '/test_sites.json'
        if file_exists(config):
            self.options.update(json.loads(open(config).read()))

    def init (self):
        os.mkdir(self.path)
        open(self.path+'/test_sites.json', 'w').write(
            json.dumps(self.options, indent=4, sort_keys=True)
            )

    def isUp (self):
        return file_exists(self.path+'/run')

    def getMySQLUser (self):
        return self.options.get('mysqlTestUser', 'test')

    def mysqlCreate (self):
        return mysql_create(
            self.name, 
            self.getMySQLUser(), 
            'dummy'
            )

    def mysqlImport (self):
        return mysql_import(self.path, self.getMySQLUser(), 'dummy', self.name)

    def mysqlSetup (self):
        self.mysqlCreate()
        if file_exists(self.path+'/mysql.zip'):
            self.mysqlImport()

    def runSetup (self):
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
            shell_exec('cd {0}/run; git init'.format(self.path))
        if file_exists(self.path+'/run.zip'):
            shell_exec('cd {0}; unzip run.zip'.format(self.path))
        git_add_untracked(self.path)
        git_add_updated(self.path)
        git_commit(self.path)

    def setup (self):
        self.mysqlSetup()
        self.runSetup()

    def dump (self):
        return (
            mysql_dump(self.path, self.getMySQLUser(), 'dummy', self.name),
            run_dump(self.path)
            )

    def teardown (self):
        return (
            run_teardown(self.path),
            mysql_drop(self.name, self.getMySQLUser(), 'dummy')
            )

    def getHttpHost (self):
        return self.options.get(u'httpHost', u'localhost:8089')

    def isRunning (self):
        return file_exists(self.path+'/pid')

    def httpServerStart (self):
        pid = server_start(self.path, self.getHttpHost())
        if pid:
            open(self.path+'/pid', 'w').write('{0}'.format(pid))
            return True

        return False

    def httpServerStop (self):
        pid_file = self.path+'/pid'
        if file_exists(pid_file):
            server_stop(int(open(pid_file).read()))
            os.unlink(pid_file)
            return True

        return False

    def testSuite (self):
        units = self.options.get(u'testUnits', [])
        for script in units:
            try:
                if script.endswith('.js'):
                    shell_exec(
                        'deps/casperjs/bin/casperjs'
                        ' test/units/{0} --name={1} --host={2} --mysqluser={3}'
                        .format(script, self.name, self.getHttpHost(), self.getMySQLUser())
                        )
                else:
                    shell_exec(script)
            except subprocess.CalledProcessError as e:
                return '{0} failed : {1}'.format(script, e.output)

    def hasOutput (self):
        out_dir = self.path+'/out'
        return file_exists(out_dir) and len(os.listdir(out_dir)) > 0

    def mergeOutput (self, basedir='.'):
        shell_exec(
            'cd {0} ; cp out/mysql.zip {1} ; zipmerge {1}/run.zip out/run.zip'
            .format(self.path, basedir)
            )

    def cleanOutput (self):
        out_dir = self.path + '/out'
        if file_exists(out_dir):
            shell_exec('rm {0} -rf'.format(out_dir))
        os.mkdir(out_dir)

    def getStatus (self):
        hasOutput = "O" if self.hasOutput() else " "
        if not self.isUp():
            return "_{0} {1}".format(hasOutput, self.name)
        elif not self.isRunning():
            return "U{0} {1}".format(hasOutput, self.name)
        else:
            return "R{0} {1} http://{2}/".format(hasOutput, self.name, self.getHttpHost())

# commands

def error (code, message):
    print ("! "+message+"\r\n")
    sys.exit(code)

def help ():
    print ("see: https://github.com/unframed/test_sites.php\n")

def exists (name):
    if not file_exists('test/sites/'+name):
        error(1, 'site {0} does not exist'.format(name))

    else:
        return name;

def up (site):
    if site.isUp():
        error(2, 'site is already up')

    site.setup()

def start (site):
    if site.isRunning():
        error(3, 'site may be running, cannot start')

    if not site.isUp():
        error(4, 'site is down, cannot start')

    if not site.httpServerStart():
        error(5, 'could not start an HTTP server')

def stop (site):
    if not site.isUp():
        error(6, 'site is down, cannot stop')

    if not site.isRunning():
        error(7, 'site has already stopped')

    site.httpServerStop()

def dump (site):
    if not site.isUp():
        error(8, 'site is not up, nothing to dump')

    site.cleanOutput()
    site.dump()

def down (site):
    if not site.isUp():
        error(9, 'site is already down')

    site.httpServerStop()
    site.teardown()

def init (site):
    if file_exists(site.path):
        error(10, 'site already exists')

    site.init()

def step (site):
    basedir = '.' if not len(sys.argv) > 3 else '../'+sys.argv[3]
    if basedir == '.':
        if not site.isUp():
            error(11, 'site is down, cannot step')

        if not site.hasOutput():
            error(12, 'site has no output to merge')

        site.mergeOutput()
    else:
        if not site.isUp():
            test(site)
        if not site.hasOutput():
            dump(site)
        down(site)
        site.mergeOutput(basedir)

def test (site):
    if not site.isUp():
        up(site)
    if not site.isRunning():
        start(site)
    failed = site.testSuite()
    if failed:
        error(13, failed)

def run (site):
    test(site)
    stop(site)
    dump(site)
    down(site)

def status (site):
    print site.getStatus()

COMMANDS = {
    'status': status,
    'run': run,
    'test': test,
    'step': step,
    'init': init,
    'up': up,
    'start': start,
    'stop': stop,
    'dump': dump,
    'down': down,
    'help': help 
}

def cli(factory):
    if not len(sys.argv) > 1:
        for name in os.listdir('test/sites'):
            status(factory(name))
    elif COMMANDS.has_key(sys.argv[1]):
        command = COMMANDS[sys.argv[1]]
        if len(sys.argv) > 2:
            if command == init:
                command(factory(sys.argv[2]))
            else:
                command(factory(exists(sys.argv[2])))
        elif command == COMMANDS['init']:
            def createDir(path):
                if not file_exists(path):
                    os.mkdir(path)
            map(createDir, ['test', 'test/sites', 'test/units'])
        else:
            error(14, 'missing site name')
    else:
        error(15, 'unknwon command')

    sys.exit(0);

if __name__ == '__main__':
    cli(TestSite)
