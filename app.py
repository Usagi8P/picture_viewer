import customtkinter as ctk #type: ignore
from tkinter import filedialog
import tkinter as tk
import tkinter.ttk as ttk
import os
from PIL import Image, ImageTk #type: ignore
from db import get_db, close_db


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.app_height:int = 720
        self.app_width:int = 1280
        self.padding = 5

        self.title('Picture Viewer')
        self.geometry(f'{self.app_width}x{self.app_height}')
        ctk.set_appearance_mode('dark')

        self.current_dir = None
        self.jpegs = []
        self.jpeg_display = []
        self.active_index = 0
        self.angle = 0

        # -12 for the height of the title bar
        self.file_view = Panel(self, self, height=self.app_height-self.padding*2-12)
        self.file_view.grid(row=0, column=0, padx=self.padding, pady=self.padding)

        self.picture_view = PictureView(self, self)
        self.picture_view.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        self.key_lock = False
        self.bind('<Left>', self.show_previous_image)
        self.bind('<Right>', self.show_next_image)
        self.bind('<KeyPress-q>', self.rotate_left)
        self.bind('<KeyPress-e>', self.rotate_right)
        self.bind('<KeyPress-d>', self.set_keep)
        self.bind('<KeyPress-f>', self.set_delete)

    def delete(self):
        self.jpegs = []
        self.jpeg_display = []

    def show_previous_image(self, event=None):
        if self.active_index is None:
            return

        self.save_details()

        if self.active_index == 0:
            self.active_index = len(self.jpegs)-1
        else:
            self.active_index -= 1

        self.picture_view.open_image(self.jpegs[self.active_index])

    def show_next_image(self, event=None):
        if self.active_index is None:
            return
        
        self.save_details()

        if self.active_index == len(self.jpegs)-1:
            self.active_index = 0
        else:
            self.active_index += 1

        self.picture_view.open_image(self.jpegs[self.active_index])

    def reset_delete_option(self):
        db = get_db()

        delete_action = db.execute(
            """
            SELECT delete_action FROM files
             WHERE folder=? AND filename=?
            """, (self.current_dir, self.jpeg_display[self.active_index])
        ).fetchone()['delete_action']

        self.file_view.options.set(delete_action.title())
        if delete_action is None:
            self.file_view.options.set('Keep')

    def rotate_right(self, event=None):
        if self.picture_view.current_image is None:
            return
        
        self.save_details()

        if not self.key_lock:
            self.key_lock = True
            self.picture_view.rotate_image(-90)
            self.after(200, self.unlock_key)

    def rotate_left(self, event=None):
        if self.picture_view.current_image is None:
            return

        if not self.key_lock:
            self.key_lock = True
            self.picture_view.rotate_image(90)
            self.after(200, self.unlock_key)

    def unlock_key(self):
        self.key_lock = False

    def set_keep(self, event=None):
        self.file_view.options.set('Keep')

    def set_delete(self, event=None):
        self.file_view.options.set('Delete')

    def save_details(self):
        db = get_db()

        save_angle = ((self.angle / 90) % 4) * 90
        delete_action = self.file_view.options.get().lower()

        db.execute(
            """
            UPDATE files
             SET delete_action=?, rotation=?
             WHERE folder=? AND filename=?
            """, (delete_action, save_angle, self.current_dir, self.jpeg_display[self.active_index])
        )
        db.commit()
        close_db(db)

    def mainloop(self, n:int=0) -> None:
        return super().mainloop(n)


class Panel(ctk.CTkFrame):
    def __init__(self, parent, controller, height):
        super().__init__(parent)
        self.controller = controller

        self.browse_button = ctk.CTkButton(self, text='Browse', command=self.browse_directory)
        self.browse_button.pack(pady=5, anchor='nw')

        # TODO: Add panel to keep/discard
        self.options = ctk.CTkOptionMenu(self, values=['Keep', 'Delete'])
        self.options.pack(anchor='nw')

        # -10 for the padding, -30 for the height of the button
        self.file_view = FileView(self, controller, height-10-30)
        self.file_view.pack()
    
    def browse_directory(self):
        for widget in self.file_view.tree_view.winfo_children():
            widget.destroy()

        folder_path = filedialog.askdirectory()
        if folder_path:
            self.controller.current_dir = folder_path
            self.create_db_entry(folder_path)
            self.list_files(folder_path)

    def list_files(self, folder_path):
        self.controller.delete()
        if not folder_path:
            return

        db = get_db()

        filenames = db.execute(
            """
            SELECT filename FROM files
             WHERE folder = ?
            """, (folder_path,)
        ).fetchall()

        close_db(db)

        self.controller.jpegs = [os.path.join(folder_path,f['filename']) for f in filenames]
        self.controller.jpeg_display = [f['filename'] for f in filenames]
        if self.controller.jpegs:
            self.controller.picture_view.open_image(self.controller.jpegs[0])
            self.controller.active_index = 0
        self.file_view.tree_view.update()

    def create_db_entry(self, folder_path):
        db = get_db()

        filenames = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg'))]
        to_insert = [(folder_path, filename) for filename in filenames]
        db.executemany(
            """
            INSERT OR IGNORE INTO files (folder, filename)
            values (?,?)
            """, (to_insert)
            )
        db.commit()

        close_db(db)


class FileView(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller, height:int):
        super().__init__(parent, height=height)
        self.controller = controller

        self.tree_view = FileTree(self, controller)
        self.tree_view.pack()


class FileTree(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.files = []
        self.controller = controller

    def update(self):
        for i, file in enumerate(self.controller.jpeg_display):
            path = self.controller.jpegs[i]
            button = ctk.CTkButton(self, text=file, fg_color='transparent', height=10, command= lambda p=path: self.view_file(p))
            button.pack(anchor='w', fill='x')

    def view_file(self,path):
        self.controller.save_details()
        self.controller.picture_view.open_image(path)
        self.controller.active_index = self.controller.jpegs.index(path)


class PictureView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.image_label = ctk.CTkLabel(self, text='')
        self.image_label.pack(expand=True)
        self.current_image = None
        
    def open_image(self,path):
        self.current_image = Image.open(path)
        
        db = get_db()
        self.controller.angle = db.execute(
            """
            SELECT rotation FROM files
             WHERE folder=? AND filename=?
            """, (self.controller.current_dir, self.controller.jpeg_display[self.controller.active_index])
        ).fetchone()['rotation']
        db.close()

        self.controller.reset_delete_option()

        self.rotate_image()

    def display_image(self, image):
        width, height = image.size
        ratio = self.controller.app_height / height
        self.image_label.configure(image=ctk.CTkImage(image, size = (width*ratio, height*ratio)), text='')

    def rotate_image(self, angle:int=0):
        self.controller.angle += angle
        self.display_image(self.current_image.rotate(self.controller.angle))


def main() -> None:
    app = App()
    app.mainloop()


if __name__=="__main__":
    main()
