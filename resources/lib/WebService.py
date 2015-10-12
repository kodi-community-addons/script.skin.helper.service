import SimpleHTTPServer, BaseHTTPServer, httplib
import threading
import thread
import json
import os
import sys
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import xbmcvfs
import urllib
from Utils import *
port = 8888

class WebService(threading.Thread):
    event = None
    exit = False
    
    def __init__(self, *args):
        logMsg("WebService - started",0)
        self.event =  threading.Event()
        threading.Thread.__init__(self, *args)
    
    def stop(self):
        logMsg("WebService - stop called",0)
        conn = httplib.HTTPConnection("localhost:%d" % port)
        conn.request("QUIT", "/")
        conn.getresponse()
        self.exit = True
        self.event.set()

    def run(self):
        server = StoppableHttpServer(('localhost', port), StoppableHttpRequestHandler)
        server.serve_forever()


class Request(object):
    # attributes from urlsplit that this class also sets
    uri_attrs = ('scheme', 'netloc', 'path', 'query', 'fragment')
  
    def __init__(self, uri, headers, rfile=None):
        self.uri = uri
        self.headers = headers
        parsed = urlparse.urlsplit(uri)
        for i, attr in enumerate(self.uri_attrs):
            setattr(self, attr, parsed[i])
        try:
            body_len = int(self.headers.get('Content-length', 0))
        except ValueError:
            body_len = 0
        if body_len and rfile:
            self.body = rfile.read(body_len)
        else:
            self.body = None

        
class StoppableHttpRequestHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):
    """http request handler with QUIT stopping the server"""
    
    def __init__(self, request, client_address, server):
        try:
            SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
        except Exception as e: logMsg("WebServer error occurred " + str(e))
    
    def do_QUIT (self):
        """send 200 OK response, and set server.stop to True"""
        self.send_response(200)
        self.end_headers()
        self.server.stop = True
    
    def log_message(self, format, *args):
        logMsg("Webservice --> %s - - [%s] %s\n" %(self.address_string(),self.log_date_time_string(),format%args))
    
    def parse_request(self):
        #hack to accept non url encoded strings to pass listitem details from Kodi to webservice
        if ("GET /getthumb" in self.raw_requestline or "HEAD /getthumb" in self.raw_requestline) and not "%20" in self.raw_requestline and "title=" in self.raw_requestline and "channel=" in self.raw_requestline:
            if self.raw_requestline.startswith("HEAD"): command = "HEAD /getthumb"
            else: command = "GET /getthumb"
            self.raw_requestline = self.raw_requestline.replace(command,"").replace(" HTTP/1.1","")
            title = self.raw_requestline.split("&channel=")[0].replace("&title=","")
            channel = self.raw_requestline.split("&channel=")[1].replace("\r\n","")
            type = None
            if "&type=" in channel:
                channeltemp = channel
                channel = channeltemp.split("&type=")[0]
                type = "&type=" + channeltemp.split("&type=")[1]           
            title = single_urlencode(try_encode(title))
            channel = single_urlencode(try_encode(channel))
            if type:
                self.raw_requestline = "%s&title=%s&channel=%s&type=%s HTTP/1.1" %(command,title,channel,type)
            else:
                self.raw_requestline = "%s&title=%s&channel=%s HTTP/1.1" %(command,title,channel)
        retval = SimpleHTTPServer.SimpleHTTPRequestHandler.parse_request(self)
        self.request = Request(self.path, self.headers, self.rfile)
        return retval
    
    def do_HEAD(self):
        image = self.send_headers()
        if image: image.close()
        return
    
    def send_headers(self):
        image = None
        preferred_type = None
        params = urlparse.parse_qs(self.path)       
        title = params.get("title","")
        channel = params.get("channel","")
        preferred_type = params.get("type","")
        if title: title = title[0].decode("utf-8")
        if channel: channel = channel[0].decode("utf-8")
        if preferred_type: preferred_type = preferred_type[0]        
        if title and title != "..":
            if xbmc.getCondVisibility("Window.IsActive(MyPVRRecordings.xml)"): type = "recordings"
            else: type = "channels"
            artwork = getPVRThumbs(title, channel, type)
            if preferred_type:
                image = artwork.get(preferred_type)
            else:
                if artwork.get("thumb"): image = artwork.get("thumb")
                if artwork.get("fanart"): image = artwork.get("fanart")
                if artwork.get("landscape"): image = artwork.get("landscape")
        if image:
            self.send_response(200)
            self.send_header('Content-type','image/png')
            self.send_header('Last-Modified',WINDOW.getProperty("SkinHelper.lastUpdate"))
            logMsg("found image for request %s  --> %s" %(try_encode(self.path),try_encode(image)))
            image = xbmcvfs.File(image)
            size = image.size()
            self.send_header('Content-Length',str(size))
            self.end_headers() 
        else:
            self.send_error(404)
        return image

    def do_GET(self):
        image = self.send_headers()
        if image:
            #send the image to the client
            logMsg("WebService -- sending image for --> " + try_encode(self.path))
            self.wfile.write(image.readBytes())
            image.close()
        return

class StoppableHttpServer (BaseHTTPServer.HTTPServer):
    """http server that reacts to self.stop flag"""

    def serve_forever (self):
        """Handle one request at a time until stopped."""
        self.stop = False
        while not self.stop:
            self.handle_request()


def stop_server (port):
    """send QUIT request to http server running on localhost:<port>"""
    conn = httplib.HTTPConnection("localhost:%d" % port)
    conn.request("QUIT", "/")
    conn.getresponse()
   