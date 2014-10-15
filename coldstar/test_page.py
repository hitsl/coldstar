# -*- coding: utf-8 -*-
from twisted.web.resource import Resource

__author__ = 'mmalkov'


class TestPageResource(Resource):
    def render_GET(self, request):
        return """
<!DOCTYPE html>
    <html ng-app="ColdStar" ng-cloak>
    <head>
        <script src="//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
        <script src="//ajax.googleapis.com/ajax/libs/angularjs/1.2.26/angular.min.js"></script>
        <script>
            ColdStar = angular.module('ColdStar',[])
            .factory('$WebSocket', ['$rootScope', '$timeout', function ($rootScope, $timeout) {
                var Socket = function (address) {
                    this.address = address;
                    this._reconnect = null;
                    this.ws = null;
                    this.timeout = 5000;
                    this.expect_disconnect = false;
                    this.queue = [];
                };
                Socket.prototype.connect = function () {
                    this.expect_disconnect = false;
                    var t;
                    if (arguments.length > 0) {
                        t = arguments[0];
                    } else {
                        t = this
                    }
                    var ws = new WebSocket(this.address);
                    ws.onopen = function (event) {
                        if (t._reconnect) {
                            $timeout.cancel(t._reconnect);
                            t._reconnect = null;
                        }
                        t.ws = ws;
                        if (t._on_open_callback) {
                            t._on_open_callback();
                        }
                        var i;
                        for (i=0; i < t.queue.length; i++) {
                            t.ws.send(JSON.stringify(t.queue[i]));
                        }
                        t.queue = [];
                    };
                    ws.onclose = function (event) {
                        if (t._on_disconnect_callback) {
                            $rootScope.$apply(t._on_disconnect_callback)
                        }
                        if (!t.expect_disconnect) {
                            t._reconnect = $timeout(function () {
                                t.connect(t);
                            }, t.timeout);
                            t.ws = null;
                        }
                    };
                    ws.onerror = function (event) {
                        ws.close();
                    };
                    ws.onmessage = function (event) {
                        if (t._on_message_callback) {
                            $rootScope.$apply(function () {
                                t._on_message_callback(JSON.parse(event.data))
                            })
                        }
                    };
                };
                Socket.prototype.send = function (object) {
                    if (this.ws) {
                        this.ws.send(JSON.stringify(object));
                    } else {
                        this.queue.push(object);
                    }
                };
                Socket.prototype.disconnect = function () {
                    this.expect_disconnect = true;
                    if (this._reconnect) {
                        clearInterval(this._reconnect);
                    } else {
                        this.ws.close();
                    }
                };
                Socket.prototype.onMessage = function (f) {
                    this._on_message_callback = f;
                };
                Socket.prototype.onOpen = function (f) {
                    this._on_open_callback = f;
                };
                Socket.prototype.onDisconnect = function (f) {
                    this._on_disconnect_callback = f;
                };
                return Socket;
            }]);
            ColdStarCtrl = function($scope, $WebSocket) {
                $scope.messages = [];
                $scope.tokens = {};
                var myWS = new $WebSocket('ws://' + location.host + '/ws/');
                myWS.onMessage(function(message) {
                    console.log('Message received: ' + message);
                    $scope.messages.push(message);
                    if (Object.hasOwnProperty(message, 'token')) {
                        $scope.tokens[message.object_id] = message.token;
                    }
                });
                myWS.onOpen(function() {
                    console.log('Connected to WS');
                    myWS.send({
                        command: 'locker',
                        locker: 'test'
                    });
                });
                myWS.connect();
                $scope.ws_acquire = function() {
                    myWS.send({
                        command: 'acquire_lock',
                        object_id: 'test_01'
                    })
                };
                $scope.ws_release = function() {
                    myWS.send({
                        command: 'release_lock',
                        object_id: 'test_01',
                        token: $scope.tokens['test_01']
                    })
                }
            }
        </script>
        <title>ColdStar test page</title>
    </head>
    <body ng-controller="ColdStarCtrl">
        <button ng-click="ws_acquire()">Acquire</button>
        <button ng-click="ws_release()">Release</button>
        <pre ng-bind="messages | json"></pre>
    </body>
    </html>
    """