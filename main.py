# 451-badge-v1 - Description rapide du programme.
# Copyright (C) 2026 uhqtools-on
# This file is part of 451-badge-v1.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see https://www.gnu.org/licenses/.


import tkinter as tk
import threading
import requests
import time

API_BASE = "https://discord.com/api/v9"

HOUSES = {
    "Bravery":    1,
    "Brilliance": 2,
    "Balance":    3,
}

HOUSE_COLORS = {
    "Bravery":    "#9B59B6",
    "Brilliance": "#F1C40F",
    "Balance":    "#2ECC71",
}


class HypeSquadClient:
    def __init__(self, token, log):
        self.token = token.strip()
        self.log = log
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

    def get_me(self):
        r = requests.get(f"{API_BASE}/users/@me", headers=self.headers, timeout=15)
        if r.status_code == 401:
            raise RuntimeError("Token invalide (401).")
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _extract_house(flags):
        if flags & (1 << 6):
            return 1
        if flags & (1 << 7):
            return 2
        if flags & (1 << 8):
            return 3
        return None

    def set_house(self, house_id):
        r = requests.post(
            f"{API_BASE}/hypesquad/online",
            headers=self.headers,
            json={"house_id": house_id},
            timeout=15,
        )
        if r.status_code == 204:
            return True
        if r.status_code == 429:
            wait = r.json().get("retry_after", 5)
            self.log(f"Cooldown {wait}s, retry...")
            time.sleep(wait + 1)
            return self.set_house(house_id)
        raise RuntimeError(f"Erreur {r.status_code}: {r.text}")

    def run(self, house_name):
        self.log("Verification du token...")
        me = self.get_me()
        self.log(f"Connecte : {me['username']} (id {me['id']})")

        existing = self._extract_house(me.get("flags", 0))
        if existing:
            names = {v: k for k, v in HOUSES.items()}
            self.log(f"Badge actuel : {names[existing]}")
            if existing == HOUSES[house_name]:
                self.log(f"Deja {house_name} - rien a faire.")
                return True
            self.log(f"Changement vers {house_name}...")

        self.log(f"Attribution : {house_name}...")
        self.set_house(HOUSES[house_name])
        self.log(f"Badge {house_name} active ! Redemarre Discord.")
        return True


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Discord HypeSquad - Venice")
        self.geometry("520x540")
        self.resizable(False, False)
        self.configure(bg="#1e1f22")
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg="#1e1f22")
        header.pack(fill="x", pady=(20, 10))

        tk.Label(
            header, text="HypeSquad Badge",
            font=("Segoe UI", 18, "bold"),
            fg="#ffffff", bg="#1e1f22",
        ).pack()
        tk.Label(
            header, text="Colle ton token, choisis ta maison.",
            font=("Segoe UI", 9),
            fg="#b9bbbe", bg="#1e1f22",
        ).pack(pady=(2, 0))

        token_frame = tk.Frame(self, bg="#1e1f22")
        token_frame.pack(fill="x", padx=30, pady=(15, 5))

        tk.Label(
            token_frame, text="Token Discord",
            font=("Segoe UI", 10, "bold"),
            fg="#dcddde", bg="#1e1f22", anchor="w",
        ).pack(fill="x")

        self.token_entry = tk.Entry(
            token_frame, font=("Consolas", 10),
            bg="#2b2d31", fg="#ffffff", insertbackground="#ffffff",
            relief="flat", bd=0,
        )
        self.token_entry.pack(fill="x", ipady=8, pady=(4, 0))

        house_frame = tk.Frame(self, bg="#1e1f22")
        house_frame.pack(fill="x", padx=30, pady=(20, 5))

        tk.Label(
            house_frame, text="Choisis ton badge",
            font=("Segoe UI", 10, "bold"),
            fg="#dcddde", bg="#1e1f22", anchor="w",
        ).pack(fill="x")

        self.house_var = tk.StringVar(value="Bravery")
        radio_container = tk.Frame(house_frame, bg="#1e1f22")
        radio_container.pack(fill="x", pady=(8, 0))

        for name in HOUSES:
            tk.Radiobutton(
                radio_container,
                text=name,
                value=name,
                variable=self.house_var,
                font=("Segoe UI", 11),
                fg=HOUSE_COLORS[name],
                bg="#1e1f22",
                selectcolor="#2b2d31",
                activebackground="#1e1f22",
                activeforeground=HOUSE_COLORS[name],
                cursor="hand2",
            ).pack(side="left", padx=(0, 20))

        self.run_btn = tk.Button(
            self, text="Attribuer le badge",
            font=("Segoe UI", 11, "bold"),
            bg="#5865F2", fg="#ffffff",
            activebackground="#4752C4", activeforeground="#ffffff",
            relief="flat", cursor="hand2", bd=0,
            command=self.on_run,
        )
        self.run_btn.pack(fill="x", padx=30, pady=(25, 15), ipady=10)

        log_frame = tk.Frame(self, bg="#1e1f22")
        log_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        tk.Label(
            log_frame, text="Console",
            font=("Segoe UI", 9, "bold"),
            fg="#72767d", bg="#1e1f22", anchor="w",
        ).pack(fill="x")

        self.log_box = tk.Text(
            log_frame, font=("Consolas", 9),
            bg="#2b2d31", fg="#dcddde",
            relief="flat", bd=0, wrap="word",
            state="disabled", height=10,
        )
        self.log_box.pack(fill="both", expand=True, pady=(4, 0))

        self.status = tk.Label(
            self, text="Pret.", font=("Segoe UI", 8),
            fg="#72767d", bg="#1e1f22", anchor="w",
        )
        self.status.pack(fill="x", padx=30, pady=(0, 10))

    def log(self, msg):
        def _write():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _write)

    def set_status(self, text):
        self.after(0, lambda: self.status.config(text=text))

    def on_run(self):
        token = self.token_entry.get().strip()
        if not token:
            self.log("Token vide.")
            return

        house = self.house_var.get()
        self.run_btn.config(state="disabled", text="En cours...")
        self.set_status("Traitement...")

        def worker():
            try:
                client = HypeSquadClient(token, self.log)
                client.run(house)
                self.set_status("Termine.")
            except Exception as e:
                self.log(f"Erreur : {e}")
                self.set_status("Erreur.")
            finally:
                self.after(0, lambda: self.run_btn.config(
                    state="normal", text="Attribuer le badge"))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()