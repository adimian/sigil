"use strict"
var PAGE_LIMIT = 30;

var TabItem = function(key, label, options) {
    this.key = key;
    this.label = label;
    this.searchable = options.searchable ||  false;
    this.can_add = options.can_add ||  false;
    this.can_toggle = options.can_toggle || false;
    this.has_permissions = options.has_permissions  || false;
};

var GenericDataView = function(parent) {
    var self = this;
    self.parent_app = parent;
    self.columns = ko.observable([])
    self.collection = ko.observableArray([]);
    self.cursor = ko.observable();
    self.sort_direction = ko.observable(true);
    self.sort_column = ko.observable();

    self.limit = ko.observable(PAGE_LIMIT);

    self.table_data = ko.computed(function() {
        if (self.parent_app !== undefined) {
            var searchbar = self.parent_app.searchbar();
            if (!searchbar) {
                return this.collection();
            } else {
                return ko.utils.arrayFilter(this.collection(), function(item) {
                    searchbar = searchbar.toLowerCase();
                    var value = null;
                    var attribute = null;
                    for (attribute in item) {
                        value = item[attribute];
                        if (typeof(value) == "string" && item[attribute].toLowerCase().indexOf(searchbar) > -1) {
                            return true;
                        }
                    }
                    return false;
                });
            }
        }
    }, this);

    self.get_data = ko.computed(function() {
        var res = this.table_data();
        var limit = self.limit();
        if (res && res.length > limit) {
            return res.slice(0, limit);
        }
        return res;
    }, this);

    self.collection.subscribe(function() {
        self.limit(PAGE_LIMIT);
    }, this);

    window.onscroll = function(ev) {
        var full_height = document.body.offsetHeight;
        var position = window.innerHeight + window.scrollY;
        var near_bottom = position >= full_height * 0.9;
        if (this.collection() && near_bottom && this.collection().length > this.limit()) {
            this.limit(this.limit() + PAGE_LIMIT);
        }
    }.bind(this);

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
        if (column == self.sort_column()) {
            self.sort_direction(!self.sort_direction());
        } else {
            self.sort_direction(true);
        }
        self.sort_column(column);

        self.collection.sort(function(a, b) {
            var left = a[column];
            var right = b[column];
            if (!self.sort_direction()) {
                var tmp = left;
                left = right;
                right = tmp;
            }
            if (typeof(left) == 'number' ||  typeof(left) == 'boolean') {
                return left - right;
            } else {
                return String(left).localeCompare(String(right));
            }
        });
    };

    self.tabname = function() {
        return app.current_tab().key;
    }

    self.show_permissions = function(item) {
        var tab = self.tabname();
        if (tab == 'users') {
            var user = new User();
            user.load(item);
            user.load_needs();
            app.current_principal(user);
            $('#assigned_permissions_modal').modal('show');
        }

        if (tab == 'teams') {
            var team = new UserTeam();
            team.load(item);
            team.load_needs();
            app.current_principal(team);
            $('#assigned_permissions_modal').modal('show');
        }
    }

    self.toggle_active = function(item) {
        var tab = self.tabname();
        if (tab == 'groups') {
            authed_request('PATCH', '/group', {
                'name': item.name,
                'active': !item.active
            }, function(data) {
                location.reload(false);
            });
        };
        if (tab == 'teams') {
            authed_request('PATCH', '/team', {
                'name': item.name,
                'active': !item.active
            }, function(data) {
                location.reload(false);
            });
        };
        if (tab == 'users') {
            authed_request('POST', '/user/details', {
                'username': item.username,
                'active': !item.active
            }, function(data) {
                location.reload(false);
            });
        };
    }

    self.show_detail = function(item)  {
        var tab = self.tabname();
        self.cursor(item);

        if (tab == 'groups') {
            authed_request('GET', '/group/members', {
                'name': item.name
            }, function(data) {
                app.group_view.collection(data['users']);
                app.group_view.active(data['active']);
                app.group_view.columns([
                    new DataColumn('username', 'Username'),
                    new DataColumn('displayname', 'Display Name')
                ]);
            });
            $("#group_popup").modal('show');
        };

        if (tab == 'teams') {
            authed_request('GET', '/team/members', {
                'name': item.name
            }, function(data) {
                app.group_view.collection(data['users']);
                app.group_view.active(data['active']);
                app.group_view.columns([
                    new DataColumn('username', 'Username'),
                    new DataColumn('displayname', 'Display Name')
                ]);
            });
            $("#team_popup").modal('show');
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

        if (tab == 'applications') {
            authed_request('GET', '/app', {
                'name': item.name
            }, function(data) {
                var appctx = new AppContext();
                appctx.name(item.name);
                for (var i = 0; i < data.needs.length; i++) {
                    appctx.needs.push(new Need(item.name, data.needs[i]));
                }
                app.edited_app(appctx);
                $("#app_details_modal").modal('show');
            });
        };
    };
};


var GroupDataView = function(parent, resource_type) {
    var self = this;
    self.parent_app = parent;
    self.resource_type = resource_type;
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
        authed_request('DELETE', '/'+self.resource_type+'/members', {
            'name': app.data_view.cursor().name,
            'usernames': JSON.stringify([item.username])
        }, function() {});
    }

    self.add_selected = function(item) {
        self.add_user(null);
        var url = '/'+self.resource_type+'/members';
        if ($.inArray(item.username, self.usernames()) === -1) {
            self.collection.push(item);
            authed_request('POST', url, {
                'name': app.data_view.cursor().name,
                'usernames': JSON.stringify([item.username])
            }, function() {}).error(function(error){console.log(url);});
        }
    };
};
GroupDataView.prototype = new GenericDataView();

var DataColumn = function(key, label) {
    this.key = key;
    this.label = label;
};
