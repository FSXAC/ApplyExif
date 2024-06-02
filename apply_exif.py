# given a csv file and a directory, assign exif data to all images in a given
# directory. we can assume the images in the directories are labelled
# sequentially.
# 
# the program checks if exiftool is installed, and if not, it will prompt the
# user to install it.
# 
# the csv file should be formatted as follows (header included):
# Shot #, SS or exposure time, Aperture, Focal length, Date, Location,
# Longitude, Latitude
# 
# note that date is in string format, and location is in string format.
# 
# the program uses argparse to take in the csv file and the directory as
# arguments.
# 

import argparse
import csv
import os
import datetime
import sys
from pathlib import Path
from enum import Enum

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import tkinter.font as tkfont

from PIL import Image, ImageTk

# argparse
parser = argparse.ArgumentParser()
parser.add_argument("csv_file", help="path to csv file")
parser.add_argument("directory", help="path to directory")
parser.add_argument("camera", choices=['canonet', 'fm10'], help="camera model")

# csv enum
class CSV_OLD(Enum):
    SHOT = 0
    EXP_TIME = 1
    APERTURE = 2
    FOCAL_LENGTH = 3
    DATE = 4
    LOCATION = 5
    LONGITUDE = 6
    LATITUDE = 7

class CSV(Enum):
    SHOT = 0
    EXP_TIME = 1
    APERTURE = 2
    FOCAL_LENGTH = 3
    LENS = 4
    LENS_MODEL = 5
    FILM = 6
    ISO = 7
    FORMAT = 8
    DATE = 9
    LOCATION = 10
    LATITUDE = 11
    LONGITUDE = 12
    NOTES = 13
    STARS = 14

def check_exiftool() -> bool:
    """check if exiftool is installed"""
    if os.system("exiftool -ver") == 0:
        print("exiftool is installed.")
        return True
    else:
        return False
    
def get_images(directory: Path) -> list:
    """get all images in a directory"""
    images = []
    for file in directory.iterdir():
        if file.suffix == ".jpg":
            images.append(file)

    # images.sort(key=lambda x: int(x.stem))
    try:
        images.sort(key=lambda x: int(x.stem.split("-")[-1]))
    except ValueError:
        images.sort()

    for image in images:
        print(image)
    return images

def get_exif_data(csv_file: Path, has_header=True) -> list:
    """get exif data from csv file"""
    exif_data = []
    with open(csv_file, newline="") as csvfile:
        reader = csv.reader(csvfile)
        if has_header:
            next(reader, None)
        for row in reader:
            if row:
                exif_data.append(row)
    
    return exif_data

def check_match(images, exif_data) -> bool:
    """check if number of images and number of exif data match"""
    # first get a list of shot #s
    # for row in exif_data:
    #     print(row)

    # for image in images:
    #     print(image)

    if len(images) != len(exif_data):
        print("number of images and number of exif data do not match.")
        return False
        
    return True

def ss_to_float(ss: str) -> float:
    """convert shutter speed (either in the format of 1/Ks or K") to float"""
    if ss == '-':
        return ''

    if ss.endswith('s'):
        return 1 / float(ss[2:-1])
    else:
        return float(ss[:-2])

def main():
    args = parser.parse_args()
    csv_file = Path(args.csv_file)
    directory = Path(args.directory)
    
    # check if exiftool is installed
    if not check_exiftool():
        print("exiftool is not installed. please install it before proceeding.")
        return
    
    # get images
    images = get_images(directory)
    
    # get exif data
    exif_data = get_exif_data(csv_file)
    
    # assign exif data to images
    if not check_match(images, exif_data):
        return
    
    for image, row in zip(images, exif_data):
        shot_num = row[CSV.SHOT.value]
        ss = row[CSV.EXP_TIME.value]
        aperture = row[CSV.APERTURE.value]
        focal_length = row[CSV.FOCAL_LENGTH.value]
        lens = row[CSV.LENS.value]
        lens_model = row[CSV.LENS_MODEL.value]
        film = row[CSV.FILM.value]
        iso = row[CSV.ISO.value]
        film_format = row[CSV.FORMAT.value]
        date = row[CSV.DATE.value]
        location = row[CSV.LOCATION.value]
        latitude = row[CSV.LATITUDE.value]
        longitude = row[CSV.LONGITUDE.value]


        # ss or exposure time must be in float (seconds)
        try:
            ss = ss_to_float(ss)
        except ValueError:
            ss = ''

        # try to convert aperture to float
        try:
            if aperture.startswith("f:"):
                aperture = aperture[2:]
            aperture = float(aperture)
        except ValueError:
            aperture = ''

        # convert date to exif format
        # csv date is in the format of "Dec 13, 2023 at 13:36"
        # exif date is in the format of "2023:12:13 13:36:00"
        date = datetime.datetime.strptime(date, "%b %d, %Y at %H:%M").strftime("%Y:%m:%d %H:%M:%S")

        # longitude and latitude
        if longitude and latitude:
            gps_data = f'-GPSLongitudeRef="W" -GPSLongitude="{longitude}" -GPSLatitudeRef="N" -GPSLatitude="{latitude}" -GPSAltitudeRef="Above Sea Level" -GPSAltitude="0"'
        else:
            gps_data = ""

        # Other exif data
        # print(f'{image} {date} {location} {longitude} {latitude} {ss} {aperture} {focal_length} {iso}')

        ss_cmd = f'-ExposureTime="{ss}" ' if ss else ''
        aperture_cmd = f'-FNumber="{aperture}" ' if aperture else ''

        camera_info = ''
        if args.camera == 'canonet':
            camera_info = f'-Make="Canon" -Model="Canon Canonet QL17 Giii" -LensMake="Canon"'
        elif args.camera == 'fm10':
            camera_info = f'-Make="Nikon" -Model="Nikon FM10" -LensMake="Nikon"'

        # assign exif data
        os.system(
            f'exiftool -overwrite_original '
            f'-AllDates="{date}" '
            f'{gps_data}'
            f'-ImageDescription="{location}" '
            f'-Artist="Muchen He" '
            # f'-ImageUniqueID="{shot_num}" '
            f'{ss_cmd} {aperture_cmd}'
            f'-FocalLength="{focal_length}" -FocalLengthIn35mmFormat="{focal_length}" '
            f'{camera_info} '
            f'-LensModel="{lens_model}" '

            f'-ISO="{iso}" '
            f'{image}'
        )

class ApplyExifApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Apply Exif")
        self.root.geometry("1600x900")

        # paths
        self.csv_path = Path(r'C:\Users\Muchen\Documents\ApplyExif\Wrista_Arista EDU 100_100_Nikon.csv')
        self.photos_path = Path(r'C:\Users\Muchen\Documents\ApplyExif\Example_input')

        # tool bar + buttons
        self.toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
        self.btn_open_csv = tk.Button(self.toolbar, text="Open CSV", command=self.on_open_csv)
        self.btn_open_photo_dir = tk.Button(self.toolbar, text="Open Photos", command=self.on_open_photo_dir)
        self.btn_export = tk.Button(self.toolbar, text="Export", command=self.on_export)

        # pack buttons
        self.btn_open_csv.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_open_photo_dir.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_export.pack(side=tk.LEFT, padx=2, pady=2)

        # pack toolbar
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Create the PanedWindow
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Create the table (Treeview) on the left side
        self.table_frame = tk.Frame(self.paned_window)
        self.tree = ttk.Treeview(self.table_frame, columns=("A", "B", "C"), show='headings')
        self.tree.heading("A", text="Column A")
        self.tree.heading("B", text="Column B")
        self.tree.heading("C", text="Column C")
        self.tree.pack(fill=tk.BOTH, expand=1)

        # Add the table frame to the PanedWindow
        self.paned_window.add(self.table_frame)

        # Create the photo preview on the right side
        self.photo_frame = tk.Frame(self.paned_window)
        self.photo_label = tk.Label(self.photo_frame, text="Photo Preview Here")
        self.photo_label.pack(fill=tk.BOTH, expand=1)

        # Add the photo frame to the PanedWindow
        self.paned_window.add(self.photo_frame)

        self.status_bar = tk.Label(root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # bind root to handlers
        self.root.bind("<Configure>", self.update_window_size)

        # what kind of dataloaded
        self.csv_data_type = None
        self.csv_data_header = None

        # pre-init
        if self.csv_path and self.photos_path and self.csv_path.exists() and self.photos_path.exists():
            self.combined_load()
        else:
            print("big error")

    def update_window_size(self, event):
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.status_bar.config(text=f'Status: Window size {w}x{h}')
    
    # tool bar handlers
    def on_open_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        file_path = Path(file_path)
        if file_path.exists():
            try:
                with open(file_path, newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    data = list(reader)


                    header = data[0]
                    self.csv_data_header = header
                    header_len = len(header)
                    data = data[1:]

                    if header_len == len(CSV_OLD):
                        self.csv_data_type = CSV_OLD
                        
                        # Clear the existing table
                        for widget in self.table_frame.winfo_children():
                            widget.destroy()

                        # add non-editable image column + insert header
                        # header = ['Image'] + header
                        self.tree = ttk.Treeview(self.table_frame, columns=header, show='headings')
                        for col in header:
                            self.tree.heading(col, text=col)
                            self.tree.column(col, width=tkfont.Font().measure(col))
                        
                        # insert remaining rows as data
                        for row in data:
                            self.tree.insert("", tk.END, values=row)
                            # self.tree.insert("", tk.END, values=['-'] + row)

                        self.tree.pack(fill=tk.BOTH, expand=1)
                        # self.tree.bind("<ButtonRelease-1>", self.on_cell_select)
                        self.tree.bind("<Double-1>", self.on_double_click)
                    
            except Exception as e:
                messagebox.showerror("Error", e)

    def on_open_photo_dir(self):
        """get all images in a directory"""
        directory = Path(filedialog.askdirectory())
        if not directory.exists():
            messagebox.showerror("Cannot find directory", f"Cannot find directory. {directory} does not exist or cannot be read")
            return

        image_files = []
        for file in directory.iterdir():
            if file.suffix == ".jpeg":
                image_files.append(file)

        # images.sort(key=lambda x: int(x.stem))
        try:
            image_files.sort(key=lambda x: int(x.stem.split("-")[-1]))
        except ValueError:
            image_files.sort()

        for img in image_files:
            print(img)

        # TODO: CONTINUE
        # self.images = {}
        # for i, img in enumerate(image_files):
        #     self.images[str(i + 1)] = ImageTk.PhotoImage(Image.open(img).resize((20, 20)))
        
        # for i, item in enumerate(self.tree.get_children()):
        #     # assuming first column is for image
        #     first_col_val = self.tree.set(item, column=self.csv_data_header[0])
        #     print(f'first_col_val: {first_col_val}')
        #     set_img = self.images[str(i + 1)]
        #     if set_img:
        #         print(set_img)
        #         self.tree.item(item, image=set_img)

            

    def combined_load(self):
        image_files = []
        for file in self.photos_path.iterdir():
            if file.suffix == ".jpeg":
                image_files.append(file)

        # images.sort(key=lambda x: int(x.stem))
        try:
            image_files.sort(key=lambda x: int(x.stem.split("-")[-1]))
        except ValueError:
            image_files.sort()

        for img in image_files:
            print(img)

        self.photos_preview = []
        self.photos_listpreview = []
        for i, img in enumerate(image_files):
            self.photos_preview.append(ImageTk.PhotoImage(Image.open(img)))
            self.photos_listpreview.append(ImageTk.PhotoImage(Image.open(img).resize((20, 20))))

        # preview
        big_photo = self.photos_preview[0]
        big_label = tk.Label(self.photo_frame, image=big_photo)
        big_label.pack()

        try:
            with open(self.csv_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)


                header = data[0]
                self.csv_data_header = header
                header_len = len(header)
                data = data[1:]

                if header_len == len(CSV_OLD):
                    self.csv_data_type = CSV_OLD
                    
                    # Clear the existing table
                    for widget in self.table_frame.winfo_children():
                        widget.destroy()

                    # add non-editable image column + insert header
                    # header = ['Image'] + header
                    self.tree = ttk.Treeview(self.table_frame, columns=header, show='headings')
                    for col in header:
                        self.tree.heading(col, text=col)
                        self.tree.column(col, width=tkfont.Font().measure(col))
                    
                    # insert remaining rows as data
                    for i, row in enumerate(data):
                        self.tree.insert("", tk.END, values=row, image=self.photos_listpreview[i])
                        # self.tree.insert("", tk.END, values=['-'] + row)

                    self.tree.pack(fill=tk.BOTH, expand=1)
                    # self.tree.bind("<ButtonRelease-1>", self.on_cell_select)
                    self.tree.bind("<Double-1>", self.on_double_click)
                
        except Exception as e:
            messagebox.showerror("Error", e)

    def on_export(self):
        messagebox.showinfo("Export", "")

    # table handlers
    def on_cell_select(self, event):
        selected_item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)
        column_name = self.tree.heading(column)['text']
        # self.tree.set(selected_item, column_name, )
        self.tree.tag_configure('colored', foreground='blue')
        self.tree.item(selected_item, tags=('colored',))

    def on_double_click(self, event):
        region = self.tree.identify('region', event.x, event.y)
        if region == 'cell':
            col = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)
            if row and col:
                col_index = int(col[1:]) -1
                self.edit_cell(row, col_index)

    def edit_cell(self, item, column_index):
        x, y, width, height = self.tree.bbox(item, column=column_index)
        print(f'Editing column: {column_index} ({self.csv_data_header[column_index]})')
        value = self.tree.set(item, column=self.tree['columns'][column_index])

        self.editing_entry = tk.Entry(self.tree, width=width)
        self.editing_entry.place(x=x, y=y, width=width, height=height)
        self.editing_entry.insert(0, value)
        self.editing_entry.focus()

        self.editing_entry.bind('<FocusOut>', lambda e: self.update_cell(item, column_index))
        self.editing_entry.bind('<Return>', lambda e: self.update_cell(item, column_index, True))

    def update_cell(self, item, column_index, from_return=False):
        new_value = self.editing_entry.get()
        self.tree.set(item, column=self.tree['columns'][column_index], value=new_value)
        self.editing_entry.destroy()
        self.editing_entry = None
        if from_return:
            self.tree.focus(item)
            self.tree.selection_set(item)

def main_menu():
    root = tk.Tk()
    app = ApplyExifApp(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main_menu()
        # main()
    except KeyboardInterrupt:
        print("program terminated by user.")
        sys.exit()
    except Exception as e:
        print(e)
