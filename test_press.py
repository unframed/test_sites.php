import os, sys
sys.path.append(os.path.abspath(os.pardir))

import test_sites, re

class TestPress (test_sites.TestSite):

    def mysqlImport (self):
        return test_sites.mysql_import(
            self.path, self.getMySQLUser(), 'dummy', self.name, 
            ' | sed s,TEST_SITES_HOST,{0},g | '.format(self.getHttpHost())
            )

    def mysqlDump (self):
        return test_sites.mysql_dump(
            self.path, self.getMySQLUser(), 'dummy', self.name, 
            ' | sed s,{0},TEST_SITES_HOST,g | '.format(self.getHttpHost())
            )

    def setup (self):
        test_sites.TestSite.setup(self)
        # if a wp-config.php exists, make sure the right database is configured
        wp_config = self.path+'/run/wp-config.php'
        if test_sites.file_exists(wp_config):
            configuration = re.sub(
                r"define[(]'DB_NAME', '.+?'[)];", 
                "define('DB_NAME', '{0}');".format(self.name),
                open(wp_config).read()
                )
            open(wp_config, 'w').write(configuration)

if __name__ == '__main__':
    test_sites.cli(TestPress)