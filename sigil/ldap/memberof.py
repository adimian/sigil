from ldap3 import MODIFY_ADD


def load_module(connection):
    dn = 'cn=module,cn=config'
    objectClass = 'olcModuleList'
    attributes = {'cn': 'module',
                  'olcModuleLoad': 'memberof',
                  'olcModulePath': '/usr/lib/ldap'}
    return connection.add(dn, objectClass, attributes)


def install_overlay(connection):
    dn = 'olcOverlay={0}memberof,olcDatabase={1}hdb,cn=config'
    objectClass = ['olcConfig', 'olcMemberOf', 'olcOverlayConfig', 'top']
    attributes = {'olcOverlay': 'memberof',
                  'olcMemberOfDangling': 'ignore',
                  'olcMemberOfRefInt': 'TRUE',
                  'olcMemberOfGroupOC': 'groupOfNames',
                  'olcMemberOfMemberAD': 'member',
                  'olcMemberOfMemberOfAD': 'memberOf'}
    return connection.add(dn, objectClass, attributes)


def install_refint1(connection):
    dn = 'cn=module{1},cn=config'
    attributes = {'olcmoduleload': [(MODIFY_ADD, 'refint')]}
    modification = connection.modify(dn, attributes)
    if modification.endswith('-'):
        modification = modification[:-1]
    return modification


def install_refint2(connection):
    dn = 'olcOverlay={1}refint,olcDatabase={1}hdb,cn=config'
    objectClass = ['olcConfig', 'olcOverlayConfig', 'olcRefintConfig', 'top']
    attributes = {'olcOverlay': '{1}refint',
                  'olcRefintAttribute': 'memberof member manager owner'}
    return connection.add(dn, objectClass, attributes)
