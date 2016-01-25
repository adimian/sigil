"use strict"
var UserAccount = function() {
    var self = this;
    self.email = ko.observable();
};

var RecoverAccountApplication = function() {
    var self = this;
    self.server_options = new ServerOptions();
    self.user_account = new UserAccount();

    self.error_message = ko.observable(null);

    self.redirect = function()  {
        window.location = app_root_redirect();
    }

    self.recover = function() {
        self.error_message(null);

        var data = {
            email: self.user_account.email()
        };

        if (self.user_account.email() === undefined || !self.user_account.email().length)  {

            self.error_message("Please provide identification");

        } else {

            var success = function(data) {
                $('#recover-modal').modal('show');
            };

            $.ajax({
                method: "GET",
                url: SIGIL_API + '/user/recover',
                data: data,
                success: success
            }).error(function(data) {
                if (data.status == 404)  {
                    self.error_message('E-mail or username not found');
                }
                console.log(data);
            });

        }
    };
};

var init = function() {
    var app = new RecoverAccountApplication();
    ko.applyBindings(app);
    window.app = app;
};

$(init);
