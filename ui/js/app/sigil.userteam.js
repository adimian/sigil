"use strict"
var UserTeam = function()  {
    var self = this;
    self.name = ko.observable(undefined);

    self.register = function() {
        authed_request('POST', '/team', {
            name: self.name()
        }, function(data) {
            $("#team_add_modal").modal('hide');
        });
    };
};
