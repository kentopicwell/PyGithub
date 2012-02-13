import unittest
import MockMockMock

from GithubObject import *

class GithubObjectTestCase( unittest.TestCase ):
    def testDuplicatedAttributeInOnePolicy( self ):
        with self.assertRaises( BadGithubObjectException ):
            GithubObject( "", SimpleScalarAttributes( "a", "a" ) )

    def testDuplicatedAttributeInTwoPolicies( self ):
        with self.assertRaises( BadGithubObjectException ):
            GithubObject( "", SimpleScalarAttributes( "a" ), SimpleScalarAttributes( "a" ) )

class TestCaseWithGithubTestObject( unittest.TestCase ):
    def setUp( self ):
        unittest.TestCase.setUp( self )
        self.g = MockMockMock.Mock( "github" )
        self.o = self.GithubTestObject( self.g.object, { "a1": 1, "a2": 2 }, lazy = True )

    def tearDown( self ):
        self.g.tearDown()
        unittest.TestCase.tearDown( self )

    def expectGet( self, url ):
        return self.g.expect._dataRequest( "GET", url )

    def expectPut( self, url ):
        return self.g.expect._statusRequest( "PUT", url )

    def expectPatch( self, url, data ):
        return self.g.expect._dataRequest( "PATCH", url, data )

    def expectDelete( self, url ):
        return self.g.expect._statusRequest( "DELETE", url )

class GithubObjectWithOnlySimpleScalarAttributes( TestCaseWithGithubTestObject ):
    GithubTestObject = GithubObject(
        "GithubTestObject",
        BaseUrl( lambda obj: "/test" ),
        SimpleScalarAttributes( "a1", "a2", "a3", "a4" )
    )

    def testInterface( self ):
        self.assertEqual( [ e for e in dir( self.o ) if not e.startswith( "_" ) ], [ "a1", "a2", "a3", "a4"  ] )

    def testCompletion( self ):
        # A GithubObject:
        # - knows the attributes given to its constructor
        self.assertEqual( self.o.a1, 1 )
        self.assertEqual( self.o.a2, 2 )
        # - is completed the first time any unknown attribute is requested
        self.expectGet( "/test" ).andReturn( { "a2": 22, "a3": 3 } )
        self.assertEqual( self.o.a3, 3 )
        # - remembers the attributes that were not updated
        self.assertEqual( self.o.a1, 1 )
        # - acknowledges updates of attributes
        self.assertEqual( self.o.a2, 22 )
        # - remembers that some attributes are absent even after an update
        self.assertEqual( self.o.a4, None )

    def testUnknownAttribute( self ):
        self.assertRaises( AttributeError, lambda: self.o.foobar )

    def testNonLazyConstruction( self ):
        self.expectGet( "/test" ).andReturn( { "a2": 2, "a3": 3 } )
        o = self.GithubTestObject( self.g.object, {}, lazy = False )
        self.g.tearDown()
        self.assertEqual( o.a1, None )
        self.assertEqual( o.a2, 2 )
        self.assertEqual( o.a3, 3 )
        self.assertEqual( o.a4, None )

class GithubObjectWithOtherBaseUrl( TestCaseWithGithubTestObject ):
    GithubTestObject = GithubObject(
        "GithubTestObject",
        BaseUrl( lambda obj: "/other/" + str( obj.a1 ) ),
        SimpleScalarAttributes( "a1", "a2", "a3", "a4" )
    )

    def testCompletion( self ):
        self.expectGet( "/other/1" ).andReturn( { "a2": 22, "a3": 3 } )
        self.assertEqual( self.o.a3, 3 )

class EditableGithubObject( TestCaseWithGithubTestObject ):
    GithubTestObject = GithubObject(
        "GithubTestObject",
        BaseUrl( lambda obj: "/test" ),
        SimpleScalarAttributes( "a1", "a2", "a3", "a4" ),
        Editable( [ "a1" ], [ "a2", "a4" ] ),
    )

    def testEditWithoutArgument( self ):
        with self.assertRaises( TypeError ):
            self.o.edit()

    def testEditWithSillyArgument( self ):
        with self.assertRaises( TypeError ):
            self.o.edit( foobar = 42 )

    def testEditWithOneKeywordArgument( self ):
        self.expectPatch( "/test", { "a1": 11 } ).andReturn( {} )
        self.o.edit( a1 = 11 )

    def testEditWithTwoKeywordArguments( self ):
        self.expectPatch( "/test", { "a1": 11, "a2": 22 } ).andReturn( {} )
        self.o.edit( a1 = 11, a2 = 22 )

    def testEditWithTwoKeywordArgumentsSkipingFirstOptionalArgument( self ):
        self.expectPatch( "/test", { "a1": 11, "a4": 44 } ).andReturn( {} )
        self.o.edit( a1 = 11, a4 = 44 )

    def testEditWithThreeKeywordArguments( self ):
        self.expectPatch( "/test", { "a1": 11, "a2": 22, "a4": 44 } ).andReturn( {} )
        self.o.edit( a1 = 11, a4 = 44, a2 = 22 )

    def testEditWithOnePositionalArgument( self ):
        self.expectPatch( "/test", { "a1": 11 } ).andReturn( {} )
        self.o.edit( 11 )

    def testEditWithTwoPositionalArguments( self ):
        self.expectPatch( "/test", { "a1": 11, "a2": 22 } ).andReturn( {} )
        self.o.edit( 11, 22 )

    def testEditWithThreePositionalArguments( self ):
        self.expectPatch( "/test", { "a1": 11, "a2": 22, "a4": 44 } ).andReturn( {} )
        self.o.edit( 11, 22, 44 )

    def testEditWithMixedArguments_1( self ):
        self.expectPatch( "/test", { "a1": 11, "a2": 22 } ).andReturn( {} )
        self.o.edit( 11, a2 = 22 )

    def testEditWithMixedArguments_2( self ):
        self.expectPatch( "/test", { "a1": 11, "a2": 22, "a4": 44 } ).andReturn( {} )
        self.o.edit( 11, a2 = 22, a4 = 44 )

    def testEditWithMixedArguments_3( self ):
        self.expectPatch( "/test", { "a1": 11, "a2": 22, "a4": 44 } ).andReturn( {} )
        self.o.edit( 11, 22, a4 = 44 )

    def testAcknoledgeUpdatesOfAttributes( self ):
        self.expectPatch( "/test", { "a1": 11 } ).andReturn( { "a2": 22, "a3": 3 } )
        self.o.edit( a1 = 11 )
        self.assertEqual( self.o.a1, 1 )
        self.assertEqual( self.o.a2, 22 )
        self.assertEqual( self.o.a3, 3 )
        self.expectGet( "/test" ).andReturn( {} )
        self.assertEqual( self.o.a4, None )

class DeletableGithubObject( TestCaseWithGithubTestObject ):
    GithubTestObject = GithubObject(
        "GithubTestObject",
        BaseUrl( lambda obj: "/test" ),
        SimpleScalarAttributes( "a1", "a2", "a3", "a4" ),
        Deletable(),
    )

    def testDelete( self ):
        self.expectDelete( "/test" )
        self.o.delete()

class GithubObjectWithExtendedScalarAttribute( TestCaseWithGithubTestObject ):
    ContainedObject = GithubObject(
        "ContainedObject",
        BaseUrl( lambda obj: "/test/a3s/" + obj.id ),
        SimpleScalarAttributes( "id", "name", "desc" )
    )

    GithubTestObject = GithubObject(
        "GithubTestObject",
        BaseUrl( lambda obj: "/test" ),
        SimpleScalarAttributes( "a1", "a2" ),
        ExtendedScalarAttribute( "a3", ContainedObject )
    )

    def testCompletion( self ):
        self.expectGet( "/test" ).andReturn( { "a3": { "id": "id1", "name": "name1" } } )
        self.assertEqual( self.o.a3.id, "id1" )
        self.assertEqual( self.o.a3.name, "name1" )
        self.expectGet( "/test/a3s/id1" ).andReturn( { "desc": "desc1" } )
        self.assertEqual( self.o.a3.desc, "desc1" )

class GithubObjectWithExtendedListAttribute( TestCaseWithGithubTestObject ):
    ContainedObject = GithubObject(
        "ContainedObject",
        BaseUrl( lambda obj: "/test/a3s/" + obj.id ),
        SimpleScalarAttributes( "id", "name" )
    )

    GithubTestObject = GithubObject(
        "GithubTestObject",
        BaseUrl( lambda obj: "/test" ),
        SimpleScalarAttributes( "a1", "a2" ),
        ExtendedListAttribute( "a3s", ContainedObject )
    )

    def testGetList( self ):
        self.expectGet( "/test/a3s" ).andReturn( [ { "id": "id1" }, { "id": "id2" }, { "id": "id3" } ] )
        a3s = self.o.get_a3s()
        self.assertEqual( len( a3s ), 3 )
        self.assertEqual( a3s[ 0 ].id, "id1" )
        self.expectGet( "/test/a3s/id1" ).andReturn( { "name": "name1" } )
        self.assertEqual( a3s[ 0 ].name, "name1" )

class GithubObjectWithModifiableExtendedListAttribute( TestCaseWithGithubTestObject ):
    ContainedObject = GithubObject(
        "ContainedObject",
        BaseUrl( lambda obj: "/test/a3s/" + obj.id ),
        Identity( lambda obj: obj.id ),
        SimpleScalarAttributes( "id", "name" ),
    )

    GithubTestObject = GithubObject(
        "GithubTestObject",
        BaseUrl( lambda obj: "/test" ),
        SimpleScalarAttributes( "a1", "a2" ),
        ExtendedListAttribute( "a3s", ContainedObject, addable = True, removable = True )
    )

    def testAddToList( self ):
        a3ToAdd = self.ContainedObject( self.g.object, { "id": "idAdd", "name": "nameAdd" }, lazy = True )
        self.expectPut( "/test/a3s/idAdd" ).andReturn( {} )
        self.o.add_a3s( a3ToAdd )

    def testRemoveFromList( self ):
        a3ToRemove = self.ContainedObject( self.g.object, { "id": "idRemove", "name": "nameRemove" }, lazy = True )
        self.expectDelete( "/test/a3s/idRemove" ).andReturn( {} )
        self.o.remove_a3s( a3ToRemove )

unittest.main()