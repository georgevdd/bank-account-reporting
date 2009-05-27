from sqlalchemy import *
import unittest

# Change this to something appropriate
testDbs = 'postgres://tester:testing@localhost/bills_test'

class Owner(object):
    pass

class Owned(object):
    pass

md = MetaData()
ownerTable = Table('Owner', md,
    Column('ownerId', Integer, primary_key=True),
    )
ownedTable = Table('Owned', md,
    Column('ownedId', Integer, primary_key=True),
    Column('ownerId', Integer, ForeignKey(ownerTable.c.ownerId))
    )

ownerMapping = mapper(Owned, ownedTable)
ownerMapping = mapper(Owner, ownerTable,
                      properties={'ownedObjects' : relation(Owned)})

class OuterJoinTest(unittest.TestCase):
    def testOuterJoin(self):

        db = create_engine(testDbs, encoding='utf-8')
        md.create_all(db)

        owner1 = Owner()
        owner2 = Owner()
        
        owned1 = Owned()
        owned2 = Owned()
        
        for x in owned1, owned2:
            owner1.ownedObjects.append(x)
        
        allObjects = owner1, owner2, owned1, owned2

        session = create_session(bind_to=db)

        # Save and update everything.
        for table in ownedTable, ownerTable:
            session.execute(ownerMapping, delete(table), None)
        for x in owner1, owner2:
            session.save(x)
        session.flush()
        for x in allObjects:
            session.update(x)

        j = outerjoin(ownerTable, ownedTable)
        sel = select([ownerTable.c.ownerId, ownedTable.c.ownedId], from_obj=[j], engine=db)
        print str(sel)
        results = sel.execute()
        results = [x for x in results]
        
        expected = [(owner1.ownerId, owned1.ownedId),
                    (owner1.ownerId, owned2.ownedId),
                    (owner2.ownerId, None)]
        
        for x in expected:
            self.assert_(x in results)
        self.assertEqual(len(expected), len(results))

if __name__ == '__main__':
    OuterJoinTest('testOuterJoin').debug()
