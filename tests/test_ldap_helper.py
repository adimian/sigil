from ldap3 import Connection, LDIF
import pytest
from sigil.ldap.memberof import (load_module, install_overlay,
                                 install_refint1, install_refint2)
from sigil.ldap.extended import install_extended


@pytest.fixture
def connection():
    return Connection(server=None, client_strategy=LDIF)


def test_memberof_config(connection):

    fixture = load_module(connection)
    expected = '''version: 1
dn: cn=module,cn=config
changetype: add
objectClass: olcModuleList
cn: module
olcModuleLoad: memberof
olcModulePath: /usr/lib/ldap'''

    assert sorted(fixture.splitlines()) == sorted(expected.splitlines())


def test_install_overlay(connection):

    fixture = install_overlay(connection)
    expected = '''version: 1
dn: olcOverlay={0}memberof,olcDatabase={1}hdb,cn=config
changetype: add
objectClass: olcConfig
objectClass: olcMemberOf
objectClass: olcOverlayConfig
objectClass: top
olcOverlay: memberof
olcMemberOfDangling: ignore
olcMemberOfRefInt: TRUE
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf'''

    assert sorted(fixture.splitlines()) == sorted(expected.splitlines())


def test_install_refint1(connection):

    fixture = install_refint1(connection)
    expected = '''version: 1
dn: cn=module{1},cn=config
changetype: modify
add: olcmoduleload
olcmoduleload: refint'''

    assert sorted(fixture.splitlines()) == sorted(expected.splitlines())


def test_install_refint2(connection):

    fixture = install_refint2(connection)
    expected = '''version: 1
dn: olcOverlay={1}refint,olcDatabase={1}hdb,cn=config
changetype: add
objectClass: olcConfig
objectClass: olcOverlayConfig
objectClass: olcRefintConfig
objectClass: top
olcOverlay: {1}refint
olcRefintAttribute: memberof member manager owner'''

    assert sorted(fixture.splitlines()) == sorted(expected.splitlines())


def test_install_extended(connection):
    fixture = install_extended(connection)
    expected = '''version: 1
dn: cn=extendedInetPerson,cn=schema,cn=config
changetype: add
objectClass: olcSchemaConfig
olcObjectClasses: {0}( 1.3.6.1.4.1.4203.666.1.100 NAME 'extendedInetPerson' DE
 SC 'objectClass for totp' SUP inetOrgPerson STRUCTURAL MAY (totpSecret $ totp
 Enabled) )
olcAttributeTypes: {0}( 1.3.6.1.4.1.4203.666.1.90 NAME 'totpSecret' DESC 'Time
 d one time password secret' EQUALITY caseIgnoreMatch SYNTAX 1.3.6.1.4.1.1466.
 115.121.1.15{64} SINGLE-VALUE )
olcAttributeTypes: {0}( 1.3.6.1.4.1.4203.666.1.91 NAME 'totpEnabled' DESC 'Tim
 ed one time password enabled' EQUALITY caseIgnoreMatch SYNTAX 1.3.6.1.4.1.146
 6.115.121.1.15{64} SINGLE-VALUE )
cn: extendedInetPerson
'''
    assert sorted(fixture.splitlines()) == sorted(expected.splitlines())
