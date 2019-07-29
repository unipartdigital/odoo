odoo.define('web.framework', function (require) {
"use strict";

var core = require('web.core');
var crash_manager = require('web.crash_manager');
var ajax = require('web.ajax');
var Widget = require('web.Widget');

var _t = core._t;

var message = _t("Loading");
var mes = message;
var dots = 0;

var Throbber = Widget.extend({
    template: "Throbber",
    start: function() {
        this.start_time = new Date().getTime();
        this.act_message();
    },
    act_message: function() {
        var self = this;
        setTimeout(function() {
            if (self.isDestroyed())
                return;
            mes = mes + '.';
            if(dots == 8) {
                mes = message;
                dots = 0;
            }   
            self.$(".oe_throbber_message").html(mes);
            dots++;
            self.act_message();
        }, 1000);
    },
});

/** Setup blockui */
if ($.blockUI) {
    $.blockUI.defaults.baseZ = 1100;
    $.blockUI.defaults.message = '<div class="openerp oe_blockui_spin_container" style="background-color: transparent;">';
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
}


var throbbers = [];

function blockUI() {
    var tmp = $.blockUI.apply($, arguments);
    var throbber = new Throbber();
    throbbers.push(throbber);
    throbber.appendTo($(".oe_blockui_spin_container"));
    $(document.body).addClass('o_ui_blocked');
    return tmp;
}

function unblockUI() {
    _.invoke(throbbers, 'destroy');
    throbbers = [];
    $(document.body).removeClass('o_ui_blocked');
    return $.unblockUI.apply($, arguments);
}

/**
 * Redirect to url by replacing window.location
 * If wait is true, sleep 1s and wait for the server i.e. after a restart.
 */
function redirect (url, wait) {
    // Dont display a dialog if some xmlhttprequest are in progress
    crash_manager.disable();

    var load = function() {
        var old = "" + window.location;
        var old_no_hash = old.split("#")[0];
        var url_no_hash = url.split("#")[0];
        location.assign(url);
        if (old_no_hash === url_no_hash) {
            location.reload(true);
        }
    };

    var wait_server = function() {
        ajax.rpc("/web/webclient/version_info", {}).done(load).fail(function() {
            setTimeout(wait_server, 250);
        });
    };

    if (wait) {
        setTimeout(wait_server, 1000);
    } else {
        load();
    }
}

//  * Client action to reload the whole interface.
//  * If params.menu_id, it opens the given menu entry.
//  * If params.wait, reload will wait the openerp server to be reachable before reloading

function Reload(parent, action) {
    var params = action.params || {};
    var menu_id = params.menu_id || false;
    var l = window.location;

    var sobj = $.deparam(l.search.substr(1));
    if (params.url_search) {
        sobj = _.extend(sobj, params.url_search);
    }
    var search = '?' + $.param(sobj);

    var hash = l.hash;
    if (menu_id) {
        hash = "#menu_id=" + menu_id;
    }
    var url = l.protocol + "//" + l.host + l.pathname + search + hash;

    // Clear cache
    core.bus.trigger('clear_cache');

    redirect(url, params.wait);
}

core.action_registry.add("reload", Reload);


/**
 * Client action to go back home.
 */
function Home (parent, action) {
    var url = '/' + (window.location.search || '');
    redirect(url, action && action.params && action.params.wait);
}
core.action_registry.add("home", Home);

/**
 * Client action to go back in breadcrumb history.
 * If can't go back in history stack, will go back to home.
 */
function HistoryBack (parent) {
    parent.history_back().fail(function () {
        Home(parent);
    });
}
core.action_registry.add("history_back", HistoryBack);

function login(redirectUrl) {
    if (redirectUrl) {
        redirect('/web/login?redirect=' + encodeURIComponent(redirectUrl));
    } else {
        redirect('/web/login');
    }
}
core.action_registry.add("login", login);

function logout() {
    redirect('/web/session/logout');
    return $.Deferred();
}
core.action_registry.add("logout", logout);

/**
 * Client action to refresh the session context (making sure
 * HTTP requests will have the right one) then reload the
 * whole interface.
 */
function ReloadContext (parent, action) {
    // side-effect of get_session_info is to refresh the session context
    ajax.rpc("/web/session/get_session_info", {}).then(function() {
        Reload(parent, action);
    });
}
core.action_registry.add("reload_context", ReloadContext);

// In Internet Explorer, document doesn't have the contains method, so we make a
// polyfill for the method in order to be compatible.
if (!document.contains) {
    document.contains = function contains (node) {
        if (!(0 in arguments)) {
            throw new TypeError('1 argument is required');
        }

        do {
            if (this === node) {
                return true;
            }
        } while (node = node && node.parentNode);

        return false;
    };
}

return {
    blockUI: blockUI,
    unblockUI: unblockUI,
    redirect: redirect,
};

});
