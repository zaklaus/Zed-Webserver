'''
Zed webserver
Very basic model of working Webserver

	@name Zed
	@author ZaKlaus
	@version 1.0
	@imports socket,re,os
	@license MIT
'''

import socket as bs
import re
import os.path
import os

pathz = os.getcwd()
domain = ""
slashes = "\\"		# Linux/Unix - /, Windows - \\
mimelist = open(pathz+slashes+"mime.txt", 'r', encoding="utf-8").read()
mimemap = []
binarystate = False

print ("Zed Webserver")

print ("Building MIME map...")
for x in mimelist.split("\n"):
    try:
        mimemap.append([x.split(" ")[0][1:], x.split(" ")[1]])
    except IndexError: # plati pre prazdny riadok
        pass
print ("MIME map's been built!")
def LoadFile(fn):
    global binarystate
    print('File request: ', pathz+slashes+fn)
    try:
        f = open(pathz+slashes+fn,'r', encoding="utf-8")
        out = f.read()
        binarystate = False
    except:
        f = open(pathz+slashes+fn,'rb')
        out = f.read()
        binarystate = True
    f.close()
    return out

def BuildList():
	data = os.listdir(pathz)
	text = "<html><head><title>Files</title></head><body>Files:\n"
	for a in data:
		text += '<li><a href="http://'+domain+str(port)+'/'+a+'">'+a+'</a>' + '</li>'
	text += "</body></html>"
	return text
def WrapResult(out, params):
    return "HTTP/1.1 200 OK\nServer: ZaKok\n%sConnection: keep-alive\nContent-Type: %s\n\n%s" % (params[0], params[1], out);

def GetMIME(ext):
    global mimemap
    ext = ext[:-1]
    #print(str(len(ext)) + " vs. " + str(len(mimemap[0][0])))
    for x in range(len(mimemap)):
        #print(mimemap[x][0], " and fucking ", ext)
        if mimemap[x][0] == ext:
            return mimemap[x][1]
    return "null"

def Identify(var, op):
    if op == 's':
        print ("Content-Length: %d\n" % len(var))
        return "Content-Length: %d\n" % len(var)
    elif op == 't':
        #try:
            mime = GetMIME(var)
            if mime == "null":
                print("tak skoro? jewbe?")
                
            print ("Content-Type: %s" % mime)
            return mime
        except:
            print ("Unknown MIME type! Extension: %s" % var)
            return "text/html"

s = bs.socket()
host = ''
port = 7777
s.bind((host,port))

s.listen(666)
while True:
    c, addr = s.accept()
    print('Incoming connection from: ', addr)
    try:
        req = c.recv(1024)
    except:
        print("Connection error. Resetting...")
        s = bs.socket()
        s.bind((host,port))
        s.listen(666)
        continue
    
    #print (req)
    m = 0;
    fr = 0;

    try:
            domain = re.search('Host: (\S+):',req.decode(),re.DOTALL).group(0)[6:]
            m = re.search('/(\S+\.\S+)\s',req.decode(),re.DOTALL)
            fr = m.group(0)

            if fr.startswith("/1.1"):
                c.send(BuildList().encode())
                c.close()
                continue
    except:
            print('No URL specified! Assuming index.html')
            print(req)
            if not os.path.isfile(pathz+slashes+'index.html'):
                    c.send(BuildList().encode())
                    c.close()
                    continue
            c.send(WrapResult(LoadFile('index.html'), ("","text/html")).encode())
            c.close()
            continue

    print (fr)

    if not os.path.isfile(pathz+slashes+fr):
        c.send(WrapResult(LoadFile('404.html'), ("","text/html")).encode())
        c.close()
        continue

    cont = LoadFile(fr)
    ext = fr.split(".")[1]
    print(ext)
    if binarystate:
        out = cont
    else:
        out = WrapResult(cont, (Identify(cont, 's'),Identify(ext, 't'))).encode()
    
    c.send(out)

    c.close()
    print("Client is done!")
