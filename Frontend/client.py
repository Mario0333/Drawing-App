import customtkinter as ctk
import requests
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import io , os

API_URL = "http://127.0.0.1:5000"
current_user = None  # track logged-in user


# ---------------- HELPER FUNCTIONS ----------------
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







# ---------------- LOGIN SCREEN ----------------
def open_login_window():
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
    
     #frame
    frame = ctk.CTkFrame(app, width=400, height=400, corner_radius=15 , fg_color="#A39775")
    frame.pack(pady=20)
    frame.pack_propagate(False)  # prevent frame from resizing to fit contents
   

    title_label = ctk.CTkLabel(frame, text="LOGIN", font=("Arial", 40, "bold"), text_color="black")
    title_label.pack(pady=20)
    
    entry_username = ctk.CTkEntry(frame, placeholder_text="Username", width=300 , fg_color="#FFFFFF", text_color="black", )
    entry_username.pack(pady=10)

    entry_password = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=300 , fg_color="#FFFFFF", text_color="black")
    entry_password.pack(pady=10)

    action_button = ctk.CTkButton(frame, text="Login", command=submit_action , font=("Arial",16,"bold") , fg_color="#C44E00", text_color="black", width=160, height=40 ,  corner_radius=20, hover_color="#0DA000")
    action_button.pack(pady=10)

    switch_button = ctk.CTkButton(frame, text="Switch to Signup", command=switch_mode, font=("Arial",16,"bold") , fg_color="#C44E00", text_color="black", width=140, height=40 ,  corner_radius=20, hover_color="#0DA000")
    switch_button.pack(pady=10)

    background_label = ctk.CTkLabel(frame, text="Welcome to Palette! Share Your Masterpiece!.", font=("Arial", 12), text_color="black")
    background_label.pack(side="bottom", pady=10)

    logo_label = ctk.CTkLabel(frame, text="🎨", height= 1000 , width= 500, font=("Arial", 50), text_color="orange" )
    logo_label.pack(side="left", padx=0, pady=0, anchor="center")

    app.mainloop()

# ---------------- MAIN APP SCREEN ----------------
def open_main_window():
    global profile_pic_label, menu_profile_pic, menu_img_ref, menu_username_label

    main = ctk.CTk()
    main.title("Palette")
    main.geometry("1000x600")

    # ---------------- MENU BAR ----------------
    menu_bar = ctk.CTkFrame(main, height=60, fg_color="#C44E00", corner_radius=10)
    menu_bar.pack(side="top", fill="x")

    # --- Search Bar in Menu Bar (center) ---
    def search_action():
        query = search_entry.get()
        if not query:
            messagebox.showinfo("Search", "Please enter a search term.")
            return
        # Example: search users (can be extended to search posts, etc.)
        response = requests.get(API_URL + "/search", params={"q": query})
        if response.status_code == 200:
            results = response.json()
            result_text = "\n".join(results) if results else "No results found."
            messagebox.showinfo("Search Results", result_text)
        else:
            messagebox.showerror("Error", "Search failed.")

    # Center the search bar in the menu bar
    search_frame = ctk.CTkFrame(menu_bar, fg_color="transparent")
    search_frame.place(relx=0.4, rely=0.5, anchor="center")

    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search users...", width=200 , fg_color="#FFFFFF")
    search_entry.pack(side="left", padx=5)

    search_button = ctk.CTkButton(search_frame, text="Search 🔍", command=search_action, width=80, height=30, fg_color="Black")
    search_button.pack(side="left", padx=5)

    menu_username_label = ctk.CTkLabel(menu_bar, text=f"{current_user}", font=("Arial", 14, "bold"))
    menu_username_label.pack(side="left", padx=5)
    menu_username_label.place(x=60, y=15) # adjust position next to profile pic


    # Menu button actions
    def go_home():
        tabview.set("Feed")

    def go_profile():
        tabview.set("Profile")

    def go_settings():
        messagebox.showinfo("Settings", "Settings screen coming soon!")

    def do_logout():
        main.destroy()
        open_login_window()

    logout_btn = ctk.CTkButton(menu_bar, text="Logout", width=80, height=30,
                               fg_color="red", text_color="white", command=do_logout)
    logout_btn.pack(side="right", padx=5, pady=10)

    settings_btn = ctk.CTkButton(menu_bar, text="Settings", width=80, height=30,
                                 fg_color="#000000", text_color="white", command=go_settings)
    settings_btn.pack(side="right", padx=5, pady=10)

    profile_btn = ctk.CTkButton(menu_bar, text="Profile", width=80, height=30,
                                fg_color="#000000", text_color="white", command=go_profile)
    profile_btn.pack(side="right", padx=5, pady=10)

    home_btn = ctk.CTkButton(menu_bar, text="Home", width=80, height=30,
                             fg_color="#000000", text_color="white", command=go_home)
    home_btn.pack(side="right", padx=5, pady=10)

    # Improved logo loading and display using CTkImage
    
        # Fallback if image not found
    logo_label = ctk.CTkLabel(menu_bar, text="🎨 PALETTE", font=("Arial", 24))
    logo_label.pack(side="left", padx=10, pady=10)



     # ---------------- RIGHT SIDEBAR ----------------
    right_sidebar = ctk.CTkFrame(main, width=500, corner_radius=15 ,fg_color="#BBA25D")
    right_sidebar.pack(side="right", fill="y", padx=20 , pady=20 )

    like_label = ctk.CTkLabel(right_sidebar, text=" You Might Like: ", font=("Arial", 20), text_color="black")
    like_label.pack(pady=20)

    online_label = ctk.CTkLabel(right_sidebar, text="                                         ", font=("Arial", 40))
    online_label.pack(pady=20)



    # ---------------- LEFT SIDEBAR ----------------
    left_sidebar = ctk.CTkFrame(main, width=500, corner_radius=15 ,fg_color="#BBA25D")
    left_sidebar.pack(side="left", fill="y", padx=20 , pady=20, )

    profile_label = ctk.CTkLabel(left_sidebar, text=f"Logged in as: {current_user}", width=200,  font=("Arial", 14), anchor="center", text_color="black")
    profile_label.pack(pady=20)

    friends_label = ctk.CTkLabel(left_sidebar, text="          Friends        ", font=("Arial", 16), text_color="black")
    friends_label.pack(pady=30)

    # Example friend list
    friends_list = ["Alice", "Bob", "Charlie"]
    for f in friends_list:
        ctk.CTkButton(left_sidebar, text=f, width=135,fg_color="#C44E00").pack(pady=5)


    # ---------------- MAIN CONTENT ----------------
    main_content = ctk.CTkFrame(main, corner_radius=10,bg_color="orange")
    main_content.pack(padx=10, pady=10, fill="both", expand=True)


    # Tabs inside main content
    tabview = ctk.CTkTabview(main_content, width=580, height=550)
    tabview.pack(padx=10, pady=10, fill="both", expand=True)

    upload_tab = tabview.add("Upload")
    feed_tab = tabview.add("Feed")
    tabview.set("Feed")  # default tab

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

    upload_button = ctk.CTkButton(upload_tab, text="Upload Drawing" , font=('Arial', 17) , command=upload_file , fg_color="#0B82F1", text_color="black", width=200, height=40 ,  corner_radius=10, hover_color="#0A6ED1" )
    upload_button.pack(side='bottom', padx= 150 ,pady=20)

    # --- Feed tab ---
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
                    pil_img = Image.open(img_data).resize((400, 400))
                    tk_img = ImageTk.PhotoImage(pil_img)

                    img_label = ctk.CTkLabel(feed_frame, image=tk_img, text="")
                    img_label.image = tk_img
                    img_label.pack(pady=5)

    refresh_feed()
    refresh_button = ctk.CTkButton(feed_tab, text="Refresh Feed", command=refresh_feed)
    refresh_button.pack(pady=10)

    #Back to login button
    """def logout():
        global current_user
        current_user = None
        main.destroy()
        open_login_window()
    logout_button = ctk.CTkButton(left_sidebar, text="Logout", command=logout)
    logout_button.pack(pady=20)"""

# --------------- Profile Tab ----------------
   

    profile_image_ref = None  # keep global reference

    def make_circle(img: Image.Image, size=(150, 150)):
        """Resize and crop an image into a circular format"""
        img = img.resize(size, Image.LANCZOS).convert("RGBA")

        # Create circular mask
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)

        # Apply mask
        circular_img = Image.new("RGBA", size)
        circular_img.paste(img, (0, 0), mask=mask)

        return circular_img

# ---------------- Profile Tab ----------------
    profile_tab = tabview.add("Profile")

    profile_info = ctk.CTkLabel(profile_tab, text=f"Username: {current_user}", font=("Arial", 16))
    profile_info.pack(pady=20)

    '''
    # Default gray placeholder avatar
    def create_placeholder(size=(150, 150)):
        img = Image.new("RGBA", size, (200, 200, 200, 255))  # gray circle
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        placeholder = Image.new("RGBA", size, (255, 255, 255, 0))
        placeholder.paste(img, (0, 0), mask=mask)
        return placeholder
    '''
    placeholder_img = create_placeholder()
    profile_image_ref = ImageTk.PhotoImage(placeholder_img)

    profile_pic_label = ctk.CTkLabel(profile_tab, image=profile_image_ref, text="")
    profile_pic_label.pack(pady=10)

    # Upload new profile picture
    def upload_profile_pic():
        global profile_image_ref

        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            img = make_circle(img)  # convert to circular

            profile_image_ref = ImageTk.PhotoImage(img)
            profile_pic_label.configure(image=profile_image_ref, text="")

            # TODO: send image to backend for saving
            messagebox.showinfo("Success", "Profile picture uploaded!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    upload_pic_button = ctk.CTkButton(profile_tab, text="Upload Profile Picture", command=upload_profile_pic)
    upload_pic_button.pack(pady=10)

    # Use the same profile image for both menu bar and profile tab
    # If user has uploaded a profile picture, use it; otherwise use placeholder
    if profile_image_ref in globals() and profile_image_ref is not None:
        menu_img_ref = profile_image_ref
    else:
        menu_img_ref = ImageTk.PhotoImage(create_placeholder((40, 40)))
    menu_profile_pic = ctk.CTkLabel(menu_bar, image=menu_img_ref, text="")
    menu_profile_pic.pack(side="left", padx=10, pady=10)
    

    


    # Additional profile info 
    profile_info2 = ctk.CTkLabel(profile_tab, text="Bio: Avid artist and doodler.", font=("Arial", 12))
    profile_info2.pack(pady=10)
    profile_info3 = ctk.CTkLabel(profile_tab, text="Location: Tanta City", font=("Arial", 12))
    profile_info3.pack(pady=10)
    profile_info4 = ctk.CTkLabel(profile_tab, text="Member since: 2025", font=("Arial", 12))
    profile_info4.pack(pady=10)
    profile_info5 = ctk.CTkLabel(profile_tab, text="Interests: Sketching, Painting, Digital Art", font=("Arial", 12))
    profile_info5.pack(pady=10)
    

    main.mainloop()


# ---------------- RUN APP ----------------
open_login_window()
