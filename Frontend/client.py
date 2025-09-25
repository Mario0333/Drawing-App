import customtkinter as ctk
import requests
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io

API_URL = "http://127.0.0.1:5000"
current_user = None  # track logged-in user

# ---------------- LOGIN SCREEN ----------------
def open_login_window():
    app = ctk.CTk()
    app.title("Drawing Social App - Login")
    app.geometry("400x300")

    mode = ctk.StringVar(value="login")

    def switch_mode():
        if mode.get() == "login":
            mode.set("signup")
            title_label.configure(text="Signup")
            action_button.configure(text="Signup")
            switch_button.configure(text="Switch to Login")
        else:
            mode.set("login")
            title_label.configure(text="Login")
            action_button.configure(text="Login")
            switch_button.configure(text="Switch to Signup")

    def submit_action():
        global current_user
        username = entry_username.get()
        password = entry_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        endpoint = "/login" if mode.get() == "login" else "/signup"
        response = requests.post(API_URL + endpoint, json={"username": username, "password": password})

        if response.status_code in [200, 201]:
            current_user = username
            app.destroy()
            open_main_window()
        else:
            messagebox.showerror("Error", response.json()["message"])

    # UI
    title_label = ctk.CTkLabel(app, text="Login", font=("Arial", 20))
    title_label.pack(pady=20)

    entry_username = ctk.CTkEntry(app, placeholder_text="Username")
    entry_username.pack(pady=10)

    entry_password = ctk.CTkEntry(app, placeholder_text="Password", show="*")
    entry_password.pack(pady=10)

    action_button = ctk.CTkButton(app, text="Login", command=submit_action)
    action_button.pack(pady=10)

    switch_button = ctk.CTkButton(app, text="Switch to Signup", command=switch_mode)
    switch_button.pack(pady=10)

    app.mainloop()

# ---------------- MAIN APP SCREEN ----------------
def open_main_window():
    main = ctk.CTk()
    main.title("Drawing Social App")
    main.geometry("1000x600")

    # Configure grid layout (3 columns)
    main.grid_columnconfigure(0, weight=1, minsize=200)  # Left sidebar
    main.grid_columnconfigure(1, weight=3, minsize=500)  # Main content
    main.grid_columnconfigure(2, weight=1, minsize=200)  # Right sidebar
    main.grid_rowconfigure(0, weight=1)

    # ---------------- LEFT SIDEBAR ----------------
    left_sidebar = ctk.CTkFrame(main, width=200, corner_radius=0)
    left_sidebar.grid(row=0, column=0, sticky="nswe")

    profile_label = ctk.CTkLabel(left_sidebar, text=f"Logged in as:\n{current_user}", font=("Arial", 14))
    profile_label.pack(pady=20)

    friends_label = ctk.CTkLabel(left_sidebar, text="Friends", font=("Arial", 16))
    friends_label.pack(pady=10)

    # Example friend list
    friends_list = ["Alice", "Bob", "Charlie"]
    for f in friends_list:
        ctk.CTkButton(left_sidebar, text=f, width=150).pack(pady=5)

    # ---------------- MAIN CONTENT ----------------
    main_content = ctk.CTkFrame(main, corner_radius=10)
    main_content.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

    # Tabs inside main content
    tabview = ctk.CTkTabview(main_content, width=580, height=550)
    tabview.pack(padx=10, pady=10, fill="both", expand=True)

    upload_tab = tabview.add("Upload")
    feed_tab = tabview.add("Feed")

    # --- Upload Tab ---
    def upload_file():
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        files = {"file": open(file_path, "rb")}
        data = {"username": current_user}
        response = requests.post(API_URL + "/upload", files=files, data=data)

        if response.status_code == 201:
            messagebox.showinfo("Success", "Upload successful!")
            refresh_feed()
        else:
            messagebox.showerror("Error", response.json()["message"])

    upload_button = ctk.CTkButton(upload_tab, text="Upload Drawing", command=upload_file)
    upload_button.pack(pady=20)

    # --- Feed Tab ---
    feed_frame = ctk.CTkScrollableFrame(feed_tab, width=560, height=500)
    feed_frame.pack(pady=10, padx=10, fill="both", expand=True)

    def refresh_feed():
        for widget in feed_frame.winfo_children():
            widget.destroy()

        response = requests.get(API_URL + "/feed")
        if response.status_code == 200:
            posts = response.json()
            for post in posts:
                label = ctk.CTkLabel(feed_frame, text=f"{post['username']} uploaded:")
                label.pack()

                img_response = requests.get(API_URL + "/uploads/" + post["filename"])
                if img_response.status_code == 200:
                    img_data = io.BytesIO(img_response.content)
                    pil_img = Image.open(img_data).resize((200, 200))
                    tk_img = ImageTk.PhotoImage(pil_img)

                    img_label = ctk.CTkLabel(feed_frame, image=tk_img, text="")
                    img_label.image = tk_img
                    img_label.pack(pady=5)

    refresh_feed()

    # ---------------- RIGHT SIDEBAR ----------------
    right_sidebar = ctk.CTkFrame(main, width=200, corner_radius=0)
    right_sidebar.grid(row=0, column=2, sticky="nswe")

    online_label = ctk.CTkLabel(right_sidebar, text="Online Friends", font=("Arial", 16))
    online_label.pack(pady=20)

    # Example online friends
    online_list = ["Diana", "Ethan"]
    for o in online_list:
        ctk.CTkLabel(right_sidebar, text=f"🟢 {o}", font=("Arial", 12)).pack(pady=5)

    main.mainloop()


# ---------------- RUN APP ----------------
open_login_window()
