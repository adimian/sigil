"use strict"

var build_tabs = function() {
    //searchable, can_add, can_toggle, has_permissions
    var tabs = [new TabItem('overview', 'Overview', {})]

    var s = app.current_user.s;

    if (s.can('users.write') && s.can('users.read')) {
        tabs.push(new TabItem('users', 'Users', {
            searchable: true,
            can_add: true,
            can_toggle: true,
            has_permissions: true
        }));

    }

    if (s.can('groups.write') && s.can('groups.read')) {
        tabs.push(new TabItem('groups', 'Virtual Groups', {
            searchable: true,
            can_add: true,
            can_toggle: true,
            has_permissions: false
        }));

    }

    if (s.can('teams.write') && s.can('teams.read')) {
        tabs.push(new TabItem('teams', 'User Teams', {
            searchable: true,
            can_add: true,
            can_toggle: true,
            has_permissions: true
        }));

    }

    if (s.can('appcontexts.write') && s.can('appcontexts.read')) {
        tabs.push(new TabItem('applications', 'Applications', {
            searchable: true,
            can_add: true,
            has_permissions: false
        }));
    }

    if (s.can('users.write') && s.can('users.read')) {
        tabs.push(new TabItem('import', 'Import from Excel', {}));
        tabs.push(new TabItem('export', 'Export to Excel', {}));
    }

    return tabs
}
