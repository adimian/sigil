"use strict"

var build_tabs = function(user) {
    //searchable, can_add, can_toggle, has_permissions
    console.log(user);
    var tabs = [

    new TabItem('overview', 'Overview', {}),
        new TabItem('users', 'Users', {
            searchable: true,
            can_add: true,
            can_toggle: true,
            has_permissions: true
        }),
        //new TabItem('teams', 'User Teams', {searchable:true, can_add:true, can_toggle:true, has_permissions:true}), // feature not completed yet
        new TabItem('groups', 'Virtual Groups', {
            searchable: true,
            can_add: true,
            can_toggle: true,
            has_permissions: false
        }),
        new TabItem('applications', 'Applications', {
            searchable: true,
            can_add: true,
            has_permissions: false
        }),
        new TabItem('import', 'Import from Excel', {}),
        new TabItem('export', 'Export to Excel', {})
    ]
    return tabs
}
