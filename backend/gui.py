import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import db
import auth


def launch_gui():
    root = tk.Tk()
    root.title("Backend Admin GUI")

    def choose_root():
        path = filedialog.askdirectory()
        if path:
            db.ROOT_DIR = path
            db.init_db()
            messagebox.showinfo("Saved", f"Root set to {path}")

    def add_key():
        pub = simpledialog.askstring("Public Key", "Paste OpenSSH public key:")
        if pub:
            with auth._lock, auth._connect() as c:
                c.execute("INSERT OR IGNORE INTO USER(pubkey) VALUES(?)", (pub,))
                c.commit()
            messagebox.showinfo("Added", "Key stored.")

    tk.Button(root, text="Set Root Folder", command=choose_root).pack(pady=5)
    tk.Button(root, text="Add User Key", command=add_key).pack(pady=5)

    root.mainloop()