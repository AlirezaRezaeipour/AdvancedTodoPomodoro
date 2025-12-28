import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime, time, date
from zoneinfo import ZoneInfo
import json
import os

# ================== Settings ==================
DARK_BG = "#0f172a"
CARD_BG = "#1e293b"
TEXT_COLOR = "#e5e7eb"
ACCENT = "#38bdf8"
BTN_BG = "#334155"

TASK_FILE = "tasks.json"
POMO_FILE = "pomodoro_tasks.json"
HISTORY_FILE = "history.json"

COUNTRIES = {
    "Iran 🇮🇷": "Asia/Tehran",
    "USA 🇺🇸": "America/New_York",
    "UK 🇬🇧": "Europe/London",
    "Germany 🇩🇪": "Europe/Berlin",
    "Japan 🇯🇵": "Asia/Tokyo",
}

# ================== File Utilities ==================
def load_file(name, default=[]):
    if os.path.exists(name):
        with open(name,"r") as f:
            return json.load(f)
    return default

def save_file(name, data):
    with open(name,"w") as f:
        json.dump(data, f, indent=4)

# ================== Data ==================
tasks = load_file(TASK_FILE, [])
pomo_tasks = load_file(POMO_FILE, [])
history = load_file(HISTORY_FILE, {})

# ================== Window ==================
root = tk.Tk()
root.title("Advanced ToDo & Pomodoro")
root.geometry("950x650")
root.configure(bg=DARK_BG)

selected_country = tk.StringVar(value="Iran 🇮🇷")
mode = tk.StringVar(value="todo")  # todo | pomo

# ================== Header ==================
header = tk.Frame(root, bg=DARK_BG)
header.pack(fill="x", pady=5)

# Title
tk.Label(header, text="🗂 Pro Productivity", fg=TEXT_COLOR, bg=DARK_BG, font=("Segoe UI",16,"bold")).pack(side="left", padx=10)

# Mode Switch
def switch_mode():
    mode.set("pomo" if mode.get()=="todo" else "todo")
    render()

tk.Button(header, text="🔁 Switch Mode", bg=ACCENT, fg="black", command=switch_mode).pack(side="right", padx=10)

# ================== Remaining Time ==================
time_label = tk.Label(root, fg=TEXT_COLOR, bg=DARK_BG, font=("Segoe UI",11))
time_label.pack(pady=5)

def update_remaining_time():
    tz = ZoneInfo(COUNTRIES[selected_country.get()])
    now = datetime.now(tz)
    midnight = datetime.combine(now.date(), time(23,59,59), tz)
    remain = midnight - now
    sec = int(remain.total_seconds())
    if sec <=0:
        today = date.today().isoformat()
        total = sum(t['elapsed'] for t in tasks)
        history[today] = total
        save_file(HISTORY_FILE, history)
    else:
        h,r = divmod(sec,3600)
        m,_ = divmod(r,60)
        time_label.config(text=f"⏰ Time left today {selected_country.get()}: {h}h {m}m")
    root.after(60000, update_remaining_time)

# ================== Content ==================
content = tk.Frame(root, bg=DARK_BG)
content.pack(fill="both", expand=True)

# ================== ToDo ==================
def render_todo():
    for w in content.winfo_children(): w.destroy()
    box = tk.Frame(content, bg=CARD_BG)
    box.pack(padx=20, pady=20, fill="both", expand=True)

    def add_task():
        t = simpledialog.askstring("Add Task", "Task title:")
        if t:
            tasks.append({"title":t,"done":False,"elapsed":0,"running":False})
            save_file(TASK_FILE, tasks)
            render()

    tk.Button(box, text="➕ Add Task", bg=ACCENT, fg="black", command=add_task).pack(pady=10)

    for task in tasks:
        row = tk.Frame(box, bg=BTN_BG)
        row.pack(fill="x", padx=10, pady=4)
        lbl = tk.Label(row, text=task["title"], fg=TEXT_COLOR, bg=BTN_BG)
        lbl.pack(side="left", padx=8)
        lbl.bind("<Button-1>", lambda e, t=task: toggle_done(t))

        timer_lbl = tk.Label(row, text=f"{task['elapsed']}s", fg=TEXT_COLOR, bg=BTN_BG)
        timer_lbl.pack(side="right", padx=6)

        tk.Button(row, text="⟳", width=3, command=lambda t=task: reset_task(t), bg=ACCENT).pack(side="right", padx=2)
        btn = tk.Button(row, text="▶", width=3)
        btn.pack(side="right", padx=2)
        btn.config(command=lambda t=task, l=timer_lbl, b=btn: start_pause(t,l,b))
        tk.Button(row, text="✏", width=3, command=lambda t=task: edit_task(t), bg=ACCENT).pack(side="right", padx=2)
        tk.Button(row, text="🗑", width=3, command=lambda t=task: delete_task(t), bg=ACCENT).pack(side="right", padx=2)

    update_total_time()

# ================== Task Operations ==================
def toggle_done(task):
    task['done'] = not task['done']
    save_file(TASK_FILE,tasks)
    render()

def edit_task(task):
    new = simpledialog.askstring("Edit Task","Edit task:",initialvalue=task['title'])
    if new:
        task['title']=new
        save_file(TASK_FILE,tasks)
        render()

def delete_task(task):
    if messagebox.askyesno("Delete", f"Delete '{task['title']}'?"):
        tasks.remove(task)
        save_file(TASK_FILE,tasks)
        render()

def reset_task(task):
    task['elapsed']=0
    task['running']=False
    save_file(TASK_FILE,tasks)
    render()

def start_pause(task,lbl,btn):
    task['running']=not task['running']
    btn.config(text="⏸" if task['running'] else "▶")
    if task['running']:
        run_timer(task,lbl,btn)

def run_timer(task,lbl,btn):
    if task['running']:
        task['elapsed']+=1
        lbl.config(text=f"{task['elapsed']}s")
        update_total_time()
        root.after(1000, lambda: run_timer(task,lbl,btn))

# ================== Total Time ==================
total_lbl = tk.Label(root, fg=TEXT_COLOR, bg=DARK_BG, font=("Segoe UI",12))
total_lbl.pack(pady=6)

def update_total_time():
    total = sum(t['elapsed'] for t in tasks)
    total_lbl.config(text=f"📊 Total Time: {total}s")

def reset_total():
    for t in tasks:
        t['elapsed']=0
        t['running']=False
    save_file(TASK_FILE,tasks)
    render()

# ================== Pomodoro ==================
current_timer = {'running':False,'sec':1500}

def render_pomo():
    for w in content.winfo_children(): w.destroy()
    box = tk.Frame(content, bg=CARD_BG)
    box.pack(padx=20,pady=20,fill="both",expand=True)

    timer_lbl = tk.Label(box, fg=TEXT_COLOR, bg=CARD_BG, font=("Segoe UI",36,"bold"))
    timer_lbl.pack(pady=20)

    def update_timer():
        if current_timer['running'] and current_timer['sec']>0:
            current_timer['sec']-=1
            m,s=divmod(current_timer['sec'],60)
            timer_lbl.config(text=f"{m:02}:{s:02}")
            root.after(1000,update_timer)

    def start():
        current_timer['running']=True
        update_timer()

    def reset():
        current_timer['running']=False
        current_timer['sec']=1500
        timer_lbl.config(text="25:00")

    timer_lbl.config(text="25:00")
    btns = tk.Frame(box, bg=CARD_BG)
    btns.pack()
    tk.Button(btns, text="▶ Start", bg=ACCENT, command=start).pack(side="left", padx=5)
    tk.Button(btns, text="⟲ Reset", bg=BTN_BG, fg=TEXT_COLOR, command=reset).pack(side="left", padx=5)

# ================== Render ==================
def render():
    if mode.get()=="todo":
        render_todo()
    else:
        render_pomo()

# ================== Top Buttons ==================
top = tk.Frame(root, bg=DARK_BG)
top.pack(pady=6)

tk.Button(top, text="Select Country", width=16, bg=ACCENT, command=lambda: select_country_window()).pack(side="left", padx=4)
tk.Label(top, textvariable=selected_country, fg=TEXT_COLOR, bg=DARK_BG).pack(side="left", padx=6)
tk.Button(top, text="Reset Total", width=12, command=reset_total, bg=ACCENT).pack(side="left", padx=4)

# ================== Country Selection ==================
def select_country_window():
    win=tk.Toplevel(root)
    win.title("Select Country")
    win.geometry("260x300")
    lb=tk.Listbox(win,font=("Segoe UI",13))
    lb.pack(fill="both",expand=True,padx=10,pady=10)
    for c in COUNTRIES: lb.insert(tk.END,c)
    def choose():
        if lb.curselection():
            selected_country.set(lb.get(lb.curselection()))
            update_remaining_time()
            win.destroy()
    tk.Button(win,text="Select",command=choose).pack(pady=5)

update_remaining_time()
render()
root.mainloop()
