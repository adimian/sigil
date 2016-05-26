"use strict"
var UserTeam = function()  {
    var self = this;
    self.name = ko.observable(undefined);
    self.permissions = ko.observableArray();

    self.register = function() {
        authed_request('POST', '/team', {
            name: self.name()
        }, function(data) {
            $("#team_add_modal").modal('hide');
        });
    };

    self.load = function(item) {
        self.name(item.name);
    };

    self.load_needs = function() {
        authed_request('OPTIONS', '/team/permissions', {
            name: self.name()
        }, function(data) {
            self.permissions([]);
            for (var app_name in data) {
                var appctx = new AppContext();
                appctx.name(app_name);
                self.permissions.push(appctx);
                for (var i = 0; i < data[app_name].length; i++) {
                    var permission = data[app_name][i];
                    var need = new Need(app_name, permission[0]);
                    need.active(permission[1]);
                    appctx.needs.push(need);
                }
            }
        })
    };

    self.persist_needs = function() {
        for (var i = 0; i < self.permissions().length; i++) {
            var appctx = self.permissions()[i];
            var removed = [];
            var added = [];
            for (var j = 0; j < appctx.needs().length; j++) {
                var need = appctx.needs()[j];
                if (need.active()) {
                    added.push(need.scope);
                } else {
                    removed.push(need.scope);
                }
            }

            authed_request('POST', '/team/permissions', {
                context: appctx.name(),
                name: self.name(),
                needs: JSON.stringify(added)
            })

            authed_request('DELETE', '/team/permissions', {
                context: appctx.name(),
                name: self.name(),
                needs: JSON.stringify(removed)
            })
        }
    };
};
