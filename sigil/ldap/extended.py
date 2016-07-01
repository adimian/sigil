def install_extended(connection):
    dn = 'cn=extendedInetPerson,cn=schema,cn=config'
    objectClass = 'olcSchemaConfig'
    attributes = {'cn': 'extendedInetPerson',
                  'olcAttributeTypes': ['''{0}( 1.3.6.1.4.1.4203.666.1.90 NAME 'totpSecret' DESC 'Timed one time password secret' EQUALITY caseIgnoreMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.15{64} SINGLE-VALUE )''',
                                        '''{0}( 1.3.6.1.4.1.4203.666.1.91 NAME 'totpEnabled' DESC 'Timed one time password enabled' EQUALITY caseIgnoreMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.15{64} SINGLE-VALUE )'''],
                  'olcObjectClasses': '''{0}( 1.3.6.1.4.1.4203.666.1.100 NAME 'extendedInetPerson' DESC 'objectClass for totp' SUP inetOrgPerson STRUCTURAL MAY (totpSecret $ totpEnabled) )'''}

    return connection.add(dn, objectClass, attributes)
