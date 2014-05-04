import test_sites

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

if __name__ == '__main__':
    test_sites.cli(TestPress)