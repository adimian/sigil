"use strict"

var SIGIL_API = '/sigil-api';
var SIGIL_TOKEN_HEADER = 'Sigil-Token';

var get_auth_headers = function() {
    var headers = {};
    headers[SIGIL_TOKEN_HEADER] = app.current_user.auth_token();
    return headers;
};

var authed_request = function(verb, url, data, success) {
    return $.ajax({
        method: verb,
        dataType: "json",
        url: SIGIL_API + url,
        data: data,
        success: success,
        headers: get_auth_headers()
    }).error(function(data) {
        if (data.status == 401)  {
            app.current_user.auth_token(null);
        } else {
            if (data.status == 403){
                app.error_message("You don't have the sufficient permissions to perform this action");
                $("#error_popup").modal('show');
            }
            if (data.status == 502 && data.responseJSON === undefined)  {
                app.login_error_message('application server unreachable, please retry later')
                app.current_user.auth_token(null);
            } else {
                app.error_message(data.responseJSON.message);
                $("#error_popup").modal('show');
            }
        }
    });
};

var ServerOptions = function() {
    var self = this;
    self.use_totp = ko.observable();
    self.auth_token_name = ko.observable();
    self.version = ko.observable('loading ...');
    $.getJSON(SIGIL_API + '/options', function(data) {
        self.use_totp(data.use_totp == "1");
        self.auth_token_name(data.auth_token);
        self.version(data.version);
    });
};

var urlParams;
(window.onpopstate = function () {
    var match,
        pl     = /\+/g,  // Regex for replacing addition symbol with a space
        search = /([^&=]+)=?([^&]*)/g,
        decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
        query  = window.location.search.substring(1);

    urlParams = {};
    while (match = search.exec(query))
       urlParams[decode(match[1])] = decode(match[2]);
})();
