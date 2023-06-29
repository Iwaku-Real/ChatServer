import socket,datetime,threading,mimetypes,time,unicodedata,os,traceback

clients={}
names={}
isAdmin={}

mCount=0
uCount=0

# Seriously, change this.
admin_pwd=b"OhioAmongUs"

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host=socket.gethostname()
port=1234
s.bind((host,port))
s.listen()
print(f"Server listening on:\nIP: {socket.gethostbyname(host)}\nPort: {port}")

def accept():
    while True:
        c,addr=s.accept()
        clients[c]=addr
        print(f"\n[{datetime.datetime.now()}] Client connected: {addr}")
        threading.Thread(target=client,args=(c,addr)).start()

def client(c,addr):
    try:
        global mCount,uCount,names,isAdmin,clients
        d=c.recv(1024)
        print(repr(d))
        if b"HTTP/1"in d:
            path=d.split()[1]
            if path==b"/":
                print("Client connected on web!\n")
                c.send(b"HTTP/1.1 200 OK\n")
                c.send(f"Content-Type: text/html\n".encode())
                c.send(b"Connection: close\n")
                data=open("index.html","rb").read()
                c.send(f"Content-Length: {len(data)}\n\n".encode())
                c.send(data)
            elif not path.isspace()and not path==b"":
                print('Web client performing request')
                path=path[1:].decode("utf8")
                print(f'{addr} requested file {path}')
                if os.path.exists(path)and path!="chat.py":
                    type=mimetypes.guess_type(path)
                    type=type if type[0]is not None else "application/octet-stream"
                    c.send(f"Content-Type: {type}\n".encode())
                    c.send(b"Connection: close\n")
                    data=open(path,"rb").read()
                    c.send(f"Content-Length: {len(data)}\n\n".encode())
                    c.send(data)
                else:
                    print("File doesn't exist!")
                    c.send(b'HTTP/1.1 404 Not Found\n\n')
                    c.send(b'<html><head><title>File not found!</title></head><body><h1>File not found!</h1></body></html>')
            c.close()
            return
        elif b"\xff\xfd" in d:
            c.send(b"Our server has migrated to a new client system.\r\nPlease go back to our website and download the new client program.\r\n")
            time.sleep(3)
            c.close()
            return
        elif d!=b'':
            sSend(c,b"Hello client!\r\n")
            n="\r\n"
            while n.isspace()or (n.rstrip().lstrip()in names.values())or("[admin]"in n.lower()):
                n=getClient(c,b"Please enter a username: ",128).decode("1252")
                if n=="!quit":return
                if (not n.isspace())and (n.rstrip().lstrip() not in names.values()):break
                sSend(c,b"Invalid username!\r\n")
            
            n=''.join(i for i in n if unicodedata.category(i)[0]!='C').lstrip().rstrip()
            broadcast(f"{n} has joined\r\n".encode(),"[SERVER] ")
            isAdmin[c]=False
            uCount=len(names)
            sSend(c,f"Welcome {n}!\r\n".encode())
            sSend(c,f"Current date/time: {datetime.datetime.now()}\r\n".encode())
            sSend(c,f"Users online: {uCount}\r\n".encode())
            sSend(c,b"Type `!help` for help.\r\n")
            sSend(c,b"You can always quit with `!quit`.\r\n")
            names[c]=n
    except Exception as err:
        error(c,addr,err)
    while True:
        try:
            msg=c.recv(2048)
            if not msg.startswith(b"!") and not msg.isspace()and msg!=b"":
                mCount+=1
                print(str(mCount)+": "+msg.decode("1252"))
                broadcast(msg, n+": ")
            elif msg.startswith(b"!help"):
                sSend(c,b'''
Current commands:\r\n\
!help         print this help message\r\n\
!msgcount     shows the total number of messages sent\r\n\
!usercount    shows the number of users online; when run with\r\n\
              `names` argument, prints list of users\r\n\
!address      prints your current IP address and port\r\n\
!quit         closes connection to this chat room\r\n''')
                c.send(b"[ENDSERVER]\r\n")
            elif msg==b"!msgcount":
                sSend(c,f"There have been {mCount} messages sent since the server started\r\n".encode())
            elif msg.startswith(b"!usercount"):
                if b"names" in msg.split():
                    sSend(c,b"List of users:\r\n")
                    for i in names.values():
                        sSend(c,i.encode()+b"\r\n")
                else:
                    sSend(c,f"There are currently {uCount} users online\r\n".encode())
            elif msg==b"!adlogin":
                p=getClient(c,b"Enter password: ",32)
                if p=="!quit":return
                if p==admin_pwd:
                    sSend(c,f"Welcome to the system, {n}. Have fun...\r\n".encode())
                    isAdmin[c]=True
                    n="[ADMIN] "+n
                    names[c]=n
                else:
                    sSend(c,b"Incorrect password!\r\n")
            elif msg==b"!address":
                sSend(c,f"Your IP address is: {addr[0]}\r\n".encode())
                sSend(c,f"Your port is: {addr[1]}\r\n".encode())
            elif msg==b"!error":
                raise SystemError
            elif msg==b"!quit":
                c.sendall(f"Thanks for joining {n}! See you again soon!".encode())
                time.sleep(0.5)
                c.close()
                del clients[c]
                del names[c]
                if uCount>0:uCount-=1
                broadcast(f"{n} has left".encode(),"[SERVER] ")
                break
            elif msg.startswith(b"!endserver"):
                if isAdmin[c]:
                    sSend(c,b"***WARNING: YOU ARE ABOUT TO SHUT DOWN THE SERVER***\r\n")
                    y=getClient(c,b"Proceed? (y/n) ",1)
                    if y==b"y":
                        names=[]
                        broadcast(b"***SERVER IS BEING SHUT DOWN***","[SERVER] ")
                        time.sleep(3)
                        broadcast(b"Done. You may now input or click 'X' to close this window.","[SERVER] ")
                        for s in clients:
                            s.close()
                        clients=[]
                        names=[]
                        os._exit(0)
                    else:
                        sSend(c,b"Aborted!\r\n")
                else:
                    sSend(c,b"You do not have privileges to run this command!\r\n")
        except Exception as e:
            error(c,addr,e)
            break

def getClient(c,prompt,size):
    sSend(c,prompt)
    resp=c.recv(size)
    if resp==b"!quit":
        error(c,(0,0),ConnectionAbortedError)
    return resp

def sSend(c,msg):
    c.send(b"[SERVER] "+msg)

def error(cli,addr,e):
    global clients, names, uCount
    tb=traceback.format_exc()
    cli.close()
    if cli in clients: del clients[cli]
    if cli in names: del names[cli]
    if uCount>0:uCount-=1
    if (not isinstance(e,ConnectionResetError))and(not isinstance(e,ConnectionAbortedError)):
        broadcast(b"***SERVER ERROR***","[SERVER] ")
        broadcast(f"Exception in thread for client {addr}!".encode(),"[SERVER] ")
        broadcast(b"\n"+tb.encode(),"[SERVER] ")
        broadcast(str(e).encode(),"[SERVER] ")
    exit(0)

def broadcast(msg,prefix=""):
    for s in clients:
        if s in names or prefix=="[SERVER] ":
          s.sendall(prefix.encode()+msg.strip(b"\r\n"))

acc_t = threading.Thread(target=accept)
acc_t.start()
acc_t.join()
s.close()