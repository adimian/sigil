"use strict"
var TabItem = function(key, label, searchable, can_add, can_toggle) {
    this.key = key;
    this.label = label;
    this.searchable = searchable;
    this.can_add = can_add;
    this.can_toggle = can_toggle;
};

var GenericDataView = function(parent) {
    var self = this;
    self.parent_app = parent;
    self.columns = ko.observable([])
    self.collection = ko.observableArray([]);
    self.cursor = ko.observable();
    self.sort_direction = ko.observable(true);
    self.sort_column = ko.observable();

    self.get_data = ko.computed(function() {
        if (self.parent_app === undefined) {
            return;
        }

        var searchbar = self.parent_app.searchbar();
        if (!searchbar) {
            return this.collection();
        } else {
            return ko.utils.arrayFilter(this.collection(), function(item) {
                for (var attribute in item) {
                    var value = item[attribute];
                    if (typeof(value) == "string" && item[attribute].indexOf(searchbar) > -1) {
                        return true;
                    }
                }
                return false;
            });
        }
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

    self.toggle_active = function(item) {
        var tab = app.current_tab().key;
        if (tab == 'groups') {
            authed_request('PATCH', '/group', {
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
        var tab = app.current_tab().key;

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

        if (tab == 'applications') {
            authed_request('GET', '/app', {
                'name': item.name
            }, function(data) {
                var appctx = new AppContext();
                appctx.name(item.name);
                for (var i = 0; i < data.needs.length; i++) {
                    appctx.needs.push({
                        permission: data.needs[i].join(".")
                    });
                }
                app.edited_app(appctx);
                $("#app_details_modal").modal('show');
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
