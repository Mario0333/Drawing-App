import customtkinter as ctk
import requests
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import io, os

API_URL = "http://127.0.0.1:5000"
current_user = None
current_user_id = None
dark_mode = False

# Helper functions
def make_circle(img: Image.Image, size=(150, 150)):
    img = img.resize(size, Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    out = Image.new("RGBA", size)
    out.paste(img, (0, 0), mask=mask)
    return out

def create_placeholder(size=(150, 150)):
    img = Image.new("RGBA", size, (200, 200, 200, 255))
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    out = Image.new("RGBA", size, (255, 255, 255, 0))
    out.paste(img, (0, 0), mask=mask)
    return out

# Login/Signup
def open_login_window():
    global current_user, current_user_id
    app = ctk.CTk()
    app.title("PALETTE - Login")
    app.geometry("500x450")
    app.resizable(False, False)
    app.configure(fg_color="#FFFFFF")

    mode = ctk.StringVar(value="login")

    def switch_mode():
        if mode.get() == "login":
            mode.set("signup")
            title_label.configure(text="SIGNUP")
            action_button.configure(text="Signup")
            switch_button.configure(text="Switch to Login")
        else:
            mode.set("login")
            title_label.configure(text="LOGIN")
            action_button.configure(text="Login")
            switch_button.configure(text="Switch to Signup")

    def submit_action():
        global current_user, current_user_id
        username = entry_username.get()
        password = entry_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        endpoint = "/login" if mode.get() == "login" else "/signup"
        response = requests.post(API_URL + endpoint, json={"username": username, "password": password})

        if response.status_code in [200, 201]:
            current_user = username
            if mode.get() == "login":
                current_user_id = response.json().get("user_id")
            else:
                login_res = requests.post(API_URL + "/login", json={"username": username, "password": password})
                if login_res.status_code == 200:
                    current_user_id = login_res.json().get("user_id")
                else:
                    messagebox.showerror("Error", login_res.text or "Login after signup failed")
                    return
            app.destroy()
            open_main_window()
        else:
            try:
                error_message = response.json().get("message", "An unexpected error occurred")
                messagebox.showerror("Error", error_message)
            except requests.exceptions.JSONDecodeError:
                messagebox.showerror("Error", "Server is unreachable or returned invalid data. Ensure the backend is running.")

    frame = ctk.CTkFrame(app, width=400, height=400, corner_radius=15, fg_color="#A39775")
    frame.pack(pady=20)
    frame.pack_propagate(False)

    title_label = ctk.CTkLabel(frame, text="LOGIN", font=("Arial", 40, "bold"), text_color="black")
    title_label.pack(pady=20)

    entry_username = ctk.CTkEntry(frame, placeholder_text="Username", width=300, fg_color="#FFFFFF", text_color="black")
    entry_username.pack(pady=10)

    entry_password = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=300, fg_color="#FFFFFF", text_color="black")
    entry_password.pack(pady=10)

    action_button = ctk.CTkButton(frame, text="Login", command=submit_action, font=("Arial", 16, "bold"), fg_color="#C44E00", text_color="black", width=160, height=40, corner_radius=20, hover_color="#0DA000")
    action_button.pack(pady=10)

    switch_button = ctk.CTkButton(frame, text="Switch to Signup", command=switch_mode, font=("Arial", 16, "bold"), fg_color="#C44E00", text_color="black", width=140, height=40, corner_radius=20, hover_color="#0DA000")
    switch_button.pack(pady=10)

    app.mainloop()
# Main window
def open_main_window():
    global current_user, current_user_id, dark_mode
    main = ctk.CTk()
    main.title("PALETTE")
    main.geometry("800x600")
    main.configure(fg_color="#FFFFFF" if not dark_mode else "#2E2E2E")

    # Menu bar
    menu_bar = ctk.CTkFrame(main, fg_color="#A39775", height=60)
    menu_bar.pack(fill="x")

    # Profile pic in menu
    profile_response = requests.get(f"{API_URL}/profile/{current_user_id}")
    profile_data = profile_response.json()
    profile_pic_filename = profile_data.get("profile_pic")
    if profile_pic_filename:
        img_url = f"{API_URL}/uploads/{profile_pic_filename}"
        img_data = requests.get(img_url).content
        img = Image.open(io.BytesIO(img_data))
        menu_img = make_circle(img, (40, 40))
    else:
        menu_img = create_placeholder((40, 40))
    menu_img_ref = ImageTk.PhotoImage(menu_img)
    menu_profile_pic = ctk.CTkLabel(menu_bar, image=menu_img_ref, text="")
    menu_profile_pic.pack(side="left", padx=10)

    welcome_label = ctk.CTkLabel(menu_bar, text=f"Welcome, {current_user}!", font=("Arial", 16), text_color="black" if not dark_mode else "white")
    welcome_label.pack(side="left", padx=10)

    def logout():
        global current_user, current_user_id
        current_user = None
        current_user_id = None
        main.destroy()
        open_login_window()

    logout_button = ctk.CTkButton(menu_bar, text="Logout", command=logout, fg_color="#C44E00", hover_color="#0DA000")
    logout_button.pack(side="right", padx=10)

    def toggle_dark_mode():
        global dark_mode
        dark_mode = not dark_mode
        main.configure(fg_color="#FFFFFF" if not dark_mode else "#2E2E2E")
        welcome_label.configure(text_color="black" if not dark_mode else "white")
        tabview.configure(fg_color="#F0F0F0" if not dark_mode else "#3E3E3E")
        for tab in tabview._tabs:
            tab.configure(fg_color="#FFFFFF" if not dark_mode else "#2E2E2E")
        main.update()

    dark_mode_button = ctk.CTkButton(menu_bar, text="Toggle Dark Mode", command=toggle_dark_mode, fg_color="#C44E00", hover_color="#0DA000")
    dark_mode_button.pack(side="right", padx=10)

    # Tabview
    tabview = ctk.CTkTabview(main, fg_color="#F0F0F0" if not dark_mode else "#3E3E3E")
    tabview.pack(fill="both", expand=True, padx=20, pady=20)

   # Feed Tab
    feed_tab = tabview.add("Feed")

    # Use grid layout for feed and recommendations side by side
    feed_tab.grid_columnconfigure(0, weight=3)  # Feed takes more space
    feed_tab.grid_columnconfigure(1, weight=1)  # Recommendations take less space
    feed_tab.grid_rowconfigure(0, weight=1)     # Allow scrollable area to expand
    feed_tab.grid_rowconfigure(1, weight=0)     # Button row

    # Feed Scrollable Area (left side)
    feed_scroll = ctk.CTkScrollableFrame(feed_tab, fg_color="#FFFFFF" if not dark_mode else "#2E2E2E")
    feed_scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def load_feed():
        response = requests.get(API_URL + "/feed")
        if response.status_code == 200:
            posts = response.json()
            for widget in feed_scroll.winfo_children():
                widget.destroy()
            for post in posts:
                post_frame = ctk.CTkFrame(feed_scroll, fg_color="#FFFFFF" if not dark_mode else "#2E2E2E")
                post_frame.pack(fill="x", pady=10)

                # Image
                img_url = f"{API_URL}/uploads/{post['filename']}"
                img_data = requests.get(img_url).content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((200, 200), Image.LANCZOS)
                img_tk = ctk.CTkImage(img, size=(200, 200))
                img_label = ctk.CTkLabel(post_frame, image=img_tk, text="")
                img_label.pack(side="left", padx=10)

                # Post info
                info_frame = ctk.CTkFrame(post_frame)
                info_frame.pack(side="left", fill="x", expand=True, padx=10)

                # Username with avatar
                user_frame = ctk.CTkFrame(info_frame)
                user_frame.pack(fill="x", pady=5)
                if post['profile_pic']:
                    user_pic_url = f"{API_URL}/uploads/{post['profile_pic']}"
                    user_pic_data = requests.get(user_pic_url).content
                    user_pic_img = Image.open(io.BytesIO(user_pic_data))
                    user_pic_img = user_pic_img.resize((30, 30), Image.LANCZOS)
                    user_pic_tk = ctk.CTkImage(user_pic_img, size=(30, 30))
                    user_avatar = ctk.CTkLabel(user_frame, image=user_pic_tk, text="")
                    user_avatar.pack(side="left", padx=5)
                username_label = ctk.CTkLabel(user_frame, text=post['username'], font=("Arial", 12), text_color="black" if not dark_mode else "white")
                username_label.pack(side="left")
                timestamp_label = ctk.CTkLabel(user_frame, text=post['timestamp'], font=("Arial", 10), text_color="gray")
                timestamp_label.pack(side="right")

                # Likes
                likes_frame = ctk.CTkFrame(info_frame)
                likes_frame.pack(fill="x", pady=5)
                like_button = ctk.CTkButton(likes_frame, text="❤️ Like", width=80, command=lambda pid=post['id']: toggle_like(pid))
                like_button.pack(side="left")
                likes_label = ctk.CTkLabel(likes_frame, text=f"{post['likes_count']} likes", font=("Arial", 10), text_color="black" if not dark_mode else "white")
                likes_label.pack(side="left", padx=10)

                # Comments section
                comments_frame = ctk.CTkFrame(info_frame)
                comments_frame.pack(fill="x", pady=5)
                comments_title = ctk.CTkLabel(comments_frame, text="Comments", font=("Arial", 12, "bold"), text_color="black" if not dark_mode else "white")
                comments_title.pack(anchor="w")
                for comment in post['comments']:
                    comment_row = ctk.CTkFrame(comments_frame)
                    comment_row.pack(fill="x", pady=2)
                    comment_text = ctk.CTkLabel(comment_row, text=f"{comment['username']}: {comment['text']}", font=("Arial", 10), text_color="black" if not dark_mode else "white", wraplength=300)
                    comment_text.pack(side="left")
                    comment_time = ctk.CTkLabel(comment_row, text=comment['timestamp'], font=("Arial", 8), text_color="gray")
                    comment_time.pack(side="right")

                # Add comment input
                input_frame = ctk.CTkFrame(comments_frame)
                input_frame.pack(fill="x", pady=5)
                comment_entry = ctk.CTkEntry(input_frame, placeholder_text="Write a comment...", width=400)
                comment_entry.pack(side="left", padx=5)
                def add_comment_wrapper(pid=post['id']):
                    add_comment(pid, comment_entry)
                comment_button = ctk.CTkButton(input_frame, text="Post", command=add_comment_wrapper, width=60)
                comment_button.pack(side="right")

                # Delete if owner's post
                if post['user_id'] == current_user_id:
                    delete_button = ctk.CTkButton(post_frame, text="Delete", command=lambda pid=post['id']: delete_post(pid), fg_color="#C44E00", hover_color="#0DA000")
                    delete_button.pack(side="right", padx=10)

    def toggle_like(post_id):
        response = requests.post(f"{API_URL}/like/{post_id}", json={"user_id": current_user_id})
        if response.status_code == 200:
            data = response.json()
            load_feed()  # Refresh to update counts

    def add_comment(post_id, entry):
        text = entry.get()
        if text.strip():
            response = requests.post(f"{API_URL}/comment/{post_id}", json={"user_id": current_user_id, "text": text})
            if response.status_code == 201:
                entry.delete(0, 'end')
                load_feed()  # Refresh to show new comment

    def delete_post(post_id):
        response = requests.delete(f"{API_URL}/delete/{post_id}", json={"user_id": current_user_id})
        if response.status_code == 200:
            messagebox.showinfo("Success", "Post deleted!")
            load_feed()
        else:
            messagebox.showerror("Error", response.json()["message"])

    # You Might Like Section (right side)
    rec_frame = ctk.CTkFrame(feed_tab , fg_color="#FFFFFF" if not dark_mode else "#2E2E2E", width=150)
    rec_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=20)
    rec_frame.grid_rowconfigure(0, weight=0)  # Title row
    rec_frame.grid_rowconfigure(1, weight=1)  # Scrollable area

    # Bold "You Might Like" title
    rec_title = ctk.CTkLabel(rec_frame, text="You Might Like", font=("Arial", 14, "bold"), text_color="black" if not dark_mode else "white")
    rec_title.grid(row=0, column=0, pady=(0, 10))

    rec_scroll = ctk.CTkScrollableFrame(rec_frame, orientation="vertical", width=100, height=500)
    rec_scroll.grid(row=1, column=0, sticky="nsew")

    def load_recommendations():
        response = requests.get(f"{API_URL}/recommendations/{current_user_id}")
        if response.status_code == 200:
            recs = response.json()
            for widget in rec_scroll.winfo_children():
                widget.destroy()
            for rec in recs:
                rec_item = ctk.CTkFrame(rec_scroll)
                rec_item.pack(fill="x", pady=10)

                img_url = f"{API_URL}/uploads/{rec['filename']}"
                img_data = requests.get(img_url).content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((150, 150), Image.LANCZOS)
                img_tk = ctk.CTkImage(img, size=(150, 150))
                rec_img = ctk.CTkLabel(rec_item, image=img_tk, text="")
                rec_img.pack()

                rec_username = ctk.CTkLabel(rec_item, text=rec['username'], font=("Arial", 10), text_color="black" if not dark_mode else "white")
                rec_username.pack()
                like_button = ctk.CTkButton(rec_item, text="Like", command=lambda pid=rec['id']: toggle_like(pid), width=60)
                like_button.pack()

    # Place load_feed_button below feed_scroll using grid
    load_feed_button = ctk.CTkButton(feed_tab, text="Refresh Feed", command=load_feed, fg_color="#C44E00", hover_color="#0DA000")
    load_feed_button.grid(row=1, column=0, pady=10)

    load_feed()
    load_recommendations()

    def delete_post(post_id):
        response = requests.delete(f"{API_URL}/delete/{post_id}", json={"user_id": current_user_id})
        if response.status_code == 200:
            messagebox.showinfo("Success", "Post deleted!")
            load_feed()
        else:
            messagebox.showerror("Error", response.json()["message"])

    load_feed_button = ctk.CTkButton(feed_tab, text="Refresh Feed", command=load_feed, fg_color="#C44E00", hover_color="#0DA000")
    load_feed_button.grid(row=1, column=0, pady=10)
    load_feed()

    # Upload Tab
    upload_tab = tabview.add("Upload")

    def upload_file():
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if file_path:
            img = Image.open(file_path)
            img = img.resize((200, 200), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            preview_label = ctk.CTkLabel(upload_tab, image=img_tk, text="")
            preview_label.image = img_tk
            preview_label.pack(pady=10)

            progress = ctk.CTkProgressBar(upload_tab, width=200)
            progress.pack(pady=10)
            progress.set(0.0)

            files = {'file': open(file_path, 'rb')}
            data = {'user_id': current_user_id}
            response = requests.post(API_URL + "/upload", files=files, data=data)
            progress.set(1.0)

            if response.status_code == 201:
                messagebox.showinfo("Success", "Upload successful!")
            else:
                messagebox.showerror("Error", response.json()["message"])
            preview_label.destroy()
            progress.destroy()

    upload_button = ctk.CTkButton(upload_tab, text="Select and Upload Drawing", command=upload_file, fg_color="#C44E00", hover_color="#0DA000")
    upload_button.pack(pady=20)

    # Profile Tab
    profile_tab = tabview.add("Profile")

    response = requests.get(f"{API_URL}/profile/{current_user_id}")
    profile_data = response.json()

    profile_info = ctk.CTkLabel(profile_tab, text=f"Username: {current_user}", font=("Arial", 16), text_color="black" if not dark_mode else "white")
    profile_info.pack(pady=20)

    profile_image_ref = None
    if profile_data['profile_pic']:
        img = Image.open(io.BytesIO(requests.get(f"{API_URL}/uploads/{profile_data['profile_pic']}").content))
        profile_img = make_circle(img)
        profile_image_ref = ImageTk.PhotoImage(profile_img)
    else:
        profile_image_ref = ImageTk.PhotoImage(create_placeholder())
    profile_pic_label = ctk.CTkLabel(profile_tab, image=profile_image_ref, text="")
    profile_pic_label.pack(pady=10)

    def upload_profile_pic():
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if file_path:
            files = {'file': open(file_path, 'rb')}
            data = {'user_id': current_user_id}
            response = requests.post(API_URL + "/upload_profile", files=files, data=data)
            if response.status_code == 201:
                messagebox.showinfo("Success", "Profile picture uploaded!")
                new_filename = response.json()["filename"]
                img = Image.open(io.BytesIO(requests.get(f"{API_URL}/uploads/{new_filename}").content))
                new_img = make_circle(img)
                new_ref = ImageTk.PhotoImage(new_img)
                profile_pic_label.configure(image=new_ref)
                profile_pic_label.image = new_ref
            else:
                messagebox.showerror("Error", response.json()["message"])

    upload_pic_button = ctk.CTkButton(profile_tab, text="Upload Profile Picture", command=upload_profile_pic, fg_color="#C44E00", hover_color="#0DA000")
    upload_pic_button.pack(pady=10)

    bio_entry = ctk.CTkEntry(profile_tab, placeholder_text="Bio", width=300)
    bio_entry.insert(0, profile_data['bio'])
    bio_entry.pack(pady=5)

    location_entry = ctk.CTkEntry(profile_tab, placeholder_text="Location", width=300)
    location_entry.insert(0, profile_data['location'])
    location_entry.pack(pady=5)

    interests_entry = ctk.CTkEntry(profile_tab, placeholder_text="Interests", width=300)
    interests_entry.insert(0, profile_data['interests'])
    interests_entry.pack(pady=5)

    def save_profile():
        data = {
            "user_id": current_user_id,
            "bio": bio_entry.get(),
            "location": location_entry.get(),
            "interests": interests_entry.get()
        }
        response = requests.post(API_URL + "/update_profile", json=data)
        if response.status_code == 200:
            messagebox.showinfo("Success", "Profile updated!")

    save_button = ctk.CTkButton(profile_tab, text="Save Profile", command=save_profile, fg_color="#C44E00", hover_color="#0DA000")
    save_button.pack(pady=10)

    gallery_scroll = ctk.CTkScrollableFrame(profile_tab, fg_color="#FFFFFF" if not dark_mode else "#2E2E2E")
    gallery_scroll.pack(fill="both", expand=True, pady=10)

    def load_gallery():
        response = requests.get(API_URL + "/feed")
        if response.status_code == 200:
            posts = [p for p in response.json() if p['user_id'] == current_user_id]
            for widget in gallery_scroll.winfo_children():
                widget.destroy()
            for post in posts:
                img_url = f"{API_URL}/uploads/{post['filename']}"
                img_data = requests.get(img_url).content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((100, 100), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                img_label = ctk.CTkLabel(gallery_scroll, image=img_tk, text="")
                img_label.image = img_tk
                img_label.pack(side="left", padx=5)

    load_gallery()

    # Friends Tab
    friends_tab = tabview.add("Friends")

    friends_scroll = ctk.CTkScrollableFrame(friends_tab, fg_color="#FFFFFF" if not dark_mode else "#2E2E2E")
    friends_scroll.pack(fill="both", expand=True)

    def load_friends():
        response = requests.get(f"{API_URL}/friends/{current_user_id}")
        if response.status_code == 200:
            friends = response.json()
            for widget in friends_scroll.winfo_children():
                widget.destroy()
            for friend in friends:
                friend_label = ctk.CTkLabel(friends_scroll, text=friend['username'], font=("Arial", 12), text_color="black" if not dark_mode else "white")
                friend_label.pack(pady=5)

    load_friends_button = ctk.CTkButton(friends_tab, text="Refresh Friends", command=load_friends, fg_color="#C44E00", hover_color="#0DA000")
    load_friends_button.pack(pady=10)

    add_friend_entry = ctk.CTkEntry(friends_tab, placeholder_text="Friend's username", width=300)
    add_friend_entry.pack(pady=10)

    def add_friend():
        friend_username = add_friend_entry.get()
        if friend_username:
            response = requests.post(API_URL + "/add_friend", json={"user_id": current_user_id, "friend_username": friend_username})
            if response.status_code == 201:
                messagebox.showinfo("Success", "Friend added!")
                load_friends()
            else:
                messagebox.showerror("Error", response.json()["message"])

    add_friend_button = ctk.CTkButton(friends_tab, text="Add Friend", command=add_friend, fg_color="#C44E00", hover_color="#0DA000")
    add_friend_button.pack(pady=10)

    load_friends()

    main.mainloop()

# Run app
open_login_window()