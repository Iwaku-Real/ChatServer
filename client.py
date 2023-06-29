from socket import AF_INET, socket, SOCK_STREAM, error
from threading import Thread
import tkinter,time
from os import _exit

def receive():
    global connected
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            for i in msg.strip("\r").split("\n"):
                if i!='':
                    msg_list.insert(tkinter.END, i)
            msg_list.see("end")
        except Exception as e:
            fail_connect(e)
            break

def settheme(bg,fg):
    global top, messages_frame
    for w in[top,messages_frame]+top.winfo_children()+messages_frame.winfo_children():
        if'bg'in w.config():
            w.config(bg=bg)
        if'fg'in w.config():
            w.config(fg=fg)

def send(event=None):
    msg = my_msg.get()
    my_msg.set("")
    try:
        client_socket.send(bytes(msg, "utf8"))
    except Exception as e:
        fail_connect(e)
    else:
        if msg == "!quit":
            time.sleep(0.5)
            endclient()
        elif msg == "!hackertheme":
            settheme("black","lightgreen")
        elif msg =="!defaulttheme":
            settheme("white","black")

# Default host and port (change this to anywhere else the server is being hosted)
HOST = "193.161.193.99"
PORT = 46398
BUFSIZ = 1024
ADDR = (HOST, PORT)

top = tkinter.Tk()
top.title("Chat")
top.geometry("700x400")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()
my_msg.set("")
scrollbarX = tkinter.Scrollbar(messages_frame,orient="horizontal")
scrollbarY = tkinter.Scrollbar(messages_frame)

msg_list = tkinter.Listbox(messages_frame, font="Courier", xscrollcommand=scrollbarX.set, yscrollcommand=scrollbarY.set)
scrollbarX.pack(side=tkinter.BOTTOM, fill=tkinter.X)
scrollbarY.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH,expand=True)
messages_frame.pack(fill=tkinter.BOTH,expand=True)

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack(fill=tkinter.X)
send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()

client_socket = socket(AF_INET, SOCK_STREAM)

connected=False

def endclient(event=None):
    client_socket.close()
    top.destroy()
    _exit(0)

top.protocol("WM_DELETE_WINDOW", endclient)

def fail_connect(e):
    global connected
    top.withdraw()
    client_socket.close()
    connected=False
    print("Can't connect!")
    print(e)
    begin()

def try_connect():
    print("Connecting...")
    global connected,client_socket,ADDR
    while not connected:
        try:
            client_socket = socket(AF_INET, SOCK_STREAM)
            client_socket.connect(ADDR)
            connected=True
            print("Successfully connected!")
            client_socket.send(b"Client here!\r\n")
            top.deiconify()
        except error:
            print("Failed to connect! Retrying...")
            time.sleep(3)
        except KeyboardInterrupt:
            _exit(0)

def begin():
    global client_socket,msg_list
    msg_list.delete(0,'end')
    try_connect()
    print("A window should have opened, check your taskbar")
    receive_thread = Thread(target=receive)
    receive_thread.start()

begin()

tkinter.mainloop()