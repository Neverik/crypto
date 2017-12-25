from main import *
from flask import Flask
from rsa import newkeys
from requests import get
from rsa import PublicKey
import pickle
from flask import render_template
from requests import get

def encode(s):
    return codecs.encode(pickle.dumps(s), "base64").decode()
def decode(s):
    return pickle.loads(codecs.decode(s.encode(), "base64"))
def nice_print(s):
    return "From: " + s["from"] + ", to: " + s["to"] + ", amount: " + s["amount"] + ".\n"
def dup(seq):
   seen = {}
   result = []
   for item in seq:
       if item in seen: continue
       seen[item] = 1
       result.append(item)
   return result
def render(t):
    return render_template("temp.html", txt=t);

if __name__ == '__main__':
    app = Flask(__name__)

    diff = 4

    ledger = blockchain(4)
    contacts = ["127.0.0.1"]
    trans = []
    lastmined = 0
    port = 8080
    pub = None
    priv = None

    @app.route("/")
    def greeting():
        return render_template("index.html")

    @app.route("/update/")
    def update():
        global ledger
        t = []
        for a in contacts:
            b = get("http://" + a + ":5000/ledger/").text
            t.append(decode(b))
        m = -1000
        me = ledger
        for i in t:
            if i.verify() and i.diff == diff:
                if len(i.blocks) > m:
                    m = len(i.blocks)
                    me = i
        ledger = me

    @app.route("/add/<data>", methods = ['GET'])
    def add(data):
        global trans
        d = data.split("_")
        trans.append(block(pub, d[0], d[1], priv))
        return render("Successfully added!")

    @app.route("/see/")
    def see():
        global trans
        t = ""
        for i in trans:
            t += "§" + str(i)
        return t

    @app.route("/new/")
    def new():
        global pub
        global priv
        pair = newkeys(512)
        pub = pair[0]
        priv = pair[1]
        return render("Generated! Public: " + to_str(pub) + ". private: " + to_strp(priv))


    @app.route("/mine/")
    def mine():
        global lastmined
        forblocks = list(filter(lambda x: x.time > lastmined, gather()))
        print([x.time for x in forblocks])
        print(len(forblocks))
        for i,e in enumerate(forblocks):
            e.miner = pub
        for i in forblocks:
            ledger.add(i)
            ledger.blocks[-1].mine(ledger.diff)
            if not ledger.verify():
                ledger.blocks.pop()
        print([x.time for x in ledger.blocks])
        lastmined = time()
        ledger.lastmined = lastmined
        return render("Mined!")

    def gather():
        global contacts
        t = []
        for a in contacts:
            '''for i in decode(get("http://" + a + ":5000/contacts/").text):
                contacts += decode(get("http://" + a + ":5000/contacts/").text)
            contacts = dup(contacts)'''
            b = get("http://" + a + ":5000/see/").text
            for i in b.split("§"):
                if i != '':
                    t.append(i)
        t = [block.from_str(i) for i in t]
        t.sort(key=lambda x: x.time)
        return t

    @app.route("/ledger/")
    def led():
        return encode(ledger.blocks)

    @app.route("/contacts/")
    def cont():
        global contacts
        return encode(contacts)

    @app.route("/all/")
    def al():
        t = ""
        for i in ledger.blocks:
            print(nice_print(i.data))
            t += nice_print(i.data)
        return render(t)

    @app.route("/cont/<key>/")
    def con(key):
        global contacts
        contacts.append(key)
        contacts = dup(contacts)
        return render("Added!")

    app.run(threaded=True)
