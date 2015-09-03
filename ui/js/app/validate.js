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
        });
    };
};

var init = function() {
    var app = new ValidateAccountApplication();
    ko.applyBindings(app);
    window.app = app;
};

$(init);
