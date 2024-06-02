import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

def adjust_column_width(tree):
    for col in tree['columns']:
        # Measure the width of the column header text
        font = tkfont.Font()
        header_text = tree.heading(col, 'text')
        header_width = font.measure(header_text)
        tree.column(col, width=header_width)

# Example usage
root = tk.Tk()
columns = ("A", "B", "C")
tree = ttk.Treeview(root, columns=columns)

# Add headings
tree.heading("A", text="Column A")
tree.heading("B", text="Column B")
tree.heading("C", text="C")

# Adjust column widths based on header text
adjust_column_width(tree)

tree.pack()
root.mainloop()