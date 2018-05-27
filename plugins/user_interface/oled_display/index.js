'use strict';

var libQ = require('kew');
var fs=require('fs-extra');
var config = new (require('v-conf'))();
var exec = require('child_process').exec;
var execSync = require('child_process').execSync;
//var socket = new(require("net").Socket)();
//var net = require("net");
//const socket_address = "/tmp/oled_display.sock";
//var socket = net.createConnection(socket_address);
var oled = require('child_process').spawn('/usr/bin/python3',[__dirname + '/oled_display.py'],{stdio:['ipc']});


module.exports = oledDisplay;
function oledDisplay(context) {
	var self = this;

	this.context = context;
	this.commandRouter = this.context.coreCommand;
	this.logger = this.context.logger;
	this.configManager = this.context.configManager;

}



oledDisplay.prototype.onVolumioStart = function()
{
	var self = this;
	var configFile=this.commandRouter.pluginManager.getConfigurationFile(this.context,'config.json');
	this.config = new (require('v-conf'))();
	this.config.loadFile(configFile);

        self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::######## start' );
 //       socket.connect(socket_address,function(){
  //          self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::onVolumioStart connect to ' + socket_address);
   //     });
  //      socket.on('connect', function() {
   //         self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::onVolumioStart connect to ' + socket_address);
    //    });


        oled.stdout.on('data', (data) => {
          self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::######## stdout' + data);
        });
        
        oled.stderr.on('data', (data) => {
          self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::######## stderr' + data);
        });

    return libQ.resolve();
}

oledDisplay.prototype.onStart = function() {
    var self = this;
	var defer=libQ.defer();


	// Once the Plugin has successfull started resolve the promise
	defer.resolve();

    return defer.promise;
};

oledDisplay.prototype.onStop = function() {
    var self = this;
    var defer=libQ.defer();

    // Once the Plugin has successfull stopped resolve the promise
    defer.resolve();

    return libQ.resolve();
};

oledDisplay.prototype.onRestart = function() {
    var self = this;
    // Optional, use if you need it
};


// Configuration Methods -----------------------------------------------------------------------------

oledDisplay.prototype.getUIConfig = function() {
    var defer = libQ.defer();
    var self = this;

    var lang_code = this.commandRouter.sharedVars.get('language_code');

    self.commandRouter.i18nJson(__dirname+'/i18n/strings_'+lang_code+'.json',
        __dirname+'/i18n/strings_en.json',
        __dirname + '/UIConfig.json')
        .then(function(uiconf)
        {


            defer.resolve(uiconf);
        })
        .fail(function()
        {
            defer.reject(new Error());
        });

    return defer.promise;
};


oledDisplay.prototype.setUIConfig = function(data) {
	var self = this;
	//Perform your installation tasks here
};

oledDisplay.prototype.getConf = function(varName) {
	var self = this;
	//Perform your installation tasks here
};

oledDisplay.prototype.setConf = function(varName, varValue) {
	var self = this;
	//Perform your installation tasks here
};



// Playback Controls ---------------------------------------------------------------------------------------
// If your plugin is not a music_sevice don't use this part and delete it


oledDisplay.prototype.addToBrowseSources = function () {

	// Use this function to add your music service plugin to music sources
    //var data = {name: 'Spotify', uri: 'spotify',plugin_type:'music_service',plugin_name:'spop'};
    this.commandRouter.volumioAddToBrowseSources(data);
};

oledDisplay.prototype.handleBrowseUri = function (curUri) {
    var self = this;

    //self.commandRouter.logger.info(curUri);
    var response;


    return response;
};



// Define a method to clear, add, and play an array of tracks
oledDisplay.prototype.clearAddPlayTrack = function(track) {
	var self = this;
	self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::clearAddPlayTrack');

	self.commandRouter.logger.info(JSON.stringify(track));

	return self.sendSpopCommand('uplay', [track.uri]);
};

oledDisplay.prototype.seek = function (timepos) {
    this.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::seek to ' + timepos);

    return this.sendSpopCommand('seek '+timepos, []);
};

// Stop
oledDisplay.prototype.stop = function() {
	var self = this;
	self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::stop');


};

// Spop pause
oledDisplay.prototype.pause = function() {
	var self = this;
	self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::pause');


};

// Get state
oledDisplay.prototype.getState = function() {
	var self = this;
	self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::getState');


};

//Parse state
oledDisplay.prototype.parseState = function(sState) {
	var self = this;
	self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::parseState');

	//Use this method to parse the state and eventually send it with the following function
};

// Announce updated State
oledDisplay.prototype.pushState = function(state) {
	var self = this;
	self.commandRouter.pushConsoleMessage('[' + Date.now() + '] ' + 'oledDisplay::pushState' + JSON.stringify(state));
        
        oled.send(JSON.stringify(state)); 

	return self.commandRouter.servicePushState(state, self.servicename);
};


oledDisplay.prototype.explodeUri = function(uri) {
	var self = this;
	var defer=libQ.defer();

	// Mandatory: retrieve all info for a given URI

	return defer.promise;
};

oledDisplay.prototype.getAlbumArt = function (data, path) {

	var artist, album;

	if (data != undefined && data.path != undefined) {
		path = data.path;
	}

	var web;

	if (data != undefined && data.artist != undefined) {
		artist = data.artist;
		if (data.album != undefined)
			album = data.album;
		else album = data.artist;

		web = '?web=' + nodetools.urlEncode(artist) + '/' + nodetools.urlEncode(album) + '/large'
	}

	var url = '/albumart';

	if (web != undefined)
		url = url + web;

	if (web != undefined && path != undefined)
		url = url + '&';
	else if (path != undefined)
		url = url + '?';

	if (path != undefined)
		url = url + 'path=' + nodetools.urlEncode(path);

	return url;
};





oledDisplay.prototype.search = function (query) {
	var self=this;
	var defer=libQ.defer();

	// Mandatory, search. You can divide the search in sections using following functions

	return defer.promise;
};

oledDisplay.prototype._searchArtists = function (results) {

};

oledDisplay.prototype._searchAlbums = function (results) {

};

oledDisplay.prototype._searchPlaylists = function (results) {


};

oledDisplay.prototype._searchTracks = function (results) {

};
