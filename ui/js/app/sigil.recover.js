"use strict"
var UserAccount = function() {
    var self = this;
    self.email = ko.observable();
};

var RecoverAccountApplication = function() {
    var self = this;
    self.server_options = new ServerOptions();
    self.user_account = new UserAccount();

    self.redirect = function()  {
        window.location = app_root_redirect();
    }

    self.recover = function() {
        var data = {
            email: self.user_account.email()
        };

        var success = function(data) {
            $('#recover-modal').modal('show');
        };

        $.ajax({
            method: "GET",
            url: SIGIL_API + '/user/recover',
            data: data,
            success: success
        }).error(function(data) {
            console.log(data);
        });
    };
};

var init = function() {
    var app = new RecoverAccountApplication();
    ko.applyBindings(app);
    window.app = app;
};

$(init);
