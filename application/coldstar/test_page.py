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
        .factory('ColdStarWS', ['$timeout', '$q', function ($timeout, $q) {
            return function (address, locker) {
                var reconnect_timeout = null,
                    expect_disconnect = false,
                    queue = [],
                    ws = null,
                    promises = {};
                this.address = address;
                this.locker = locker;
                this.timeout = 5000;

                // Session Layer
                this.connect = function () {
                    expect_disconnect = false;
                    var self = this;
                    ws = new WebSocket(this.address);
                    ws.onopen = function (event) {
                        if (reconnect_timeout) {
                            $timeout.cancel(reconnect_timeout);
                            reconnect_timeout = null;
                        }
                        send_command('locker', {
                            locker: self.locker
                        });
                        for (var i=0; i < queue.length; i++) {
                            ws.send(JSON.stringify(queue[i]));
                        }
                        queue = [];
                    };
                    ws.onclose = function (event) {
                        Object.getOwnPropertyNames(promises).forEach(function(magic) {
                            var promise = promises[magic];
                            if (promise) {
                                promise.reject({
                                    exception: 'Disconnect',
                                    message: 'Disconnected'
                                })
                            }
                        });
                        promises = {};
                        if (!expect_disconnect) {
                            reconnect_timeout = $timeout(function () {
                                self.connect.call(self);
                            }, self.timeout);
                            ws = null;
                        }
                    };
                    ws.onerror = function (event) {
                        ws.close();
                    };
                    ws.onmessage = function (event) {
                        var data = JSON.parse(event.data);
                        if (data.hasOwnProperty('magic')) {
                            var promise = promises[data.magic];
                            if (promise) {
                                if (data.hasOwnProperty('exception')) {
                                    promise.reject(data.exception)
                                } else {
                                    promise.resolve(data.result)
                                }
                                promises[data.magic] = undefined;
                            }
                        }
                    };
                };
                this.disconnect = function () {
                    expect_disconnect = true;
                    if (reconnect_timeout) {
                        $timeout.cancel(reconnect_timeout);
                    } else if (ws) {
                        ws.close();
                    }
                };
                var send_command = function(command, params) {
                    if (!ws) return;
                    var defer = $q.defer(),
                        magic = String(Math.floor(Math.random() * Math.pow(2, 16)));
                    promises[magic] = defer;
                    ws.send(JSON.stringify({
                        command: command,
                        params: params,
                        magic: magic
                    }));
                    return defer.promise;
                };

                // Application Layer
                this.acquire_lock = function(object_id) {
                    return send_command('acquire_lock', {object_id: object_id});
                };
                this.release_lock = function(object_id) {
                    return send_command('release_lock', {object_id: object_id});
                };
            };
        }]);
        ColdStarCtrl = function($scope, ColdStarWS) {
            $scope.messages = [];
            $scope.tokens = {};
            var myWS = new ColdStarWS('ws://' + location.host + '/ws/', 'test!12');
            myWS.connect();
            $scope.ws_acquire = function() {
                myWS.acquire_lock('test_01').then(function(result) {
                    $scope.messages.push(result);
                }, function(exception) {
                    $scope.messages.push(exception);
                })
            };
            $scope.ws_release = function() {
                myWS.release_lock('test_01').then(function(result) {
                    $scope.messages.push(result);
                }, function(exception) {
                    $scope.messages.push(exception);
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