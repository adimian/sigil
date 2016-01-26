"use strict"

var SigilApplication = function() {
    var self = this;

    self.searchbar = ko.observable();

    self.login_error_message = ko.observable();
    self.error_message = ko.observable();

    self.server_options = new ServerOptions();
    self.current_user = new LoggedInUser();

    self.tabs = build_tabs(self.current_user);
    self.tabmap = {};
    for (var i = 0; i < self.tabs.length; i++) {
        var tab = self.tabs[i];
        self.tabmap[tab.key] = tab;
    }

    self.edited_user = ko.observable(new User());
    self.edited_app = ko.observable(new AppContext());
    self.edited_group = ko.observable(new VirtualGroup());

    self.all_apps = ko.observableArray([]);
    self.current_principal = ko.observable(new User());

    // generic view
    self.data_view = new GenericDataView(self);
    self.group_view = new GroupDataView(self);

    // download
    self.download_ready = ko.observable(true);

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
    this.current_user.password(null);
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
    if (tab == 'users')  {
        app.edited_user(new User());
        $("#user_add_modal").modal('show');
    };
    if (tab == 'applications')  {
        app.edited_app(new AppContext());
        $("#app_add_modal").modal('show');
    };
    if (tab == 'groups')  {
        app.edited_group(new VirtualGroup());
        $("#group_add_modal").modal('show');
    };
};

SigilApplication.prototype.download = function() {
    if (app.download_ready()) {
        app.download_ready(false);
        authed_request('GET', '/export/excel', {}, function(data) {
            var url = SIGIL_API + '/download/excel?token=' + data.token;
            $('#download_frame').attr('src', url);
            app.download_ready(true);
        })
    }
};
