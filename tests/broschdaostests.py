'''
Created on 11.08.2020

@author: michael
'''
import unittest
from sqlalchemy.engine import create_engine
from asb.brosch.broschdaos import BroschDao, Zeitschrift,\
    ZeitschriftenDao, ZEITSCH_TABLE, NoDataException,\
    GROUP_TABLE, Group,\
    GroupDao, UNTERGRUPPEN_TABLE, DataError, VORLAEUFER_TABLE, BROSCH_TABLE,\
    BroschFilter, Brosch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import insert


class TestBroschDao(unittest.TestCase):


    def setUp(self):
        
        self.engine = create_engine('sqlite://')
        self.connection = self.engine.connect()
        BROSCH_TABLE.create(self.engine)
        self.broschdao = BroschDao(self.connection)
        self.number = 1
        
    def _save_brosch(self, titel):
        
        brosch = Brosch()
        brosch.titel = titel
        brosch.hauptsystematik = 0
        brosch.format = 1
        brosch.nummer = self.number
        self.number += 1
        return self.broschdao.save(brosch)
        
    def testInsert(self):
        
        brosch = self._save_brosch('My title')
        brosch2 = self.broschdao.fetch_by_id(1, Brosch())
        self.assertEqual(1, brosch2.id)
        self.assertEqual(brosch.titel, brosch2.titel)
        self.assertEqual(1, self.broschdao.count())
        
    def testNoInsertWithoutTitle(self):

        with self.assertRaises(IntegrityError):
            self.broschdao.save(Brosch())

    def testUpdate(self):

        brosch = self._save_brosch('My title')
        self.assertEqual(1, brosch.id)
        brosch.title = 'Other title'
        self.broschdao.save(brosch)
        brosch2 = self.broschdao.fetch_by_id(1, Brosch())
        self.assertEquals(brosch.titel, brosch2.titel)
        self.assertEquals(1, self.broschdao.count())
        
    def testFetchNext(self):
        
        self._save_brosch('My title')
        self._save_brosch('Another title')
        brosch = self._save_brosch('My title')

        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual('Another title', brosch.titel)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(1, brosch.id)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(3, brosch.id)
        
    def testFilter(self):
        
        self._save_brosch('My title')
        self._save_brosch('Another title')
        self._save_brosch('My title')

        self.broschdao.filter._set_title_filter('y')
        
        brosch = self.broschdao.fetch_first(Brosch())
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(1, brosch.id)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(3, brosch.id)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(1, brosch.id)
        
    def test_unique_constraint(self):
        
        brosch = Brosch()
        brosch.titel = 'My titel'
        brosch.hauptsystematik = 1
        brosch.format = self.broschdao.A4
        brosch.nummer = 7
        self.broschdao.save(brosch)

        with self.assertRaises(IntegrityError):
            brosch = Brosch()
            brosch.titel = 'My titel'
            brosch.hauptsystematik = 1
            brosch.format = self.broschdao.A4
            brosch.nummer = 7
            self.broschdao.save(brosch)
            
    def test_auto_numbering(self):
        
        brosch = Brosch()
        brosch.titel = 'My titel'
        brosch.hauptsystematik = 1
        brosch.format = self.broschdao.A4
        brosch.nummer = None
        brosch = self.broschdao.save(brosch)
        
        brosch = Brosch()
        brosch.titel = 'My titel'
        brosch.hauptsystematik = 1
        brosch.format = self.broschdao.A4
        brosch.nummer = None
        brosch = self.broschdao.save(brosch)

        self.assertEqual(2, brosch.nummer)

    def testSignatureSort(self):
        
        # id 1
        brosch = self._save_brosch('My title')
        brosch.hauptsystematik = 2
        brosch.format = 2
        brosch.nummer = 2
        self.broschdao.save(brosch)
        
        # id 2
        brosch = self._save_brosch('Another title')
        brosch.hauptsystematik = 2
        brosch.format = 2
        brosch.nummer = 1
        self.broschdao.save(brosch)

        # id 3
        brosch = self._save_brosch('My title')
        brosch.hauptsystematik = 1
        brosch.format = 1
        brosch.nummer = 1
        self.broschdao.save(brosch)

        # id 4
        brosch = self._save_brosch('Another title')
        brosch.hauptsystematik = 1
        brosch.format = 2
        brosch.nummer = 1
        self.broschdao.save(brosch)

        self.broschdao.filter._set_sort_order(BroschFilter.SIGNATUR_ORDER)
        
        brosch = self.broschdao.fetch_first(Brosch())
        self.assertEqual(3, brosch.id)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual(4, brosch.id)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual(2, brosch.id)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual(1, brosch.id)
        brosch = self.broschdao.fetch_next(brosch)
        self.assertEqual(3, brosch.id)
        brosch = self.broschdao.fetch_previous(brosch)
        self.assertEqual(1, brosch.id)
        brosch = self.broschdao.fetch_previous(brosch)
        self.assertEqual(2, brosch.id)
        brosch = self.broschdao.fetch_previous(brosch)
        self.assertEqual(4, brosch.id)
        brosch = self.broschdao.fetch_previous(brosch)
        self.assertEqual(3, brosch.id)

    def testFetchPrevious(self):
        
        self._save_brosch('My title')
        self._save_brosch('Another title')
        brosch = self._save_brosch('My title')

        brosch = self.broschdao.fetch_previous(brosch)
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(1, brosch.id)
        brosch = self.broschdao.fetch_previous(brosch)
        self.assertEqual('Another title', brosch.titel)
        brosch = self.broschdao.fetch_previous(brosch)
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(3, brosch.id)

    def testFirst(self):
        
        with self.assertRaises(NoDataException):
            self.broschdao.fetch_first(Brosch())
        
        self._save_brosch('My title')
        self._save_brosch('Another title')
        self._save_brosch('Another title')


        brosch = self.broschdao.fetch_first(Brosch())
        self.assertEqual('Another title', brosch.titel)
        self.assertEqual(2, brosch.id)
        
    def testLast(self):
        
        with self.assertRaises(NoDataException):
            self.broschdao.fetch_first(Brosch())
        
        self._save_brosch('My title')
        self._save_brosch('My title')
        self._save_brosch('Another title')

        brosch = self.broschdao.fetch_last(Brosch())
        self.assertEqual('My title', brosch.titel)
        self.assertEqual(2, brosch.id)
        
class TestGroupDao(unittest.TestCase):


    def setUp(self):
        
        self.engine = create_engine('sqlite://')
        self.connection = self.engine.connect()
        GROUP_TABLE.create(self.engine)
        UNTERGRUPPEN_TABLE.create(self.engine)
        VORLAEUFER_TABLE.create(self.engine)
        self.groupdao = GroupDao(self.connection)

    def testSave(self):
        
        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = self.groupdao.fetch_first(Group())
        self.assertEqual('Gruppenname', group.name)
        
    def testFetchFirst(self):
        
        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = self.groupdao.fetch_first(Group())
        self.assertEqual('Gruppenname', group.name)

    def testFetchLast(self):
        
        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = self.groupdao.fetch_last(Group())
        self.assertEqual('Truppenname', group.name)

    def testFetchNext(self):
        
        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Gurkenname'
        self.groupdao.save(group)

        group = self.groupdao.fetch_next(group)
        self.assertEqual('Truppenname', group.name)
        group = self.groupdao.fetch_next(group)
        self.assertEqual('Gruppenname', group.name)
        group = self.groupdao.fetch_next(group)
        self.assertEqual('Gurkenname', group.name)

    def testFetchPrevious(self):
        
        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Gurkenname'
        self.groupdao.save(group)
        
        group = self.groupdao.fetch_previous(group)
        self.assertEqual('Gruppenname', group.name)
        group = self.groupdao.fetch_previous(group)
        self.assertEqual('Truppenname', group.name)
        group = self.groupdao.fetch_previous(group)
        self.assertEqual('Gurkenname', group.name)
        
    def testSubgroups(self):

        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Gurkenname'
        self.groupdao.save(group)
        
        self.connection.execute(insert(UNTERGRUPPEN_TABLE).values(gruppenid=2, untergruppenid=1))
        self.connection.execute(insert(UNTERGRUPPEN_TABLE).values(gruppenid=2, untergruppenid=3))
        
        group = self.groupdao.fetch_by_id(1, Group())
        subgroups = self.groupdao.fetch_subgroups(group)
        self.assertEqual(0, len(subgroups))

        group = self.groupdao.fetch_by_id(2, Group())
        subgroups = self.groupdao.fetch_subgroups(group)
        self.assertEqual(2, len(subgroups))

    def testParentGroupNoParent(self):

        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        
        parentgroup = self.groupdao.fetch_parentgroup(group)
        self.assertEqual(None, parentgroup)

    def testParentGroupOneParent(self):

        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Gurkenname'
        self.groupdao.save(group)
        
        self.connection.execute(insert(UNTERGRUPPEN_TABLE).values(gruppenid=2, untergruppenid=1))
        self.connection.execute(insert(UNTERGRUPPEN_TABLE).values(gruppenid=2, untergruppenid=3))
        
        group = self.groupdao.fetch_by_id(1, Group())
        parentgroup = self.groupdao.fetch_parentgroup(group)
        self.assertEqual(2, parentgroup.id)

    def testParentGroupDataError(self):

        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Gurkenname'
        self.groupdao.save(group)
        
        self.connection.execute(insert(UNTERGRUPPEN_TABLE).values(gruppenid=2, untergruppenid=1))
        self.connection.execute(insert(UNTERGRUPPEN_TABLE).values(gruppenid=3, untergruppenid=1))
        
        group = self.groupdao.fetch_by_id(1, Group())
        with self.assertRaises(DataError):
            self.groupdao.fetch_parentgroup(group)

    def testPredecessors(self):

        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Gurkenname'
        self.groupdao.save(group)
        
        self.connection.execute(insert(VORLAEUFER_TABLE).values(gruppenid=2, vorlaeuferid=1))
        self.connection.execute(insert(VORLAEUFER_TABLE).values(gruppenid=2, vorlaeuferid=3))
        
        group = self.groupdao.fetch_by_id(2, Group())
        predecessors = self.groupdao.fetch_predecessors(group)
        self.assertEqual(2, len(predecessors))

        group = self.groupdao.fetch_by_id(1, Group())
        predecessors = self.groupdao.fetch_subgroups(group)
        self.assertEqual(0, len(predecessors))

    def testSuccessors(self):

        group = Group()
        group.name = 'Gruppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Truppenname'
        self.groupdao.save(group)
        group = Group()
        group.name = 'Gurkenname'
        self.groupdao.save(group)
        
        self.connection.execute(insert(VORLAEUFER_TABLE).values(gruppenid=2, vorlaeuferid=1))
        self.connection.execute(insert(VORLAEUFER_TABLE).values(gruppenid=3, vorlaeuferid=2))
        
        group = self.groupdao.fetch_by_id(2, Group())
        successors = self.groupdao.fetch_successors(group)
        self.assertEqual(1, len(successors))
        self.assertEquals(3, successors[0].id)

        group = self.groupdao.fetch_by_id(3, Group())
        successors = self.groupdao.fetch_subgroups(group)
        self.assertEqual(0, len(successors))
        
class TestZeitschDao(unittest.TestCase):


    def setUp(self):
        
        self.engine = create_engine('sqlite://')
        self.connection = self.engine.connect()
        ZEITSCH_TABLE.create(self.engine)
        self.zdao = ZeitschriftenDao(self.connection)
        self.number = 1
        
    def _save(self, titel):
        
        z = Zeitschrift()
        z.titel = titel
        return self.zdao.save(z)
    
    def test_save(self):
        
        self._save("Zeitschriftentitel")
        z = self.zdao.fetch_by_id(1, Zeitschrift())
        self.assertEqual("Zeitschriftentitel", z.titel)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()