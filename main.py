import tkinter as tk
from tkinter import messagebox
import json
import os
import requests

FAV_FILE = "favorites.json"


def load_favorites():
    """Загрузка избранных пользователей из JSON."""
    if not os.path.exists(FAV_FILE):
        return []
    try:
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        messagebox.showwarning(
            "Избранное",
            "Файл favorites.json повреждён. Будет создан новый список избранных.",
        )
        return []


def save_favorites(favs):
    """Сохранение избранных пользователей в JSON."""
    try:
        with open(FAV_FILE, "w", encoding="utf-8") as f:
            json.dump(favs, f, ensure_ascii=False, indent=2)
    except OSError as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить избранное: {e}")


def fetch_user(username: str):
    """
    Запрос к GitHub API: получение информации о пользователе.
    Возвращает dict при успехе, None если пользователь не найден.
    """
    url = f"https://api.github.com/users/{username}"
    try:
        resp = requests.get(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "GitHub-User-Finder"},
            timeout=5,
        )
    except requests.RequestException as e:
        messagebox.showerror("Ошибка сети", f"Не удалось обратиться к GitHub API:\n{e}")
        return None

    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 404:
        return None
    else:
        messagebox.showerror(
            "Ошибка GitHub API",
            f"Код ответа: {resp.status_code}",
        )
        return None


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GitHub User Finder")

        # данные
        self.favorites = load_favorites()
        self.search_results = []  # список dict из GitHub API

        # ---------- Поле поиска ----------
        frame_search = tk.Frame(root)
        frame_search.pack(padx=10, pady=10, fill="x")

        lbl = tk.Label(frame_search, text="Логин пользователя GitHub:")
        lbl.pack(side="left")

        self.entry_username = tk.Entry(frame_search, width=30)
        self.entry_username.pack(side="left", padx=5)

        btn_search = tk.Button(frame_search, text="Найти", command=self.on_search)
        btn_search.pack(side="left")

        # ---------- Результаты поиска ----------
        frame_results = tk.Frame(root)
        frame_results.pack(padx=10, pady=5, fill="both", expand=True)

        lbl_results = tk.Label(frame_results, text="Результаты поиска:")
        lbl_results.pack(anchor="w")

        self.list_results = tk.Listbox(frame_results, width=60, height=8)
        self.list_results.pack(fill="both", expand=True)

        btn_add_fav = tk.Button(
            frame_results,
            text="Добавить в избранное",
            command=self.add_to_favorites,
        )
        btn_add_fav.pack(pady=5)

        # ---------- Избранные ----------
        frame_favs = tk.Frame(root)
        frame_favs.pack(padx=10, pady=5, fill="both", expand=True)

        lbl_favs = tk.Label(frame_favs, text="Избранные пользователи:")
        lbl_favs.pack(anchor="w")

        self.list_favs = tk.Listbox(frame_favs, width=60, height=8)
        self.list_favs.pack(fill="both", expand=True)

        self.update_favorites_listbox()

    # ===== Логика приложения =====

    def on_search(self):
        """Обработка нажатия кнопки 'Найти'."""
        username = self.entry_username.get().strip()
        if not username:
            messagebox.showwarning("Валидация", "Поле поиска не должно быть пустым.")
            return

        user = fetch_user(username)
        if user is None:
            messagebox.showinfo("Результат", f"Пользователь '{username}' не найден.")
            return

        # добавляем в список результатов
        self.search_results.append(user)
        display = self.format_user_display(user)
        self.list_results.insert(tk.END, display)

    @staticmethod
    def format_user_display(user: dict) -> str:
        """Формат строки для отображения в списке результатов."""
        login = user.get("login", "")
        public_repos = user.get("public_repos", 0)
        followers = user.get("followers", 0)
        return f"{login} | репозиториев: {public_repos} | подписчиков: {followers}"

    def add_to_favorites(self):
        """Добавить выбранного пользователя из результатов в избранное."""
        selection = self.list_results.curselection()
        if not selection:
            messagebox.showwarning(
                "Избранное",
                "Сначала выберите пользователя в списке результатов.",
            )
            return

        index = selection[0]
        user = self.search_results[index]
        login = user.get("login")
        html_url = user.get("html_url")

        if not login:
            messagebox.showerror(
                "Избранное",
                "Не удалось определить логин пользователя.",
            )
            return

        # проверка на дубликат
        if any(f["login"] == login for f in self.favorites):
            messagebox.showinfo(
                "Избранное",
                "Этот пользователь уже есть в избранном.",
            )
            return

        self.favorites.append({"login": login, "html_url": html_url})
        save_favorites(self.favorites)
        self.update_favorites_listbox()
        messagebox.showinfo(
            "Избранное",
            f"Пользователь '{login}' добавлен в избранное.",
        )

    def update_favorites_listbox(self):
        """Обновить отображение списка избранных пользователей."""
        self.list_favs.delete(0, tk.END)
        for user in self.favorites:
            login = user.get("login", "")
            url = user.get("html_url", "")
            self.list_favs.insert(tk.END, f"{login} | {url}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()