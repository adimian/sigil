"use strict"

var SigilApplication = function() {
    var self = this;

    self.tabs = [new TabItem('overview', 'Overview', false),
        new TabItem('users', 'Users', true),
        //new TabItem('teams', 'User Teams', true), // feature not completed yet
        new TabItem('groups', 'Virtual Groups', true),
        new TabItem('permissions', 'Permissions', true),
        new TabItem('applications', 'Applications', false),
        new TabItem('import', 'Import from Excel', false),
        new TabItem('export', 'Export to Excel', false)
    ]
    self.tabmap = {};
    for (var i = 0; i < self.tabs.length; i++) {
        var tab = self.tabs[i];
        self.tabmap[tab.key] = tab;
    }

    self.login_error_message = ko.observable();
    self.error_message = ko.observable();

    self.server_options = new ServerOptions();
    self.current_user = new LoggedInUser();

    self.edited_user = ko.observable(new User());

    // generic view
    self.data_view = new GenericDataView();
    self.group_view = new GroupDataView();

    var initial_tab = (self.tabmap[location.hash.replace('#', '')] || self.tabs[0]);
    self.current_tab = ko.observable(initial_tab);

    self.authenticated = ko.computed(function() {
        return !!self.current_user.auth_token();
    }, this);

    self.authenticated.subscribe(function(new_value) {
        if (!new_value) {
            $("#login_modal").modal({
                show: true,
                backdrop: 'static'
            })
        } else {
            $("#login_modal").modal('hide');
            self.current_user.get_info();
            location.reload(false);
        };
    });

    self.current_user.auth_token(Cookies.get('token'));
};

SigilApplication.prototype.login = function() {
    var self = this;
    $.post(SIGIL_API + '/login', {
            username: this.current_user.username(),
            password: this.current_user.password(),
            totp: this.current_user.totp()
        },
        function(data) {
            self.current_user.auth_token(data.token);
            Cookies.set('token', data.token)
        }).error(function(data) {
        self.login_error_message(data.responseJSON.message);
    });
};

SigilApplication.prototype.edit_me = function() {
    var self = this;
    app.edited_user(self.current_user);
    $("#user_edit_modal").modal('show');
};

SigilApplication.prototype.logout = function() {
    var self = this;
    Cookies.remove('token')
    self.current_user.auth_token(null);
};

SigilApplication.prototype.set_current_tab = function(data) {
    if (data) {
        location.hash = data.key;
        app.current_tab(data);

        if (Cookies.get('current_tab') && Cookies.get('current_tab').key != data.key) {
            Cookies.set('current_tab', data)
        }
    }
};

SigilApplication.prototype.add_new = function(data) {
    var tab = app.current_tab().key;
    if (tab == 'users') {
        app.edited_user(new User());
        $("#user_add_modal").modal('show');
    };
};
