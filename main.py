import tkinter as tk
from tkinter import filedialog
import cv2
from pdf2image import convert_from_path
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime
import io
import os

# Global variables
label_image = None
selected_area_high_res = None
preview_image_path = None

# Define colors and fonts
bg_color = "#2c3e50"
button_color = "#3498db"
button_hover_color = "#2980b9"
button_text_color = "#ecf0f1"
label_bg_color = "#34495e"
label_fg_color = "#ecf0f1"
font = ("Helvetica", 12)

def select_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        extract_label_from_pdf(file_path)

def extract_label_from_pdf(file_path):
    global selected_area_high_res
    images = convert_from_path(file_path, dpi=300)
    if images:
        img_high_res = np.array(images[0])

        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        img_height, img_width = img_high_res.shape[:2]
        max_window_size = (screen_width * 0.8, screen_height * 0.8)
        scale = min(max_window_size[0] / img_width, max_window_size[1] / img_height)
        if scale < 1:
            img_scaled = cv2.resize(img_high_res, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        else:
            img_scaled = img_high_res

        # Select ROI with new instructions
        rect = cv2.selectROI("Press 'ENTER' to Save Selection or Press 'ESC' to Exit", img_scaled, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow("Press 'ENTER' to Save Selection or Press 'ESC' to Exit")

        x, y, w, h = rect
        if w == 0 or h == 0:
            return None

        x_real = int(x / scale)
        y_real = int(y / scale)
        w_real = int(w / scale)
        h_real = int(h / scale)

        selected_area_high_res = img_high_res[y_real:y_real+h_real, x_real:x_real+w_real]

        if w_real > h_real:
            selected_area_high_res = cv2.rotate(selected_area_high_res, cv2.ROTATE_90_CLOCKWISE)

        display_label(selected_area_high_res)
        enable_buttons()

def save_label_as_pdf():
    global selected_area_high_res
    if selected_area_high_res is not None:
        new_width = 1200
        new_height = 1800
        resized_label = cv2.resize(selected_area_high_res, (new_width, new_height))
        label_image = Image.fromarray(cv2.cvtColor(resized_label, cv2.COLOR_BGR2RGB))

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"label_{current_time}.pdf"

        label_pdf_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialfile=default_filename)

        if label_pdf_path:
            label_image.save(label_pdf_path, "PDF", resolution=300.0)
            print(f"Label saved as PDF to {label_pdf_path}")
            os.startfile(label_pdf_path)

def display_label(image):
    global preview_image_path
    label_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    preview_image_path = io.BytesIO()
    label_image.save(preview_image_path, format='PNG')

    preview_image = Image.open(preview_image_path)
    preview_image.thumbnail((400, 400))
    image_tk = ImageTk.PhotoImage(preview_image)
    label.config(image=image_tk)
    label.image = image_tk

def clear_selection():
    global selected_area_high_res, label_image
    label.config(image='')
    selected_area_high_res = None
    label_image = None
    enable_buttons(clear=False, save=False)
    select_pdf()

def enable_buttons(clear=True, save=True):
    if clear:
        clear_button.config(state=tk.NORMAL)
    else:
        clear_button.config(state=tk.DISABLED)

    if save:
        save_button.config(state=tk.NORMAL)
    else:
        save_button.config(state=tk.DISABLED)

# Button hover effect
def on_enter(e):
    e.widget['background'] = button_hover_color

def on_leave(e):
    e.widget['background'] = button_color

# GUI setup
root = tk.Tk()
root.title("Carson's PDF Label Extractor")
root.geometry("600x600")
root.configure(bg=bg_color)

# Button to select PDF file
select_button = tk.Button(root, text="Select PDF File", command=select_pdf, bg=button_color, fg=button_text_color, font=font, bd=0)
select_button.pack(pady=20)
select_button.bind("<Enter>", on_enter)
select_button.bind("<Leave>", on_leave)

# Label to display the selected image
label = tk.Label(root, bg=label_bg_color, fg=label_fg_color, font=font)
label.pack(pady=20, fill=tk.BOTH, expand=True)

# Button to clear selection
clear_button = tk.Button(root, text="Select Different PDF", command=clear_selection, bg=button_color, fg=button_text_color, font=font, bd=0, state=tk.DISABLED)
clear_button.pack(side=tk.LEFT, padx=20, pady=20)
clear_button.bind("<Enter>", on_enter)
clear_button.bind("<Leave>", on_leave)

# Button to save the label as PDF
save_button = tk.Button(root, text="Save Label", command=save_label_as_pdf, bg=button_color, fg=button_text_color, font=font, bd=0, state=tk.DISABLED)
save_button.pack(side=tk.RIGHT, padx=20, pady=20)
save_button.bind("<Enter>", on_enter)
save_button.bind("<Leave>", on_leave)

root.mainloop()