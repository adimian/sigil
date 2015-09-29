"use strict"
var VirtualGroup = function()  {
    var self = this;
    self.name = ko.observable(undefined);

    self.register = function() {
        authed_request('POST', '/group', {
            name: self.name()
        }, function(data) {
            $("#group_add_modal").modal('hide');
        });
    };
};
