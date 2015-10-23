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

    self.permissions = ko.observableArray();

    this.name = ko.pureComputed(function() {
        return self.display_name();
    }, this);

    self.change_password = function() {
        if (! self.old_password()){
            alert('Missing old password');
            return;
        }
        if (! self.new_password()){
            alert('Missing new password');
            return;
        }
        authed_request('POST', '/user/password', {
            old_password: self.old_password(),
            new_password: self.new_password()
        }, function(){});
    };

    self.request_password_change = function() {
        $("#change_password_modal").modal('show');
    };



    self.reset_totp = function() {
        self.reset_totp_app.reset();
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
    };

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
            alert('New user created');
        });
        $("#user_add_modal").modal('hide');
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
