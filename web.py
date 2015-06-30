'''
Zed webserver
Very basic model of working Webserver

    @name Zed
    @author ZaKlaus
    @version 1.0
    @imports socket,re,os
    @license DWTF
'''

import socket as bs
import re
import os.path
import os
from threading import Thread

### Handles network communication
class Network:
    def __init__(self, host, port, conn):
        self.host = host
        self.port = port
        self.conn = conn
        
    def Listen(self):
        Network.sock = bs.socket()
        Network.sock.bind((self.host, self.port))
        Network.sock.listen(self.conn)

    def Receive(self, client, size):
        try:
            return client.recv(size)
        except ConnectionResetError:
            self.Listen()

    def Send(self, client, buf):
        try:
            client.send(buf)
        except ConnectionResetError:
            self.Listen()

    def Accept(self):
        try:
            return self.sock.accept()
        except:
            self.Listen()
            return None

    def Close(self):
        Network.sock.close()

### Handles IO and provides useful tools
class System:
    def __init__(self, pagedir, slash, maxthreads, network):
        self.basedir = os.getcwd() + slash
        self.pagedir = self.basedir + pagedir + slash
        self.maxthreads = maxthreads
        self.network = Network(network[0], network[1], network[2])
        self.mimemap = []
        self.threads = []
        
        print ("Zed Webserver -- 0.0.1")
        print ("Building MIME map...")
        mimelist = open(self.basedir + "mime.txt", 'r', encoding="utf-8").read()
        for x in mimelist.splitlines():
            try:
                self.mimemap.append([x.split(" ")[0][1:], x.split(" ")[1]])
            except IndexError:
                pass
        print ("MIME map's been built!")

        self.network.Listen()
        print ("Server is listening at %s:%d" %(self.network.host, self.network.port))

    def SetDomain(self, domain):
        self.domain = domain

    def GetDomain(self):
        return self.domain
    
    def LoadFile(self, filename):
        print('File request: ', self.pagedir + filename)
        try:
            f = open(self.pagedir + filename,'r', encoding="utf-8")
            out = f.read()
            self.binarystate = False
        except:
            f = open(self.pagedir + filename,'rb')
            out = f.read()
            self.binarystate = True
        f.close()
        return out

    def GetMIME(self, ext):
        ext = ext
        for x in range(len(self.mimemap)):
            if self.mimemap[x][0] == ext:
                return self.mimemap[x][1]
        return "null"

    def Tick_safe(self, client, address):
        print ("Incoming connection: ", address)

        request = Request(self, self.network.Receive(client, 1024))
        self.network.Send(client, request.send)

        self.network.Close()

    def Tick(self):
        if True:		# len(self.threads) < self.maxthreads:
            try:
                client, address = self.network.Accept()
            except:
                return
            thread = Thread(target=self.Tick_safe, args=(client, address))      
            self.threads.append(thread)
            thread.start()
        else:
            print ("Maximum connections reached!")

### Handles clients' requests and returns formatted response.
class Request:
    def __init__(self, system, data):
        self.system = system
        self.Proceed(data)

    def BuildList(self):
        data = os.listdir(self.system.pagedir)
        text = "<html><head><title>Files</title></head><body>Files:\n"
        for a in data:
            text += '<li><a href="http://'+self.domain+str(self.system.network.port)+'/'+a+'">'+a+'</a>' + '</li>'
        text += "</body></html>"
        return text

    def GenerateResponse(self, params):
        return "HTTP/1.1 200 OK\nServer: Zed Webserver\n%sConnection: keep-alive\nContent-Type: %s\n\n" % (params[0], params[1]);

    def Identify(self, var, op):
        if op == 's':
            print ("Content-Length: %d" % len(var))
            return "Content-Length: %d\n" % len(var)
        elif op == 't':
            try:
                mime = self.system.GetMIME(var)
                if mime == "null":
                    raise ValueError
                print ("Content-Type: %s" % mime)
                return mime
            except ValueError:
                print ("Unknown MIME type! Extension: %s" % var)
                return "text/html"

    def Proceed(self, data):
        try:
            try:
                self.domain = re.search('Host: (\S+):',data.decode(),re.DOTALL).group(0)[6:]
            except:
                try:
                    self.domain = re.search('Host: (\S+)\r\nD',data.decode(),re.DOTALL).group(0)[6:-5]
                except:
                    self.system.network.Listen()
                    return
            self.get = re.search('/(\S+\.\S+)\s',data.decode(),re.DOTALL).group(0)
            
            print ("GET '%s' FROM '%s'" % (self.get, self.domain))
            
            if self.get.startswith("/1.1"):
                raise ValueError
        except:
            print('No URL specified! Assuming index.html')
            if not os.path.isfile(self.system.pagedir + 'index.html'):
                print('index.html not found! Generating file tree...')
                self.data = self.BuildList()
                self.response = self.GenerateResponse(("", "text/html"))
                self.send = ("%s%s" % (self.response, self.data)).encode()
                return
            else:
                self.data = self.system.LoadFile('index.html')
                self.response = self.GenerateResponse(("", "text/html"))
                self.send = ("%s%s" % (self.response, self.data)).encode()
                return

        if not os.path.isfile(self.system.pagedir + self.get):
            self.data = self.system.LoadFile('404.html')
            self.response = self.GenerateResponse(("", "text/html"))
            self.send = ("%s%s" % (self.response, self.data)).encode()
            return

        else:
            self.data = self.system.LoadFile(self.get)
            self.extension = self.get.split(".")[1][:-1]

            if self.system.binarystate:
                self.response = ""
                self.send = self.data
            else:
                self.response = self.GenerateResponse((self.Identify(self.data, 's'), self.Identify(self.extension, 't')))
                self.send = ("%s%s" % (self.response, self.data)).encode()


main = System("page", '\\', 12, ("", 7777, 128))

while True:
    main.Tick()
