import tkinter as tk
from tkinter import ttk

def shift_rows_down(treeview, selected_index):
    # Get all item IDs in the Treeview
    items = treeview.get_children()
    num_items = len(items)

    if selected_index < 0 or selected_index >= num_items:
        print("Invalid index")
        return

    # Loop through the items from the selected index to the second last item
    for i in range(num_items - 1, selected_index, -1):
        # Get the values of the next item
        next_values = treeview.item(items[i - 1], 'values')
        # Set the current item's values to the next item's values
        treeview.item(items[i], values=next_values)

    # Set the last item's values to the stored values of the row at selected_index
    # treeview.item(items[num_items - 1], values=prev_values)
    treeview.item(items[selected_index], values=["-"] * 3)

# Create the main window
root = tk.Tk()
root.title("Treeview Row Shift")

# Create a Treeview widget
treeview = ttk.Treeview(root, columns=("col1", "col2", "col3"), show='headings')
treeview.heading("col1", text="Column 1")
treeview.heading("col2", text="Column 2")
treeview.heading("col3", text="Column 3")

# Insert some sample data
treeview.insert("", "end", values=("Data 1", "Data 2", "Data 3"))
treeview.insert("", "end", values=("Data 4", "Data 5", "Data 6"))
treeview.insert("", "end", values=("Data 7", "Data 8", "Data 9"))
treeview.insert("", "end", values=("Data 10", "Data 11", "Data 12"))

treeview.pack(fill=tk.BOTH, expand=True)

# Button to shift rows down from the selected index
shift_button = tk.Button(root, text="Shift Rows Down", command=lambda: shift_rows_down(treeview, 1))
shift_button.pack(pady=10)

root.mainloop()
