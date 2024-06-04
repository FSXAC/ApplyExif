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

import subprocess
from concurrent.futures import ThreadPoolExecutor

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

    def __int__(self):
        return self.value

CSV_OLD_COLUMN_WIDTH = [
    50,
    70,
    70,
    90,
    200,
    200,
    100,
    100
]

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

CSV_COLUMN_WIDTH = [
    50,
    60,
    60,
    60,
    70,
    70,
    100,
    25,
    30,
    100,
    100,
    80,
    80,
    50,
    50
]

CAMERAS = {
    'canonet': {
        'make': 'Canon',
        'model': 'Canonet QL17 Giii',
    },
    'fm10': {
        'make': 'Nikon',
        'model': 'Nikon FM10'
    },
    'h35n': {
        'make': 'Reto',
        'model': 'Kodak Ektar H35N'
    }
}

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

    # invalid
    if ss == '-':
        return ''
    
    # if ends with 's'
    if ss.endswith('s') or ss.endswith('"'):
        ss = ss[:-1]
    
    # 1/125
    if '/' in ss:
        frac = ss.split('/')[-1]
        return 1 / float(frac)
    
    # 1'30"
    elif '\'' in ss:
        minute, second = ss.split('\'')
        return minute * 60 + second
    
    elif 'm' in ss:
        minute, second = ss.split('m')
        return minute * 60 + second
    
    elif ss.isdecimal():
        return float(ss)

    else:
        print(f'Could not decode shutter speed/long exposure time format: {ss}')

def aperture_to_float(aperture: str) -> float:
    if ':' in aperture:
        return float(aperture.split(':')[-1])
    elif aperture.isdecimal():
        return float(aperture)
    else:
        print(f'Cant parse aperture: {aperture}')

def group_continuous_indices(indices):
    if not indices:
        return []

    indices.sort()
    continuous_groups = []
    current_group = [indices[0]]

    for i in range(1, len(indices)):
        if indices[i] == indices[i-1] + 1:
            current_group.append(indices[i])
        else:
            continuous_groups.append(current_group)
            current_group = [indices[i]]

    continuous_groups.append(current_group)
    return continuous_groups

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

def run_exiftool(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)

class ApplyExifApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Apply Exif")
        self.root.geometry("1980x1080")

        # paths
        self.csv_path = r'C:\Users\Muchen\Pictures\Vinestill\Vinestill_CineStill 400D_400_Canonet.csv'
        self.photos_path = r'C:\Users\Muchen\Pictures\Vinestill'

        # photo data
        self.image_files = []
        self.photos_preview = []
        self.photos_listpreview = []

        # tool bar + buttons
        self.toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
        self.btn_load = tk.Button(self.toolbar, text="Load", command=self.on_load)
        self.btn_export = tk.Button(self.toolbar, text="Export", command=self.on_export)
        self.btn_save_csv = tk.Button(self.toolbar, text="Save CSV")
        self.btn_shift_down = tk.Button(self.toolbar, text="Shift down", command=self.on_shift_down)
        self.btn_remove_row = tk.Button(self.toolbar, text="Remove row", command=self.on_remove_row)
        # self.btn_values_lock = tk.Button(self.toolbar, text="Lock values", command=self.on_values_lock)
        self.btn_autofill = tk.Button(self.toolbar, text="Autofill", command=self.on_autofill)
        self.btn_clear = tk.Button(self.toolbar, text='Clear', command=self.on_clear)
        self.btn_save_csv = tk.Button(self.toolbar, text="Save CSV", command=self.on_save_csv)

        # TODO:
        self.btn_copy_above = tk.Button(self.toolbar, text="Copy above")
        self.btn_copy_below = tk.Button(self.toolbar, text="Copy below")

        # pack buttons
        self.btn_load.pack(side=tk.LEFT)
        self.btn_export.pack(side=tk.LEFT)
        self.btn_shift_down.pack(side=tk.LEFT)
        self.btn_remove_row.pack(side=tk.LEFT)
        # self.btn_values_lock.pack(side=tk.LEFT)
        self.btn_autofill.pack(side=tk.LEFT)
        self.btn_clear.pack(side=tk.LEFT)
        self.btn_save_csv.pack(side=tk.LEFT)

        # Camera select
        self.camera_select = ttk.Combobox(self.toolbar, values=list(CAMERAS.keys()))
        self.camera_select.pack(side=tk.LEFT, padx=10)
        self.camera_select.bind("<<ComboboxSelected>>", self.on_camera_select)

        # Camera select default selection
        self.camera_selected = list(CAMERAS.keys())[0]
        self.camera_select.set(self.camera_selected)

        # pack toolbar
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Create the PanedWindow
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Create the table (Treeview) on the left side
        self.table_frame = ttk.Frame(self.paned_window, width=1600)
        self.tree = None

        # Add the table frame to the PanedWindow
        self.paned_window.add(self.table_frame)

        # Create the photo preview on the right side
        self.photo_frame = ttk.Frame(self.paned_window, width=200)
        self.photo_label = tk.Label(self.photo_frame, text="Photo Preview Here")
        self.photo_label.pack(fill=tk.BOTH, expand=True)

        # Add the photo frame to the PanedWindow
        self.paned_window.add(self.photo_frame)

        self.status_bar = tk.Label(root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # bind root to handlers
        self.root.bind("<Configure>", self.update_window_size)

        # what kind of dataloaded
        self.csv_data_type = None
        self.csv_data_header = None

        self.prev_root_w = None
        self.prev_root_h = None

        self.adjust_pane()

    def adjust_pane(self):
        tot_w = self.paned_window.winfo_width()
        print(f'adjust pane, total width: {tot_w}')
        self.paned_window.sash_place(0, 1600, 0)

    def update_window_size(self, event):
        w, h = self.root.winfo_width(), self.root.winfo_height()
        if self.prev_root_w != w or self.prev_root_h != h:
            self.status_bar.config(text=f'Status: Window size {w}x{h}')
            self.prev_root_h = h
            self.prev_root_w = w

    def on_load(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Files to Load")
        
        # Make the dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # First directory input
        if not isinstance(self.csv_path, tk.StringVar):
            self.csv_path = tk.StringVar(value=self.csv_path)
        if not isinstance(self.photos_path, tk.StringVar):
            self.photos_path = tk.StringVar(value=self.photos_path)
        
        tk.Label(dialog, text="CSV").grid(row=0, column=0)
        self.path1_entry = tk.Entry(dialog, textvariable=self.csv_path, width=50)
        self.path1_entry.grid(row=0, column=1)
        self.browse1_button = tk.Button(dialog, text="Browse", command=lambda: self.browse_csv(self.csv_path, dialog))
        self.browse1_button.grid(row=0, column=2)
        
        # Second directory input
        tk.Label(dialog, text="Photos").grid(row=1, column=0)
        self.path2_entry = tk.Entry(dialog, textvariable=self.photos_path, width=50)
        self.path2_entry.grid(row=1, column=1)
        self.browse2_button = tk.Button(dialog, text="Browse", command=lambda: self.browse_directory(self.photos_path, dialog))
        self.browse2_button.grid(row=1, column=2)
        
        # Ok and Cancel buttons
        self.ok_button = tk.Button(dialog, text="OK", command=lambda: self.on_load_confirm(dialog))
        self.ok_button.grid(row=2, column=2)
        self.cancel_button = tk.Button(dialog, text="Cancel", command=dialog.destroy)
        self.cancel_button.grid(row=2, column=1)
    
    def browse_csv(self, path_var: tk.StringVar, parent):
         # Release grab before opening file dialog
        parent.grab_release()

        csv_file = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        # Re-acquire grab after closing file dialog
        parent.grab_set()
        if csv_file:
            path_var.set(csv_file)

    def browse_directory(self, path_var: tk.StringVar, parent):
        parent.grab_release()
        directory = filedialog.askdirectory()
        parent.grab_set()
        if directory:
            path_var.set(directory)

    def on_load_confirm(self, parent):
        csv_path = self.csv_path.get()
        photos_path = self.photos_path.get()

        e = lambda msg: messagebox.showerror('Load error', msg)

        try:
            csv_path = Path(csv_path)
            if not csv_path or not csv_path.exists():
                raise Exception
        except Exception:
            e(f'CSV path not correct: {csv_path}')

        try:
            photos_path = Path(photos_path)
            if not photos_path or not photos_path.exists():
                raise Exception
        except Exception:
            e(f'Photos path not correct: {photos_path}')
            
        print(csv_path.resolve())
        print(photos_path.resolve())
        self.combined_load(csv_path, photos_path)
        parent.destroy()

    def combined_load(self, csv_path: Path, photos_path: Path):
        self.image_files = []
        for file in photos_path.iterdir():
            if file.suffix == ".jpeg" or file.suffix == '.jpg':
                self.image_files.append(file)

        # images.sort(key=lambda x: int(x.stem))
        try:
            self.image_files.sort(key=lambda x: int(x.stem.split("-")[-1]))
        except ValueError:
            self.image_files.sort()

        self.photos_preview = []
        self.photos_listpreview = []
        for i, img in enumerate(self.image_files):
            source_img = Image.open(img)
            preview_width = 300
            preview_reduce_scale = preview_width / source_img.width
            self.photos_preview.append(ImageTk.PhotoImage(
                source_img.resize((preview_width, int(preview_reduce_scale * source_img.height)))))

            listpreview_width = 30
            listpreview_reduce_scale = listpreview_width / source_img.width
            self.photos_listpreview.append(ImageTk.PhotoImage(
                source_img.resize((listpreview_width, int(listpreview_reduce_scale * source_img.height)))
                ))
            
        print(f'{len(self.photos_preview)} images loaded')

        try:
            with open(csv_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)

                header = data[0]
                self.csv_data_header = header
                header_len = len(header)
                data = [row for row in data[1:] if any(cell.strip() for cell in row)]

                print(f'{len(data)} entries of csv loaded')

                if header_len == len(CSV_OLD):
                    self.csv_data_type = CSV_OLD
                    sel_column_width = CSV_OLD_COLUMN_WIDTH
                elif header_len == len(CSV):
                    self.csv_data_type = CSV
                    sel_column_width = CSV_COLUMN_WIDTH
                else:
                    print("CSV format not recognized")
                    return
                    
                # Clear the existing table
                for widget in self.table_frame.winfo_children():
                    widget.destroy()

                # create a new tree
                self.tree = ttk.Treeview(self.table_frame, columns=header, show='tree headings')

                # configure
                self.tree.tag_configure('oddrow', background='#ffffff')
                self.tree.tag_configure('evenrow', background='#efefef')
                self.tree.tag_configure('values_locked', foreground='#aaa')
                self.tree.tag_configure('edited', foreground='#c60')
                self.tree.tag_configure('auto', foreground='#06c')

                # add columns and headings and set them to pre-specified width
                for i, col in enumerate(header):
                    self.tree.heading(col, text=col, anchor='w')
                    self.tree.column(col, width=sel_column_width[i], anchor='w')

                # id column (where the preview images go)
                self.tree.column('#0', width=50, anchor='w')
                
                # insert remaining rows as data
                for i in range(max(len(data), len(self.photos_listpreview))):
                    tag = 'evenrow' if i % 2 == 0 else 'oddrow'

                    row_data = [''] * len(header)
                    photo_image = None

                    try:
                        row_data = data[i]
                    except IndexError:
                        pass

                    try:
                        photo_image = self.photos_listpreview[i]
                    except IndexError:
                        pass

                    self.tree.insert("", tk.END, values=row_data, image=photo_image, tags=(tag,))

                # set default selection to first
                first_child = self.tree.get_children()[0]
                self.tree.focus(first_child)
                self.tree.selection_set(first_child)

                self.tree.pack(fill=tk.BOTH, expand=1)

                # Force layout update
                self.root.update_idletasks()

                self.tree.bind("<Double-1>", self.on_double_click)
                self.tree.bind("<ButtonRelease-1>", self.on_row_selected)
                
        except Exception as e:
            messagebox.showerror("Error", e)

        self.display_current_preview()

    def display_current_preview(self):
        if self.tree.selection():
            selected_id = self.tree.selection()[-1]
            selected_index = self.tree.index(selected_id)
            if selected_id and selected_index < len(self.photos_preview):
                self.photo_label.config(image = self.photos_preview[selected_index])

    # MARK:
    def on_export(self):
        if not check_exiftool():
            messagebox.showerror('Missing tools', 'Cannot invoke exiftool, please install it')

        children = self.tree.get_children()

        if len(children) != len(self.image_files):
            messagebox.showwarning('Data length mismatch', 'Num of rows of metadata do not match number of photos')


        all_commands = []

        # iso is the same across shots
        roll_iso = None

        for img_file, item in zip(self.image_files, children):

            # defaults and helper functions
            g = lambda c: self.tree.set(item, column=self.tree['columns'][c.value])
            lens_model = None

            if self.csv_data_type == CSV_OLD:
                ss = g(CSV_OLD.EXP_TIME)
                aperture = g(CSV_OLD.APERTURE)
                focal_length = g(CSV.FOCAL_LENGTH)
                date = g(CSV_OLD.DATE)
                location = g(CSV_OLD.LOCATION)
                longitude = g(CSV_OLD.LONGITUDE)
                latitude = g(CSV_OLD.LATITUDE)
                
                # need to manually provide iso and lens_model
                if not roll_iso:
                    roll_iso = messagebox.askquestion("Enter ISO manually")

            elif self.csv_data_type == CSV:
                ss = g(CSV.EXP_TIME)
                aperture = g(CSV.APERTURE)
                focal_length = g(CSV.FOCAL_LENGTH)
                lens_model = g(CSV.LENS_MODEL)
                date = g(CSV.DATE)
                location = g(CSV.LOCATION)
                latitude = g(CSV.LATITUDE)
                longitude = g(CSV.LONGITUDE)

                if not roll_iso:
                    roll_iso = g(CSV.ISO)
            else:
                pass

            # ss or exposure time must be in float (seconds)
            try:
                ss = ss_to_float(ss)
            except ValueError:
                ss = ''

            # try to convert aperture to float
            try:
                aperture = aperture_to_float(aperture)
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

            # camera info
            camera_info_dict = CAMERAS[self.camera_selected]

            # assign exif data
            all_commands.append(
                f'exiftool -overwrite_original '
                f'-AllDates="{date}" '
                f'{gps_data}'
                f'-ImageDescription="{location}" '
                f'-Artist="Muchen He" '
                f'{ss_cmd} {aperture_cmd}'
                f'-FocalLength="{focal_length}" -FocalLengthIn35mmFormat="{focal_length}" '
                f'-Make="{camera_info_dict["make"]}" '
                f'-LensMake="{camera_info_dict["make"]}" '
                f'-Model="{camera_info_dict["model"]}" '
                f'-LensModel="{lens_model}" '
                f'-ISO="{roll_iso}" '
                f'{img_file}'
            )
        
        print(all_commands)

        return
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(run_exiftool, cmd) for cmd in all_commands]
            for future in futures:
                future.result()

        print('finished running exiftool')

    def on_shift_down(self):
        """
        shift the data in self.tree down
        """

        # TODO: what if num children is 0?
        # need to return early (doesn't do anything)
        
        # first check if last row of tree contains emtpy data
        # if not, insert a new empty row

        if not self.last_row_is_empty():
            tag = 'evenrow' if len(self.tree.get_children()) % 2 == 0 else 'oddrow'
            self.tree.insert("", tk.END, values=self.empty_row(), tags=(tag,))
        else:
            print("Last row is still empty, can't shift row from here")
        
        # then shift all rows down until we get to current index
        children = self.tree.get_children()
        num_children = len(children)
        first_selected_index = self.tree.index(self.tree.selection()[0])
        for i in range(num_children - 1, first_selected_index, -1):
            new_vals = self.tree.item(children[i - 1], 'values')
            self.tree.item(children[i], values=new_vals)

        # replace sel row with empty row
        self.tree.item(children[first_selected_index], values=self.empty_row())

    def on_remove_row(self):
        """
        Reverse of on_shift_downs
        """
        children = self.tree.get_children()
        num_children = len(children)
        first_selected_index = self.tree.index(self.tree.selection()[0])
        for i in range(first_selected_index, num_children):
            if i != num_children - 1:
                new_vals = self.tree.item(children[i + 1], 'values')
                self.tree.item(children[i], values=new_vals)
            else:
                # remove row (but do not delete if there are preview images)
                if len(children) > len(self.photos_listpreview):
                    self.tree.delete(children[i])
                else:
                    print('Tried to remove row, but there are more photos, so removal is cancelled')
                    self.tree.item(children[i], values=self.empty_row())

    def add_tags(self, items, tags: list):
        for i in items:
            curr_tags = self.tree.item(i, 'tags')
            self.tree.item(i, tags=curr_tags + tuple(tags))

    def remove_tags(self, items: list, tags: list):
        for i in items:
            curr_tags = self.tree.item(i, 'tags')
            new_tags = tuple(t for t in curr_tags if t not in tags)
            self.tree.item(i, tags=new_tags)

    def on_values_lock(self):
        self.add_tags(self.tree.selection(), ['values_locked'])

    def empty_row(self) -> tuple:
        return tuple([''] * len(self.csv_data_header))

    def last_row_is_empty(self) -> bool:
        if not self.tree:
            raise ValueError("no csv file loaded")
        
        children = self.tree.get_children()
        if not children:
            return False  # Treeview is empty

        last_child = children[-1]
        values = self.tree.item(last_child, 'values')
        return all(v == "" or v is None for v in values)
    
    def on_row_selected(self, event):
        self.display_current_preview()

    def on_double_click(self, event):
        region = self.tree.identify('region', event.x, event.y)
        if region == 'cell':
            col = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)
            if row and col:
                col_index = int(col[1:]) -1
                self.edit_generic_cell(row, col_index)

    def edit_generic_cell(self, item, column_index):
        x, y, width, height = self.tree.bbox(item, column=column_index)
        print(f'Editing column: {column_index} ({self.csv_data_header[column_index]})')
        value = self.tree.set(item, column=self.tree['columns'][column_index])

        self.editing_entry = tk.Entry(self.tree, width=width)
        self.editing_entry.place(x=x, y=y, width=width, height=height)
        self.editing_entry.insert(0, value)
        self.editing_entry.focus()

        self.editing_entry.bind('<FocusOut>', lambda e: self.update_cell(item, column_index, prev_value=value))
        self.editing_entry.bind('<Return>', lambda e: self.update_cell(item, column_index, True, prev_value=value))

    def update_cell(self, item, column_index, from_return=False, prev_value=None):
        new_value = self.editing_entry.get()
        if new_value != prev_value:
            self.tree.set(item, column=self.tree['columns'][column_index], value=new_value)
            self.add_tags((item, ), ['edited'])
            self.remove_tags((item, ), ['auto'])

        self.editing_entry.destroy()
        self.editing_entry = None
        if from_return:
            self.tree.focus(item)
            self.tree.selection_set(item)

    def on_autofill(self):
        # get all selections
        selected = self.tree.selection()
        selected_indices = [ self.tree.index(item) for item in selected ]

        # factor out ids into continuous groups
        grouped_selections = group_continuous_indices(selected_indices)
        for group in grouped_selections:
            for col_index, col in enumerate(self.csv_data_header):
                print(f'[autofill] working on "{col}" (index {col_index})')
                self.autofill_group(group, col_index)

        self.add_tags(selected, ['auto'])
        self.remove_tags(selected, ['edited'])
    
    def autofill_group(self, indices, col_index):
        children = self.tree.get_children()
        col = self.tree['columns'][col_index]
        is_date_col = col_index == self.csv_data_type.DATE.value
        ref_start_index = max(0, indices[0] - 1)
        ref_end_index = indices[-1] + 1
        ref_start = None
        ref_end = None

        print(f'start+1: {ref_start_index} end+1: {ref_end_index}; out of {len(children)}')

        try:
            ref_start = self.tree.set(children[ref_start_index], column=col)
        except IndexError:
            pass

        try:
            ref_end = self.tree.set(children[ref_end_index], column=col)
        except IndexError:
            pass
        
        # Handle all the cases

        # If everything is selected
        if ref_start_index < 0 and ref_end_index >= len(children):
            print('[autofill] Both starting and end ref index out of range. whole list selected?')
            print('[autofill] Oops, bulk autofil is not supported yet... pls retry')
            return
        

        # if only end has valid value
        if not ref_start and ref_end:
            print('[autofill] start ref not avail, only using end ref')

            if is_date_col:

                # if there is only end ref, and we need to add date/time,
                # subtract 1 minute for each entry from the end
                ref_end_dt = datetime.datetime.strptime(ref_end, "%b %d, %Y at %H:%M")
                for offset, i in enumerate(reversed(indices)):
                    new_dt = ref_end_dt - datetime.timedelta(minutes=(offset + 1))
                    new_date_value = datetime.datetime.strftime(new_dt, "%b %d, %Y at %H:%M")
                    self.tree.set(children[i], column=col, value=new_date_value)
            else:
                for i in indices:
                    self.tree.set(children[i], column=col, value=ref_end)

            return

        
        if ref_start and not ref_end:
            print('[autofill] end ref not avail, only using start ref')

            if is_date_col:
                # same as previously, but add 1 minute
                ref_start_dt = datetime.datetime.strptime(ref_start, "%b %d, %Y at %H:%M")
                for offset, i in enumerate(indices):
                    new_dt = ref_start_dt + datetime.timedelta(minutes=(offset + 1))
                    new_date_value = datetime.datetime.strftime(new_dt, "%b %d, %Y at %H:%M")
                    self.tree.set(children[i], column=col, value=new_date_value)

            else:
                for i in indices:
                    self.tree.set(children[i], column=col, value=ref_start)

            return
        
        elif ref_start and ref_end:
            
            # if start and end reference is same, then we can fill everything in between as the same
            if ref_start == ref_end:
                for i in indices:
                    self.tree.set(children[i], column=col, value=ref_start)

            # NOTE: not ideal to do this
            elif is_date_col:
                # interprelate date
                ref_start_dt = datetime.datetime.strptime(ref_start, "%b %d, %Y at %H:%M")
                ref_end_dt = datetime.datetime.strptime(ref_end, "%b %d, %Y at %H:%M")

                # for num of rows to update, give evenly spreadout timestamps
                time_step = (ref_end_dt - ref_start_dt) / (len(indices) + 1)
                for mult, i in enumerate(indices):
                    new_time_value = datetime.datetime.strftime((ref_start_dt + ((mult + 1) * time_step)), "%b %d, %Y at %H:%M")
                    self.tree.set(children[i], column=col, value=new_time_value)

        else:
            print('oops')

    def on_save_csv(self):
        print(f'Saving back CSV to {self.csv_path.get()}')
        with open(Path(self.csv_path.get()), 'w', newline='') as outfile:
            csv_writer = csv.writer(outfile)
            csv_writer.writerow(self.csv_data_header)

            # write the data
            for row_id in self.tree.get_children():
                row = self.tree.item(row_id)['values']
                csv_writer.writerow(row)

    def on_clear(self):
        for item in self.tree.selection():
            self.tree.item(item, values=self.empty_row())

    def on_camera_select(self, event):
        self.camera_selected = self.camera_select.get()

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
