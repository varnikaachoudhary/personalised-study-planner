# ------------------------------------------------------------
#              PERSONALISED STUDY PLANNER
#       Final Clean Single-File Version (Complete)
# ------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, Menu
import json, csv, os
from datetime import date, timedelta

# -------- Optional PDF Export ----------
try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except:
    REPORTLAB_AVAILABLE = False

# -------- Optional Calendar View --------
try:
    from tkcalendar import Calendar
    TKCALENDAR_AVAILABLE = True
except:
    TKCALENDAR_AVAILABLE = False

# ---------------- CONSTANTS ----------------
DATA_JSON   = "study_data.json"
NOTES_FILE  = "study_notes.txt"

# ---------------- ROOT WINDOW ----------------
root = tk.Tk()
root.title("Personalised Study Planner")
root.geometry("1050x700")
root.configure(bg="white")

# ---------------- VARIABLES ----------------
current_view = tk.StringVar(value="table")   # table / calendar
theme_mode   = tk.StringVar(value="light")   # light / dark
schedule     = []                             # Global schedule list

# ---------------- TOP FRAME ----------------
top_frame = tk.Frame(root, bg="white")
top_frame.pack(fill="x", pady=6)

content_frame = tk.Frame(root, bg="white")
content_frame.pack(fill="both", expand=True)

footer_frame = tk.Frame(root, bg="white")
footer_frame.pack(fill="x")

status_label = tk.Label(root, text="Ready.", bg="#EEEEEE", anchor="w", relief="sunken")
status_label.pack(fill="x", side="bottom")

# ---------------- HELPERS ----------------
def parse_list(s):
    return [i.strip() for i in s.split(",") if i.strip()]

# ---------------- INPUT FIELDS ----------------
tk.Label(top_frame, text="Subjects:", bg="white").grid(row=0, column=0, sticky="w", padx=5)
subject_entry = tk.Entry(top_frame, width=25)
subject_entry.grid(row=0, column=1, padx=5)

tk.Label(top_frame, text="Topic counts:", bg="white").grid(row=0, column=2, sticky="w", padx=5)
topics_entry = tk.Entry(top_frame, width=20)
topics_entry.grid(row=0, column=3, padx=5)

tk.Label(top_frame, text="Study Days:", bg="white").grid(row=1, column=0, sticky="w", padx=5)
days_entry = tk.Entry(top_frame, width=10)
days_entry.grid(row=1, column=1, padx=5)

tk.Label(top_frame, text="Hours/day (optional):", bg="white").grid(row=1, column=2, sticky="w", padx=5)
hours_entry = tk.Entry(top_frame, width=10)
hours_entry.grid(row=1, column=3, padx=5)


# ---------------- THEME FUNCTION ----------------
def apply_theme(mode):
    bg = "#1E1E1E" if mode=="dark" else "white"
    fg = "white" if mode=="dark" else "black"

    root.configure(bg=bg)
    top_frame.configure(bg=bg)
    content_frame.configure(bg=bg)
    footer_frame.configure(bg=bg)
    status_label.configure(bg="#333333" if mode=="dark" else "#EEEEEE", fg=fg)

theme_box = ttk.OptionMenu(top_frame, theme_mode, "light", "light", "dark", command=lambda m: apply_theme(theme_mode.get()))
theme_box.grid(row=0, column=4, padx=10)


# ---------------- VIEW SELECTOR ----------------
tk.Label(top_frame, text="View:", bg="white").grid(row=1, column=4, sticky="w", padx=5)

view_box = ttk.OptionMenu(
    top_frame,
    current_view,
    "table",
    "table",
    "calendar",
    command=lambda m: switch_view()
)
view_box.grid(row=1, column=5, padx=10)

apply_theme("light")

# ---------------- TABLE VIEW ----------------
schedule_tree = None

def create_table_view(parent):
    global schedule_tree
    frame = tk.Frame(parent)
    frame.pack(fill="both", expand=True)

    cols = ("Day","Date","Subject","Topic","Status")
    schedule_tree = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        schedule_tree.heading(c, text=c)
        schedule_tree.column(c, width=160, anchor="center")

    schedule_tree.pack(fill="both", expand=True)

# Load table initially
create_table_view(content_frame)


# ---------------- PROGRESS BAR ----------------
progress_label = tk.Label(footer_frame, text="Progress: 0% (0/0)", bg="white")
progress_label.pack(side="left", padx=6)

progressbar = ttk.Progressbar(footer_frame, length=300, mode="determinate")
progressbar.pack(side="left", padx=10)


# ---------------- SCHEDULE FUNCTIONS ----------------
def update_progress():
    if not schedule:
        progress_label.config(text="Progress: 0% (0/0)")
        progressbar["value"] = 0
        return

    total = len(schedule)
    completed = sum(1 for s in schedule if s["Status"]=="Completed")
    pct = (completed/total)*100

    progress_label.config(text=f"Progress: {pct:.2f}% ({completed}/{total})")
    progressbar["value"] = pct


def refresh_tree():
    schedule_tree.delete(*schedule_tree.get_children())
    for item in schedule:
        schedule_tree.insert("", "end", values=(
            item["Day"], item["Date"], item["Subject"], item["Topic"], item["Status"]
        ))
    update_progress()


def generate_schedule():
    global schedule
    subjects = parse_list(subject_entry.get())
    topic_counts_raw = parse_list(topics_entry.get())

    try:
        topic_counts = list(map(int, topic_counts_raw))
    except:
        messagebox.showerror("Error", "Invalid topic counts")
        return

    if len(subjects) != len(topic_counts):
        messagebox.showerror("Error", "Subjects & topic count mismatch")
        return

    try:
        days = int(days_entry.get())
    except:
        messagebox.showerror("Error", "Invalid study days")
        return

    schedule = []
    all_slots = []

    for i, subj in enumerate(subjects):
        for t in range(1, topic_counts[i]+1):
            all_slots.append((subj, t))

    per_day = len(all_slots)//days
    extra = len(all_slots)%days

    today = date.today()
    idx = 0

    for d in range(1, days+1):
        num = per_day + (1 if d<=extra else 0)
        for _ in range(num):
            if idx >= len(all_slots):
                break
            subj, tno = all_slots[idx]
            schedule.append({
                "Day": f"Day {d}",
                "Date": (today + timedelta(days=d-1)).strftime("%d-%m-%Y"),
                "Subject": subj,
                "Topic": f"Topic {tno}",
                "Status": "Pending"
            })
            idx += 1

    refresh_tree()
    status_label.config(text="Schedule generated.")


# ---------------- TOGGLE STATUS ----------------
def toggle_status():
    selected = schedule_tree.selection()
    if not selected:
        return
    for i, sel in enumerate(selected):
        values = schedule_tree.item(sel)["values"]
        idx = schedule_tree.index(sel)
        schedule[idx]["Status"] = "Completed" if schedule[idx]["Status"]=="Pending" else "Pending"
    refresh_tree()


# ---------------- SAVE / LOAD ----------------
def save_plan():
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=4)
    messagebox.showinfo("Saved", "Plan saved!")

def load_plan():
    global schedule
    if not os.path.exists(DATA_JSON):
        return
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        schedule = json.load(f)
    refresh_tree()
    messagebox.showinfo("Loaded", "Plan loaded!")


# ---------------- CALENDAR VIEW ----------------
calendar_frame = None
calendar_widget = None

def create_calendar_view(parent):
    global calendar_frame, calendar_widget
    calendar_frame = tk.Frame(parent, bg="white")

    if TKCALENDAR_AVAILABLE:
        left = tk.Frame(calendar_frame, bg="white")
        left.pack(side="left", padx=10)

        cal = Calendar(left)
        cal.pack(pady=10)
        calendar_widget = cal

        right = tk.Frame(calendar_frame, bg="white")
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Topics for Selected Date:", bg="white").pack(anchor="w")
        topic_list = tk.Listbox(right)
        topic_list.pack(fill="both", expand=True)

        def update_list(event=None):
            sel = cal.selection_get().strftime("%d-%m-%Y")
            topic_list.delete(0, "end")
            for s in schedule:
                if s["Date"] == sel:
                    topic_list.insert("end", f"{s['Subject']} - {s['Topic']} ({s['Status']})")

        cal.bind("<<CalendarSelected>>", update_list)
    else:
        tk.Label(calendar_frame, text="tkcalendar not installed", bg="white").pack()

    return calendar_frame


calendar_view = create_calendar_view(content_frame)


# ---------------- SWITCH VIEW ----------------
def switch_view():
    for widget in content_frame.winfo_children():
        widget.pack_forget()

    if current_view.get() == "table":
        schedule_tree.pack(fill="both", expand=True)
    else:
        calendar_view.pack(fill="both", expand=True)


# ---------------- NOTES WINDOW ----------------
def open_notes():
    win = tk.Toplevel(root)
    win.title("Notes")
    win.geometry("500x500")

    txt = tk.Text(win)
    txt.pack(fill="both", expand=True)

    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            txt.insert("1.0", f.read())

    def save_notes():
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            f.write(txt.get("1.0", "end"))
        messagebox.showinfo("Saved", "Notes saved!")

    tk.Button(win, text="Save Notes", command=save_notes).pack(pady=5)


# ---------------- AUTO SHIFT MISSED ----------------
def auto_shift():
    today_str = date.today().strftime("%d-%m-%Y")
    for s in schedule:
        if s["Status"]=="Pending" and s["Date"] < today_str:
            s["Date"] = today_str
    refresh_tree()
    messagebox.showinfo("Done", "Missed topics shifted!")


# ---------------- EXPORT CSV ----------------
def export_csv():
    if not schedule:
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    if not file:
        return

    with open(file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Day","Date","Subject","Topic","Status"])
        for s in schedule:
            w.writerow([s["Day"], s["Date"], s["Subject"], s["Topic"], s["Status"]])

    messagebox.showinfo("CSV", "Exported successfully!")


# ---------------- EXPORT PDF ----------------
def export_pdf():
    if not REPORTLAB_AVAILABLE:
        messagebox.showerror("Missing", "reportlab not installed!")
        return

    file = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not file:
        return

    doc = SimpleDocTemplate(file, pagesize=A4)
    data = [["Day","Date","Subject","Topic","Status"]]
    for s in schedule:
        data.append([s["Day"], s["Date"], s["Subject"], s["Topic"], s["Status"]])

    table = Table(data)
    table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.grey)]))
    doc.build([table])
    messagebox.showinfo("PDF", "PDF exported!")


# ---------------- SUMMARY WINDOW ----------------
def open_summary():
    win = tk.Toplevel(root)
    win.title("Summary")
    win.geometry("400x300")

    stats = {}

    for s in schedule:
        subj = s["Subject"]
        if subj not in stats:
            stats[subj]={"Total":0,"Completed":0,"Pending":0}

        stats[subj]["Total"] += 1
        if s["Status"]=="Completed":
            stats[subj]["Completed"] += 1
        else:
            stats[subj]["Pending"] += 1

    cols = ("Subject","Total","Completed","Pending")
    tv = ttk.Treeview(win, columns=cols, show="headings")
    for c in cols:
        tv.heading(c, text=c)
        tv.column(c, width=100)

    for k,v in stats.items():
        tv.insert("", "end", values=(k, v["Total"], v["Completed"], v["Pending"]))

    tv.pack(fill="both", expand=True)


# ---------------- FOOTER BUTTONS ----------------
btn_frame = tk.Frame(footer_frame, bg="white")
btn_frame.pack(side="right")

tk.Button(btn_frame, text="Generate", command=generate_schedule, bg="#BDE0FE").grid(row=0, column=0, padx=4)
tk.Button(btn_frame, text="Toggle Status", command=toggle_status, bg="#FFD166").grid(row=0, column=1, padx=4)
tk.Button(btn_frame, text="Save", command=save_plan, bg="#A7F3D0").grid(row=0, column=2, padx=4)
tk.Button(btn_frame, text="Load", command=load_plan, bg="#FECACA").grid(row=0, column=3, padx=4)
tk.Button(btn_frame, text="Auto-Shift", command=auto_shift, bg="#D8B4FE").grid(row=0, column=4, padx=4)
tk.Button(btn_frame, text="Notes", command=open_notes, bg="#FEF3C7").grid(row=0, column=5, padx=4)
tk.Button(btn_frame, text="Export CSV", command=export_csv, bg="#BAE6FD").grid(row=0, column=6, padx=4)
tk.Button(btn_frame, text="Export PDF", command=export_pdf, bg="#C7EFCF").grid(row=0, column=7, padx=4)
tk.Button(btn_frame, text="Summary", command=open_summary, bg="#FFE699").grid(row=0, column=8, padx=4)


# ---------------- MENUBAR ----------------
menubar = Menu(root)

file_m = Menu(menubar, tearoff=0)
file_m.add_command(label="New Plan", command=lambda: schedule.clear() or refresh_tree())
file_m.add_command(label="Load Plan", command=load_plan)
file_m.add_command(label="Save Plan", command=save_plan)
file_m.add_separator()
file_m.add_command(label="Export CSV", command=export_csv)
file_m.add_command(label="Export PDF", command=export_pdf)
file_m.add_separator()
file_m.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_m)

tools_m = Menu(menubar, tearoff=0)
tools_m.add_command(label="Notes", command=open_notes)
tools_m.add_command(label="Auto-shift", command=auto_shift)
tools_m.add_command(label="Summary", command=open_summary)
menubar.add_cascade(label="Tools", menu=tools_m)

help_m = Menu(menubar, tearoff=0)
help_m.add_command(label="About", command=lambda: messagebox.showinfo("About","Study Planner by Varnika"))
menubar.add_cascade(label="Help", menu=help_m)

root.config(menu=menubar)

root.mainloop()
