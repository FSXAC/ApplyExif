import tkinter as tk
from tkinter import ttk

# Example dictionary
data_dict = {
    "Key1": "Value1",
    "Key2": "Value2",
    "Key3": "Value3",
    "Key4": "Value4"
}

# Create main window
root = tk.Tk()
root.title("Dictionary Dropdown")

# Create a label to show the selected value
selected_value_label = tk.Label(root, text="")
selected_value_label.pack(pady=10)

# Function to update label when a key is selected
def on_select(event):
    selected_key = combo.get()
    selected_value = data_dict[selected_key]
    selected_value_label.config(text=f"Selected Value: {selected_value}")

# Create a Combobox with dictionary keys
combo = ttk.Combobox(root, values=list(data_dict.keys()))
combo.pack(pady=10)
combo.bind("<<ComboboxSelected>>", on_select)

# Start the Tkinter event loop
root.mainloop()
