"use strict"
var UserAccount = function() {
    var self = this;
    self.token = ko.observable(urlParams["token"]);
    self.password = ko.observable();
    self.qr_code = ko.observable();
};

var ValidateAccountApplication = function() {
    var self = this;
    self.server_options = new ServerOptions();
    self.user_account = new UserAccount();

    self.confirmation_code = ko.observable();
    self.confirmation_message = ko.observable();
    self.sms_message = ko.observable();

    self.redirect = function()  {
        window.location = app_root_redirect();
    }

    self.send_sms = function() {
        self.sms_message("Let's pretend it's sending a SMS right now ...")
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

    self.validate = function() {
        var data = {
            token: self.user_account.token(),
            password: self.user_account.password()
        };

        var success = function(data) {
            if (data.qrcode) {
                self.user_account.qr_code(data.qrcode);
                $('#2FA_modal').modal('show');
            }
        };

        $.ajax({
            method: "POST",
            dataType: "json",
            url: SIGIL_API + '/user/validate',
            data: data,
            success: success
        }).error(function(data) {
            console.log(data);
        });
    };
};

var init = function() {
    var app = new ValidateAccountApplication();
    ko.applyBindings(app);
    window.app = app;
};

$(init);
