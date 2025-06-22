import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import api_client
import os

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TECMFS Client")
        self.geometry("800x600")
        
        # Style
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # --- Frames ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(side="top", fill="x")

        middle_frame = ttk.Frame(self, padding="10")
        middle_frame.pack(fill="both", expand=True)

        status_frame = ttk.Frame(self, padding="5")
        status_frame.pack(side="bottom", fill="x")

        # --- Top Frame: Search and Actions ---
        ttk.Label(top_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.bind("<Return>", self.search_files)

        ttk.Button(top_frame, text="Search", command=self.search_files).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Clear", command=self.refresh_file_list).pack(side="left", padx=5)
        
        # --- Middle Frame: File List ---
        self.file_list_box = tk.Listbox(middle_frame, selectmode=tk.SINGLE)
        self.file_list_box.pack(side="left", fill="both", expand=True)

        # Scrollbar for the listbox
        scrollbar = ttk.Scrollbar(middle_frame, orient="vertical", command=self.file_list_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_list_box.config(yscrollcommand=scrollbar.set)
        
        # --- Right Frame: Buttons ---
        button_frame = ttk.Frame(middle_frame, padding="10")
        button_frame.pack(side="right", fill="y")
        
        ttk.Button(button_frame, text="Refresh List", command=self.refresh_file_list).pack(pady=5, fill="x")
        ttk.Button(button_frame, text="Upload File", command=self.upload_file).pack(pady=5, fill="x")
        ttk.Button(button_frame, text="Download File", command=self.download_file).pack(pady=5, fill="x")
        ttk.Button(button_frame, text="Delete File", command=self.delete_file).pack(pady=15, fill="x")
        ttk.Button(button_frame, text="Block Status", command=self.show_block_status).pack(side="bottom", pady=10, fill="x")

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Welcome to TECMFS!")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_label.pack(fill="x")

        # --- Data ---
        self.files_data = []
        self.refresh_file_list()

    def set_status(self, message, is_error=False):
        self.status_var.set(message)
        print(message)
        if is_error:
            messagebox.showerror("Error", message)

    def refresh_file_list(self):
        self.set_status("Refreshing file list...")
        self.search_var.set("") # Clear search bar
        files = api_client.get_files()
        self.file_list_box.delete(0, tk.END)
        if files is not None:
            self.files_data = files
            for file_info in self.files_data:
                display_text = f"{file_info['filename']} (Size: {file_info['size']} bytes)"
                self.file_list_box.insert(tk.END, display_text)
            self.set_status(f"Found {len(files)} files.")
        else:
            self.files_data = []
            self.set_status("Could not fetch file list from controller.", is_error=True)

    def search_files(self, event=None):
        query = self.search_var.get()
        if not query:
            self.refresh_file_list()
            return
        
        self.set_status(f"Searching for '{query}'...")
        results = api_client.search_files(query)
        self.file_list_box.delete(0, tk.END)
        if results is not None:
            self.files_data = results
            for file_info in self.files_data:
                display_text = f"{file_info['filename']} (Size: {file_info['size']} bytes)"
                self.file_list_box.insert(tk.END, display_text)
            self.set_status(f"Found {len(results)} results for '{query}'.")
        else:
            self.files_data = []
            self.set_status(f"Error searching for '{query}'.", is_error=True)
            
    def upload_file(self):
        filepath = filedialog.askopenfilename(title="Select a file to upload")
        if not filepath:
            return
        
        self.set_status(f"Uploading {os.path.basename(filepath)}...")
        result = api_client.upload_file(filepath)
        if result:
            self.set_status(f"Successfully uploaded file: {result.get('filename')}")
            self.refresh_file_list()
        else:
            self.set_status(f"Failed to upload {os.path.basename(filepath)}.", is_error=True)

    def get_selected_file(self):
        selection_indices = self.file_list_box.curselection()
        if not selection_indices:
            self.set_status("Please select a file from the list first.", is_error=True)
            return None
        
        selected_index = selection_indices[0]
        return self.files_data[selected_index]

    def download_file(self):
        selected_file = self.get_selected_file()
        if not selected_file:
            return

        save_dir = filedialog.askdirectory(title="Select directory to save file")
        if not save_dir:
            return
            
        file_id = selected_file['file_id']
        filename = selected_file['filename']
        self.set_status(f"Downloading {filename}...")
        
        save_path = api_client.download_file(file_id, filename, save_dir)
        if save_path:
            self.set_status(f"File downloaded successfully to {save_path}")
            messagebox.showinfo("Success", f"File saved to:\n{save_path}")
        else:
            self.set_status(f"Failed to download {filename}.", is_error=True)
            
    def delete_file(self):
        selected_file = self.get_selected_file()
        if not selected_file:
            return

        file_id = selected_file['file_id']
        filename = selected_file['filename']
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{filename}'?"):
            return

        self.set_status(f"Deleting {filename}...")
        success = api_client.delete_file(file_id)
        if success:
            self.set_status(f"Successfully deleted {filename}.")
            self.refresh_file_list()
        else:
            self.set_status(f"Failed to delete {filename}.", is_error=True)

    def show_block_status(self):
        self.set_status("Fetching block status...")
        status_data = api_client.get_block_status()

        if status_data is None:
            self.set_status("Failed to fetch block status.", is_error=True)
            return

        # Create a new top-level window
        status_window = tk.Toplevel(self)
        status_window.title("TECMFS Block Status")
        status_window.geometry("700x500")

        # Create a Treeview
        tree = ttk.Treeview(status_window, columns=("Disk", "Type"), show="tree headings")
        tree.heading("#0", text="File / Block ID")
        tree.heading("Disk", text="Disk ID")
        tree.heading("Type", text="Block Type")
        tree.column("#0", width=400)
        tree.column("Disk", width=100, anchor="center")
        tree.column("Type", width=100, anchor="center")

        # Populate the Treeview with data
        for file_info in status_data:
            # Parent node for the file
            file_node = tree.insert("", "end", text=file_info['filename'], open=True)
            
            # Child nodes for each block
            for block_info in file_info['blocks']:
                tree.insert(file_node, "end", text=f"  - {block_info['block_id']}", 
                            values=(block_info['disk_id'], block_info['type']))
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.set_status("Block status loaded successfully.")

if __name__ == "__main__":
    app = App()
    app.mainloop() 