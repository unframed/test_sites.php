import sys, os, json, subprocess, re, string, getpass, glob

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

def mysql_root (script):
    p = subprocess.Popen([
        "mysql",
        "--user=root",
        "--password={0}".format(_CONFIG.get(u'mysqlRootPass', u''))
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdout, stderr) = p.communicate(script)
    p.stdin.close()
    return stdout

def mysql_create (name, user, password):
    return mysql_root((
        "CREATE DATABASE {0} ;\n"
        "GRANT ALL PRIVILEGES ON {0}.* TO "
        "{1}@localhost IDENTIFIED BY '{2}' ;\n"
        "FLUSH PRIVILEGES ;\n"
        ).format(name, user, password))

def mysql_drop (name, user, password):
    return mysql_root("DROP DATABASE IF EXISTS {0} ;\n".format(name))

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
        'git clone -q --shared --branch {2} {0} {1}/run'
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

def run_links (path, links):
    sorted_links = [
        (value.count('/'), key, '{0}/run/{1}'.format(path, value))
        for key, value in links.items()
        ]
    sorted_links.sort()
    for (depth, directory, link) in sorted_links:
        if file_exists(directory) and not file_exists(link):
            shell_exec('ln -nsf {0} {1}'.format(
                os.path.abspath(directory), link
                ))

def run_dump (path):
    git_add_untracked(path)
    status = shell_exec('cd {0}/run; git status -s'.format(path))
    for updated in re.findall(r"(?:A |M | A| M) (.+?)\n", status):
        shell_exec('cd {0}; zip out/run.zip run/{1}'.format(path, updated))

def run_teardown (path):
    shell_exec('rm -rf {0}/run'.format(path))
    return True

def server_start (path, host):
    return subprocess.Popen(['php', '-S', host, '-t', path + '/run']).pid

def server_stop (pid):
    os.kill(pid, 9)
    return True

def http_options (path, host):
    name_port = host.split(':')
    if len(name_port) == 2:
        name, port = name_port
    else:
        name = name_port[0]
        port = '80'
    return {
        'test_sites_path': os.path.abspath(path),
        'test_sites_host': name,
        'test_sites_port': port,
        'test_sites_user': getpass.getuser()
        }

def nginx_start (path, host):
    options = http_options(path, host)
    fpm = path + '/php-fpm.conf'
    fpm_conf = path + '/out/php-fpm.conf'
    template = string.Template(open(fpm).read())
    open(fpm_conf, 'w').write(template.substitute(options))
    nginx = path + '/nginx.conf'
    nginx_conf = path + '/out/nginx.conf'
    template = string.Template(open(nginx).read())
    open(nginx_conf, 'w').write(template.substitute(options))
    return (
        shell_exec('sudo /usr/sbin/nginx -c '+os.path.abspath(nginx_conf)),
        subprocess.Popen(['/usr/sbin/php5-fpm', '-y', fpm_conf]).pid
        )

def nginx_stop (nginx_pid, fpm_pid):
    shell_exec('sudo kill -s QUIT {0}'.format(nginx_pid))
    shell_exec('kill -s QUIT {0}'.format(fpm_pid))
    return True # TODO: assert something about shell_exec's return

def apache2_start (path, host):
    options = http_options(path, host)
    apache2 = path + '/apache2.conf'
    apache2_conf = path + '/out/apache2.conf'
    template = string.Template(open(apache2).read())
    open(apache2_conf, 'w').write(template.substitute(options))
    if (options['test_sites_port']=='80'):
        return shell_exec(
            'sudo /usr/sbin/apache2'
            +' -DSys'+sys.platform.capitalize()
            +' -f '+os.path.abspath(apache2_conf)
            )
    else:
        return shell_exec(
            '/usr/sbin/apache2'
            +' -DSys'+sys.platform.capitalize()
            +' -f '+os.path.abspath(apache2_conf)
            )

def apache2_stop (apache2_pid, path, host):
    options = http_options(path, host)
    if (options['test_sites_port']=='80'):
        shell_exec('sudo kill -s WINCH {0}'.format(apache2_pid))
    else:
        shell_exec('kill -s WINCH {0}'.format(apache2_pid))
    return True # TODO: assert something about shell_exec's return

# API

class TestSite:

    def __init__ (self, name):
        self.name = name
        self.path = 'test/sites/' + self.name
        self.options = {
            u"httpHost": u"127.0.0.1:8089",
            u"httpServer": u"php",
            u"testUnits": []
        }
        self.options.update(_CONFIG)
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
        return self.options.get(u'mysqlTestUser', 'test')

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
        if self.options.has_key(u'gitSource'):
            git_checkout(
                self.path,
                self.options[u'gitSource'],
                self.options.get(u'gitBranch', 'master')
                )
        else:
            os.mkdir(self.path+'/run')
            shell_exec('cd {0}/run; git init'.format(self.path))
        if self.options.has_key(u'links'):
            run_links(self.path, self.options[u'links'])
        if file_exists(self.path+'/run.zip'):
            shell_exec('cd {0}; unzip run.zip'.format(self.path))
        git_add_untracked(self.path)
        git_add_updated(self.path)
        git_commit(self.path)

    def setup (self):
        self.mysqlSetup()
        self.runSetup()

    def dump (self):
        return (self.mysqlDump(), run_dump(self.path))

    def teardown (self):
        return (
            run_teardown(self.path),
            mysql_drop(self.name, self.getMySQLUser(), 'dummy')
            )

    def getHttpHost (self):
        return self.options.get(u'httpHost', u'localhost:8089')

    def getHttpServer (self):
        return self.options.get(u'httpServer', u'php')

    def isRunning (self):
        return file_exists(self.path+'/out/pid')

    def httpServerStart (self):
        server = self.getHttpServer()
        if server == u'php':
            pid = server_start(self.path, self.getHttpHost())
            if pid:
                open(self.path+'/out/pid', 'w').write('{0}'.format(pid))
                return True

            return False
        elif server == u'nginx':
            nginx_start(self.path, self.getHttpHost())
        elif server == u'apache2':
            apache2_start(self.path, self.getHttpHost())
        else:
            return False

        return True

    def httpServerStop (self):
        pid_file = self.path+'/out/pid'
        if file_exists(pid_file):
            pid = int(open(pid_file).read())
            server = self.getHttpServer()
            if server == u'php':
                server_stop(pid)
                os.unlink(pid_file)
            elif server == u'nginx':
                nginx_stop(pid, int(open(self.path+'/out/php-pid').read()))
            elif server == u'apache2':
                apache2_stop(pid, self.path, self.getHttpHost())
            else:
                return False

            return True

        return False

    def testSuite (self):
        phpSuite = glob.glob('./test/sites/{0}/suite/*.php'.format(self.name))
        phpSuite.sort()
        for script in phpSuite:
            print '\ntest {0} {1}\n'.format(self.name, os.path.basename(script))
            try:
                subprocess.check_call('php {0}'.format(script), shell=True)
            except subprocess.CalledProcessError as e:
                return '{0} failed : {1}'.format(os.path.basename(script), e.output)
        casperjsUnits = self.options.get(u'testUnits', [])
        for script in casperjsUnits:
            try:
                if script.endswith('.js'):
                    subprocess.check_call(
                        'deps/casperjs/bin/casperjs test'
                        ' test/units/{0} --name={1} --host={2} --mysqluser={3}'
                        ' --verbose --log-level=warning'
                        .format(script, self.name, self.getHttpHost(), self.getMySQLUser()),
                        shell=True
                        )
                else:
                    shell_exec(script)
            except subprocess.CalledProcessError as e:
                return '{0} failed : {1}'.format(script, e.output)

    def hasOutput (self):
        out_dir = self.path+'/out'
        return file_exists(out_dir) and len(os.listdir(out_dir)) > 0

    def mergeOutput (self, target=None):
        if target:
            basedir = 'test/sites/'+target
        else:
            basedir = self.path
        mysql_zip = self.path+'/out/mysql.zip'
        if file_exists(mysql_zip):
            shell_exec('cp {0} {1} ;'.format(mysql_zip, basedir))
        run_zip = self.path+'/out/run.zip'
        if (file_exists(run_zip)):
            shell_exec('zipmerge {1}/run.zip {0}'.format(run_zip, basedir))

    def cleanOutput (self):
        out_dir = self.path + '/out'
        if file_exists(out_dir):
            shell_exec('rm -rf {0}'.format(out_dir))
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

def error (code, message, exitWithError):
    print ("! "+message+"\r\n")
    if exitWithError:
        sys.exit(code)

def help ():
    print ("see: https://github.com/unframed/test_sites.php\n")

def exists (name):
    if not file_exists('test/sites/'+name):
        return error(1, 'site {0} does not exist'.format(name))

    return name;

def up (site, exitWithError=True):
    if site.isUp():
        return error(2, 'site is already up', exitWithError)

    site.setup()

def start (site, exitWithError=True):
    if site.isRunning():
        return error(3, 'site may be running, cannot start', exitWithError)

    if not site.isUp():
        return error(4, 'site is down, cannot start', exitWithError)

    if not site.httpServerStart():
        return error(5, 'could not start an HTTP server', exitWithError)

def startup (site, exitWithError=True):
    if site.isRunning():
        return error(3, 'site may be running', exitWithError)

    if not site.isUp():
        site.setup()

    if not site.httpServerStart():
        return error(5, 'could not start an HTTP server', exitWithError)

def stop (site, exitWithError=True):
    if not site.isUp():
        return error(6, 'site is down, cannot stop', exitWithError)

    if not site.isRunning():
        return error(7, 'site has already stopped', exitWithError)

    site.httpServerStop()

def dump (site):
    if not site.isUp():
        return error(8, 'site is not up, nothing to dump', True)

    site.cleanOutput()
    site.dump()

def down (site, exitWithError=True):
    if not site.isUp():
        return error(9, 'site is already down', exitWithError)

    site.httpServerStop()
    site.teardown()

def init (site):
    if file_exists(site.path):
        error(10, 'site already exists', True)

    site.init()

def step (site, exitWithError=True):
    if len(sys.argv) > 3:
        if not site.isUp():
            test(site)
        if not site.hasOutput():
            dump(site)
        down(site)
        target = sys.argv[3]
        target_dir = 'test/sites/'+target
        if not file_exists(target_dir):
            os.mkdir(target_dir)
        target_config = target_dir + '/test_sites.json'
        if not file_exists(target_config):
            shell_exec('cp {0}/test_sites.json {1}'.format(site.path, target_config))
        site.mergeOutput(target)
    else:
        if not site.isUp():
            return error(11, 'site is down, cannot step', exitWithError)

        if not site.hasOutput():
            return error(12, 'site has no output to merge', exitWithError)

        site.mergeOutput()

def stepup (site):
    step(site)
    startup(site)

def test (site):
    if not site.isUp():
        up(site)
    if not site.isRunning():
        start(site)
    failed = site.testSuite()
    if failed:
        error(13, failed, True)

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
    'startup': startup,
    'stepup': stepup,
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
            if command == COMMANDS['init']:
                command(factory(sys.argv[2]))
            else:
                command(factory(exists(sys.argv[2])))
        elif command == COMMANDS['init']:
            def createDir(path):
                if not file_exists(path):
                    os.mkdir(path)
            map(createDir, ['test', 'test/sites', 'test/units'])
        elif command in (COMMANDS['stop'], COMMANDS['down']):
            for name in os.listdir('test/sites'):
                site = factory(name)
                status(site)
                command(site, False)
        else:
            error(14, 'missing site name', True)
    else:
        error(15, 'unknwon command', True)

    sys.exit(0);

if __name__ == '__main__':
    cli(TestSite)
