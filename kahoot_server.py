from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)

# QUESTIONS
questions = [
    {"q": "What is phishing?",
     "options": ["Fake email attack", "Firewall", "Game", "Cable"],
     "answer": 0},

    {"q": "What is malware?",
     "options": ["Virus software", "Safe app", "Keyboard", "Monitor"],
     "answer": 0}
]

players = {}
current_q = -1
timer_running = False

# PLAYER PAGE
PLAYER_HTML = """
<body style="background:black;color:lime;text-align:center;font-family:monospace;">
<h1>Cyber Challenge</h1>

<input id="name" placeholder="Enter name">
<button onclick="join()">Join</button>

<div id="game" style="display:none;">
    <h2 id="timer"></h2>
    <h3 id="question"></h3>
    <div id="options"></div>
    <h2 id="result"></h2>
</div>

<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
<script>
var socket = io();
var player="";

function join(){
    player = document.getElementById("name").value;
    socket.emit("join", player);
    document.getElementById("game").style.display="block";
}

socket.on("question", function(data){
    document.getElementById("result").innerHTML="";
    document.getElementById("question").innerHTML = data.q;

    let html="";
    data.options.forEach((o,i)=>{
        html += `<button onclick="send(${i})">${o}</button><br><br>`;
    });
    document.getElementById("options").innerHTML = html;
});

socket.on("timer", function(t){
    document.getElementById("timer").innerHTML = "Time: "+t;
});

socket.on("correct", function(ans){
    document.getElementById("result").innerHTML = "Correct Answer: "+ans;
});

function send(i){
    socket.emit("answer", {name:player, ans:i});
}
</script>
</body>
"""

# HOST PAGE
HOST_HTML = """
<body style="background:black;color:lime;text-align:center;font-family:monospace;">
<h1>HOST PANEL</h1>

<button onclick="start()">Start Game</button>

<h2>Leaderboard</h2>
<div id="players"></div>

<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
<script>
var socket = io();

function start(){
    socket.emit("start");
}

socket.on("players", function(data){
    let html="";
    for(let p in data){
        html += p + " : " + data[p] + "<br>";
    }
    document.getElementById("players").innerHTML = html;
});
</script>
</body>
"""

@app.route("/")
def player():
    return render_template_string(PLAYER_HTML)

@app.route("/host")
def host():
    return render_template_string(HOST_HTML)

# SOCKET EVENTS

@socketio.on("join")
def join(name):
    players[name] = 0
    emit("players", players, broadcast=True)

@socketio.on("start")
def start_game():
    global current_q
    current_q = 0
    socketio.start_background_task(run_quiz)

def run_quiz():
    global current_q

    while current_q < len(questions):

        q = questions[current_q]
        socketio.emit("question", q)

        # TIMER 10s
        for t in range(10,0,-1):
            socketio.emit("timer", t)
            eventlet.sleep(1)

        # SHOW CORRECT ANSWER
        correct = q["options"][q["answer"]]
        socketio.emit("correct", correct)

        eventlet.sleep(3)

        current_q += 1

    socketio.emit("players", players)

@socketio.on("answer")
def answer(data):
    name = data["name"]
    ans = data["ans"]

    if questions[current_q]["answer"] == ans:
        players[name] += 1

    socketio.emit("players", players)

# RUN
socketio.run(app, host="0.0.0.0", port=5000)