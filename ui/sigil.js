"use strict"

var SIGIL_API = '/api';
var SIGIL_TOKEN_HEADER = 'Sigil-Token';

var get_auth_headers = function() {
    var headers = {};
    headers[SIGIL_TOKEN_HEADER] = app.current_user.auth_token();
    return headers;
};

var authed_request = function(verb, url, data, success) {
    return $.ajax({
        method: verb,
        dataType: "json",
        url: SIGIL_API + url,
        data: data,
        success: success,
        headers: get_auth_headers()
    }).error(function(data) {
        if (data.status == 401)  {
            app.current_user.auth_token(null);
        } else {
            if (data.status == 502 || data.responseJSON === undefined)  {
                app.login_error_message('application server unreachable, please retry later')
                app.current_user.auth_token(null);
            } else {
                app.error_message(data.responseJSON.message);
                $("#error_popup").modal('show');
            }
        }
    });
};

var ServerOptions = function() {
    var self = this;
    self.use_totp = ko.observable();
    self.auth_token_name = ko.observable();
    $.getJSON(SIGIL_API + '/options', function(data) {
        self.use_totp(data.use_totp == "1");
        self.auth_token_name(data.auth_token);
    });
};

var User = function() {
    var self = this;
    self.user_id = ko.observable();
    self.first_name = ko.observable();
    self.last_name = ko.observable();
    self.display_name = ko.observable();
    self.username = ko.observable();
    self.mobile_number = ko.observable();
    self.email = ko.observable();
    self.active = ko.observable();

    self.groups = ko.observableArray();

    self.reset_password = function() {
        // call sigil to reset password
    };

    self.reset_totp = function() {
        // call sigil to reset totp
    };

    self.load = function(item) {
        self.user_id(item.id);
        self.first_name(item.firstname);
        self.last_name(item.lastname);
        self.display_name(item.displayname);
        self.username(item.username);
        self.email(item.email);
        self.active(item.active);
        self.mobile_number(item.mobile);
    };

    self.persist = function() {
        var update = {
            username: self.username(),
            active: self.active(),
            display: self.display_name(),
            email: self.email(),
            firstname: self.first_name(),
            mobile_number: self.mobile_number(),
            surname: self.last_name()
        };
        authed_request('POST', '/user/details', update, function(data) {
            self.load(data);
            $("#user_edit_modal").modal('hide');
			location.reload(false);
        });

    };

};

var LoggedInUser = function() {
    var self = this;
    self.password = ko.observable();
    self.totp = ko.observable();

    self.auth_token = ko.observable("placeholder");

    self.get_info = function() {
        authed_request('GET', '/user/details', null, function(data) {
            self.load(data);
        });
    };
};
LoggedInUser.prototype = new User();

var TabItem = function(key, label, searchable, can_add) {
    this.key = key;
    this.label = label;
    this.searchable = searchable;
    this.can_add = searchable;
};

var GenericDataView = function() {
    var self = this;
    self.columns = ko.observable([])
    self.collection = ko.observableArray([]);
    self.cursor = ko.observable();
	self.sort_direction = ko.observable(true);
	self.sort_column = ko.observable();

    self.get_data = ko.computed(function() {
        var res = this.collection();
        return res;
    }, this);

    self.headers = ko.computed(function() {
        var res = [];
        for (var i = 0; i < self.columns().length; i++) {
            res.push({
                'name': self.columns()[i].label,
                'key': self.columns()[i].key
            });
        }
        return res;
    }, this);

    self.sortby = function(item) {
        var column = item.key;
		if (column == self.sort_column()){
			self.sort_direction(!self.sort_direction());
		} else {
			self.sort_direction(true);
		}
		self.sort_column(column);

        self.collection.sort(function(a, b) {
            var left = a[column];
            var right = b[column];
			if (!self.sort_direction()){
				var tmp = left;
				left = right;
				right = tmp;
			}
            if (typeof(left) == 'number' || typeof(left) == 'boolean') {
                return left - right;
            } else {
                return String(left).localeCompare(String(right));
            }
        });
    };

    self.show_detail = function(item)  {
        var tab = app.current_tab().key;
        self.cursor(item);

        if (tab == 'groups') {
            authed_request('GET', '/group/members', {
                'name': item.name
            }, function(data) {
                app.group_view.collection(data['users']);
                app.group_view.active(data['active']);
                app.group_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('username', 'Username'),
                    new DataColumn('displayname', 'Display Name')
                ]);
            });
            $("#group_popup").modal('show');
        };

        if (tab == 'users') {
            authed_request('GET', '/user/details', {
                'username': item.username
            }, function(data) {
                var user = new User();
                user.load(data);
                app.edited_user(user);
                $("#user_edit_modal").modal('show');
            });
        };
    };
};


var GroupDataView = function() {
    var self = this;
    self.active = ko.observable();
    self.name = ko.observable();

    self.new_users = ko.observableArray([]);
    self.add_user = ko.observable();

    self.usernames = ko.computed(function() {
        var res = [];
        for (var i = 0; i < self.collection().length; i++) {
            res.push(self.collection()[i].username);
        }
        return res;
    }, this);


    self.add_user.subscribe(function(new_value) {
        if (new_value && new_value.length > 0) {
            authed_request('GET', '/user/search', {
                'query': new_value
            }, function(data) {
                self.new_users(data['users']);
            });
        };
    });

    self.remove_selected = function(item) {
        self.collection.remove(item);
        authed_request('DELETE', '/group/members', {
            'name': app.data_view.cursor().name,
            'usernames': JSON.stringify([item.username])
        }, function() {});
    }

    self.add_selected = function(item) {
        self.add_user(null);
        if ($.inArray(item.username, self.usernames()) === -1) {
            self.collection.push(item);
            authed_request('POST', '/group/members', {
                'name': app.data_view.cursor().name,
                'usernames': JSON.stringify([item.username])
            }, function() {});
        }
    };
};
GroupDataView.prototype = new GenericDataView();

var DataColumn = function(key, label) {
    this.key = key;
    this.label = label;
};

var SigilApplication = function() {
    var self = this;

    self.tabs = [new TabItem('overview', 'Overview', false),
        new TabItem('users', 'Users', true),
        //new TabItem('teams', 'User Teams', true), // feature not completed yet
        new TabItem('groups', 'Virtual Groups', true),
        new TabItem('permissions', 'Permissions', true),
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


var init = function() {
    var app = new SigilApplication();
    ko.applyBindings(app);
    window.app = app;

    Sammy(function() {
        this.get('/', function() {});
        this.get('#users', function() {
            authed_request('GET', '/user', null, function(data) {
                app.data_view.collection(data['users']);
                app.data_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('username', 'Username'),
                    new DataColumn('displayname', 'Display Name'),
                    new DataColumn('email', 'E-mail'),
                    new DataColumn('active', 'Active')
                ]);
            });
        });

        this.get('#overview', function() {
            app.data_view.collection(null);
        });
        this.get('#teams', function() {
            authed_request('GET', '/team', null, function(data) {
                app.data_view.collection(data['groups']);
                app.data_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('name', 'Name'),
                    new DataColumn('active', 'Active')
                ]);
            });
        });
        this.get('#groups', function() {
            authed_request('GET', '/group', null, function(data) {
                app.data_view.collection(data['groups']);
                app.data_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('name', 'Name'),
                    new DataColumn('active', 'Active')
                ]);
            });
        });
        this.get('#permissions', function() {
            app.data_view.collection(null);
        });
        this.get('#import', function() {
            app.data_view.collection(null);
        });
        this.get('#export', function() {
            app.data_view.collection(null);
        });

    }).run();

    app.current_user.get_info();

    // dropzone setup
    Dropzone.options.importFileDropzone = {
        url: SIGIL_API + "/import/excel",
        paramName: "file",
        headers: get_auth_headers(),
        uploadMultiple: false,
        maxFiles: 1,
        addRemoveLinks: false,
        acceptedFiles: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel.sheet.macroEnabled.12",
        init: function() {
            this.on("error", function(file, response) {
                $(".dz-error-message>span").text(response.message);
            });
        }
    };

};

$(init);
