"use strict"

var ResetTotpApplication = function(user_account) {
    var self = this;
    self.user_account = user_account;

    self.confirmation_code = ko.observable();
    self.confirmation_message = ko.observable();
    self.sms_message = ko.observable();
    self.validation_message = ko.observable();

    self.send_sms = function() {
        var data = {
            token: self.user_account.token()
        };

        var success = function(data) {
            self.sms_message('SMS sent !');
        };

        self.sms_message("Sending a SMS right now ...")
        $.ajax({
            method: "POST",
            dataType: "json",
            url: SIGIL_API + '/user/2fa/sms',
            data: data,
            success: success
        }).error(function(data) {
            self.sms_message('Sorry but we are not able to send you a SMS now: ' + data.responseJSON.message);
        });

    };

    self.confirm_method = function() {

        if (self.confirmation_code() === undefined || !self.confirmation_code().length) {
            self.confirmation_message('Please enter your PIN code');
            $("#pin_code").focus();
            return;
        }

        var data = {
            token: self.user_account.token(),
            totp: self.confirmation_code()
        };

        var success = function(data) {
            $('#2FA_modal').modal('hide');
            self.confirmation_message('');
        };

        $.ajax({
            method: "POST",
            dataType: "json",
            url: SIGIL_API + '/user/2fa/confirm',
            data: data,
            success: success
        }).error(function() {
            self.confirmation_message('Sorry but ' + data.totp + ' was not accepted, remember that codes expire quickly');
            console.log(data);
        });
    }

    self.reset = function() {
        var success = function(data) {
            if (data.qrcode) {
                self.user_account.qr_code(data.qrcode);
                self.user_account.token(data.token);
                $('#2FA_modal').modal('show');
            }
        };

        authed_request("POST", '/user/reset2fa', {}, success)
    };
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
    self.qr_code = ko.observable();
    self.token = ko.observable();
    self.reset_totp_app = new ResetTotpApplication(self)

    self.api_key = ko.observable();

    // for password update
    self.old_password = ko.observable();
    self.new_password = ko.observable();

    self.groups = ko.observableArray();
    self.teams = ko.observableArray();

    self.permissions = ko.observableArray();

    this.name = ko.pureComputed(function() {
        return self.display_name();
    }, this);

    self.change_password = function() {
        if (!self.old_password()) {
            app.password_error_message('missing old password');
            return;
        }
        if (!self.new_password()) {
            app.password_error_message('missing new password');
            return;
        }
        authed_request('POST', '/user/password', {
            old_password: self.old_password(),
            new_password: self.new_password()
        }, function() {
            app.password_error_message(null);
            self.new_password(null);
            self.old_password(null);
            noty({
                text: 'You password has been changed',
                timeout: 2000,
                type: 'success',
                layout: 'topCenter',
            });

        });
        $("#change_password_modal").modal('hide');
    };

    self.request_password_change = function() {
        $("#change_password_modal").modal('show');
    };

    self.reset_totp = function() {
        $.confirm({
            title: "Confirmation required",
            text: "This will re-generate a new 2FA code, and invalidate the current one, do you want to proceed ?",
            confirm: function() {
                self.reset_totp_app.reset();
            },
            cancel: function() {
                // nothing
            }
        });
    };

    self.show_api_key = function() {
        authed_request('GET', '/user/key',   {}, function(data) {
            self.api_key(data.key);
            $("#api_key_modal").modal('show');
        });
    };

    self.reset_api_key = function() {
        authed_request('POST', '/user/key',   {}, function(data) {
            self.api_key(data.key);
        });
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

        self.groups(item.groups);
        self.teams(item.teams);
    };

    self.check_all = function(node) {
        var needs = node.needs();
        for (var i = 0; i < needs.length; i++)  {
            needs[i].active(true);
        }
    }

    self.uncheck_all = function(node) {
        var needs = node.needs();
        for (var i = 0; i < needs.length; i++)  {
            needs[i].active(false);
        }
    }

    self.load_needs = function() {
        authed_request('OPTIONS', '/user/permissions', {
            username: self.username()
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

            authed_request('POST', '/user/permissions', {
                context: appctx.name(),
                username: self.username(),
                needs: JSON.stringify(added)
            })

            authed_request('DELETE', '/user/permissions', {
                context: appctx.name(),
                username: self.username(),
                needs: JSON.stringify(removed)
            })
        }
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

    self.register = function() {
        var update = {
            username: self.username(),
            email: self.email(),
            mobile_number: self.mobile_number()
        };
        authed_request('POST', '/user/register', update, function(data) {
            noty({
                text: 'User ' + self.username() + ' created',
                timeout: 2000,
                type: 'success',
                layout: 'topCenter',
            });
        });
        $("#user_add_modal").modal('hide');
    };

};

var Security = function(user) {
    var self = this;

    self.permissions = ko.observableArray();

    self.refresh = function() {
        if (user.auth_token() !== TOKEN_PLACEHOLDER) {
            authed_request('GET', '/user/permissions', {
                context: 'sigil'
            }, function(data) {
                for (var i = 0; i < data.provides.length; i++) {
                    var scope = data.provides[i];
                    var need = new Need('sigil', scope);
                    self.permissions.push(need);
                }
            });
        }
    }

    self.can = function(name) {
        for (var i = 0; i < self.permissions().length; i++)  {
            if (self.permissions()[i].permission === name) {
                return true;
            }
        }
        return false;
    }

    self.permissions.subscribe(function(new_value) {
        app.refresh_tabs();
        app.set_current_tab(app.tabmap[location.hash.replace('#', '')]);
    });

}

var LoggedInUser = function() {
    var self = this;
    self.password = ko.observable();
    self.totp = ko.observable();

    self.auth_token = ko.observable(TOKEN_PLACEHOLDER);

    self.s = new Security(self);

    self.get_info = function() {
        authed_request('GET', '/user/details', null, function(data) {
            self.load(data);
            self.s.refresh();
        });
    };
};
LoggedInUser.prototype = new User();
