const fileBrowserModalProxy = {
  isOpen: false,
  isLoading: false,

  browser: {
    title: "File Browser",
    currentPath: "",
    entries: [],
    parentPath: "",
    sortBy: "name",
    sortDirection: "asc",
  },
  searchTerm: "",
  filteredEntries: [],
  selectedFiles: [],
  allFilesSelected: false,

  // Initialize navigation history
  history: [],

  async openModal(path) {
    const modalEl = document.getElementById("fileBrowserModal");
    const modalAD = Alpine.$data(modalEl);

    modalAD.isOpen = true;
    modalAD.isLoading = true;
    modalAD.history = []; // reset history when opening modal

    // Initialize currentPath to root if it's empty
    if (path) modalAD.browser.currentPath = path;
    else if (!modalAD.browser.currentPath)
      modalAD.browser.currentPath = "/"; // Start at root if no path specified

    await modalAD.fetchFiles(modalAD.browser.currentPath);
    modalAD.selectedFiles = [];
    modalAD.allFilesSelected = false;
  },

  isArchive(filename) {
    const archiveExts = ["zip", "tar", "gz", "rar", "7z"];
    const ext = filename.split(".").pop().toLowerCase();
    return archiveExts.includes(ext);
  },

  async fetchFiles(path = "") {
    this.isLoading = true;
    try {
      const response = await fetch(
        `/get_work_dir_files?path=${encodeURIComponent(path)}`
      );

      if (response.ok) {
        const data = await response.json();
        this.browser.entries = data.data.entries;
        this.browser.currentPath = data.data.current_path;
        this.browser.parentPath = data.data.parent_path;
        this.filterEntries(); // Apply filter after fetching
        this.selectedFiles = []; // Clear selection on new folder load
        this.allFilesSelected = false; // Uncheck select all
      } else {
        console.error("Error fetching files:", await response.text());
        this.browser.entries = [];
        this.filteredEntries = [];
      }
    } catch (error) {
      window.toastFetchError("Error fetching files", error);
      this.browser.entries = [];
      this.filteredEntries = [];
    } finally {
      this.isLoading = false;
    }
  },

  filterEntries() {
    const term = this.searchTerm.toLowerCase();
    this.filteredEntries = this.browser.entries.filter(entry =>
      entry.name.toLowerCase().includes(term)
    );
  },

  toggleSelectAll() {
    if (this.allFilesSelected) {
      this.selectedFiles = this.filteredEntries.map(file => file.path);
    } else {
      this.selectedFiles = [];
    }
  },

  async deleteFile(file) {
    if (!confirm(`Are you sure you want to delete ${file.name}?`)) {
      return;
    }
    await this._performDelete([file.path]);
  },

  async deleteSelectedFiles() {
    if (this.selectedFiles.length === 0) {
      alert("No files selected for deletion.");
      return;
    }
    if (!confirm(`Are you sure you want to delete ${this.selectedFiles.length} selected files?`)) {
      return;
    }
    await this._performDelete(this.selectedFiles);
  },

  async _performDelete(pathsToDelete) {
    this.isLoading = true;
    try {
      const response = await fetch("/delete_work_dir_files", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          paths: pathsToDelete,
          currentPath: this.browser.currentPath,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Filter out deleted files from both browser.entries and filteredEntries
        const deletedPaths = data.data.deleted_paths;
        this.browser.entries = this.browser.entries.filter(entry => !deletedPaths.includes(entry.path));
        this.filterEntries(); // Re-apply filter after deletion
        this.selectedFiles = []; // Clear selection after deletion
        this.allFilesSelected = false; // Uncheck select all
        alert("Selected files deleted successfully.");
      } else {
        alert(`Error deleting files: ${await response.text()}`);
      }
    } catch (error) {
      window.toastFetchError("Error deleting files", error);
      alert("Error deleting files");
    } finally {
      this.isLoading = false;
    }
  },

  async navigateToFolder(path) {
    // Push current path to history before navigating
    if (this.browser.currentPath !== path) {
      this.history.push(this.browser.currentPath);
    }
    await this.fetchFiles(path);
  },

  async navigateUp() {
    if (this.browser.parentPath !== "") {
      // Push current path to history before navigating up
      this.history.push(this.browser.currentPath);
      await this.fetchFiles(this.browser.parentPath);
    }
  },

  sortFiles(entries) {
    return [...entries].sort((a, b) => {
      // Folders always come first
      if (a.is_dir !== b.is_dir) {
        return a.is_dir ? -1 : 1;
      }

      const direction = this.browser.sortDirection === "asc" ? 1 : -1;
      switch (this.browser.sortBy) {
        case "name":
          return direction * a.name.localeCompare(b.name);
        case "size":
          return direction * (a.size - b.size);
        case "date":
          return direction * (new Date(a.modified) - new Date(b.modified));
        default:
          return 0;
      }
    });
  },

  toggleSort(column) {
    if (this.browser.sortBy === column) {
      this.browser.sortDirection =
        this.browser.sortDirection === "asc" ? "desc" : "asc";
    } else {
      this.browser.sortBy = column;
      this.browser.sortDirection = "asc";
    }
  },



  async handleFileUpload(event) {
    try {
      const files = event.target.files;
      if (!files.length) return;

      const formData = new FormData();
      formData.append("path", this.browser.currentPath);

      for (let i = 0; i < files.length; i++) {
        const ext = files[i].name.split(".").pop().toLowerCase();
        if (!["zip", "tar", "gz", "rar", "7z"].includes(ext)) {
          if (files[i].size > 100 * 1024 * 1024) {
            // 100MB
            alert(
              `File ${files[i].name} exceeds the maximum allowed size of 100MB.`
            );
            continue;
          }
        }
        formData.append("files[]", files[i]);
      }

      // Proceed with upload after validation
      const response = await fetch("/upload_work_dir_files", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        // Update the file list with new data
        this.browser.entries = data.data.entries.map((entry) => ({
          ...entry,
          uploadStatus: data.failed.includes(entry.name) ? "failed" : "success",
        }));
        this.browser.currentPath = data.data.current_path;
        this.browser.parentPath = data.data.parent_path;

        // Show success message
        if (data.failed && data.failed.length > 0) {
          const failedFiles = data.failed
            .map((file) => `${file.name}: ${file.error}`)
            .join("\n");
          alert(`Some files failed to upload:\n${failedFiles}`);
        }
      } else {
        alert(data.message);
      }
    } catch (error) {
      window.toastFetchError("Error uploading files", error);
      alert("Error uploading files");
    }
  },

  async downloadFile(file) {
    try {
      const downloadUrl = `/download_work_dir_file?path=${encodeURIComponent(
        file.path
      )}`;

      const response = await fetch(downloadUrl);

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const blob = await response.blob();

      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = file.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(link.href);
    } catch (error) {
      window.toastFetchError("Error downloading file", error);
      alert("Error downloading file");
    }
  },

  // Breadcrumbs logic
  getBreadcrumbs() {
    const pathParts = this.browser.currentPath.split('/').filter(p => p !== '');
    let currentPath = '';
    const breadcrumbs = [{
      name: 'root',
      path: '/'
    }]; // Always start with root

    for (let i = 0; i < pathParts.length; i++) {
      currentPath += '/' + pathParts[i];
      breadcrumbs.push({
        name: pathParts[i],
        path: currentPath
      });
    }
    return breadcrumbs;
  },

  // New Folder and File creation
  async createNewFolder() {
    const folderName = prompt('Enter new folder name:');
    if (!folderName) return;

    const newPath = `${this.browser.currentPath}${folderName}`;
    this.isLoading = true;
    try {
      const response = await fetch('/create_work_dir_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newPath, currentPath: this.browser.currentPath })
      });
      if (response.ok) {
        await this.fetchFiles(this.browser.currentPath);
        alert(`Folder '${folderName}' created successfully.`);
      } else {
        alert(`Error creating folder: ${await response.text()}`);
      }
    } catch (error) {
      window.toastFetchError('Error creating folder', error);
      alert('Error creating folder');
    } finally {
      this.isLoading = false;
    }
  },

  async createNewFile() {
    const fileName = prompt('Enter new file name:');
    if (!fileName) return;

    const newPath = `${this.browser.currentPath}${fileName}`;
    this.isLoading = true;
    try {
      const response = await fetch('/create_work_dir_file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newPath, currentPath: this.browser.currentPath })
      });
      if (response.ok) {
        await this.fetchFiles(this.browser.currentPath);
        alert(`File '${fileName}' created successfully.`);
      } else {
        alert(`Error creating file: ${await response.text()}`);
      }
    } catch (error) {
      window.toastFetchError('Error creating file', error);
      alert('Error creating file');
    } finally {
      this.isLoading = false;
    }
  },

  // File content viewing
  async openFileForView(filePath) {
    this.isLoading = true;
    try {
      const response = await fetch(`/read_work_dir_file?path=${encodeURIComponent(filePath)}`);
      if (response.ok) {
        const content = await response.text();
        window.genericModalProxy.openModal('File Content', `<pre>${escapeHTML(content)}</pre>`);
      } else {
        alert(`Error reading file: ${await response.text()}`);
      }
    } catch (error) {
      window.toastFetchError('Error reading file', error);
      alert('Error reading file');
    } finally {
      this.isLoading = false;
    }
  },

  // Helper for dynamic file icons
  getFileIcon(file) {
    if (file.is_dir) {
      return '/public/folder.svg';
    } else if (this.isArchive(file.name)) {
      return '/public/archive.svg';
    } else {
      // Map common file types to icons, default to 'file.svg'
      const fileTypeIcons = {
        'txt': 'document',
        'md': 'document',
        'pdf': 'document',
        'json': 'code',
        'py': 'code',
        'js': 'code',
        'html': 'code',
        'css': 'code',
        'svg': 'image',
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image',
        'gif': 'image',
        'mp4': 'video',
        'mov': 'video',
        'avi': 'video',
        'mp3': 'audio',
        'wav': 'audio',
        'ogg': 'audio',
      };
      const ext = file.name.split('.').pop().toLowerCase();
      return `/public/${fileTypeIcons[ext] || 'file'}.svg`;
    }
  },

  // Utility to escape HTML for safe display in <pre>
  escapeHTML(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  },

  // Helper Functions
  formatFileSize(size) {
    if (size === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(size) / Math.log(k));
    return parseFloat((size / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  },

  formatDate(dateString) {
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  },

  handleClose() {
    this.isOpen = false;
  },
};

// Wait for Alpine to be ready
document.addEventListener("alpine:init", () => {
  Alpine.data("fileBrowserModalProxy", () => ({
    init() {
      Object.assign(this, fileBrowserModalProxy);
      // Ensure immediate file fetch when modal opens
      this.$watch("isOpen", async (value) => {
        if (value) {
          await this.fetchFiles(this.browser.currentPath);
        }
      });

      // Watch for changes in filteredEntries to update allFilesSelected
      this.$watch('selectedFiles', (newSelectedFiles) => {
        this.allFilesSelected = newSelectedFiles.length > 0 && newSelectedFiles.length === this.filteredEntries.length;
      });
    },
  }));
});

// Keep the global assignment for backward compatibility
window.fileBrowserModalProxy = fileBrowserModalProxy;

openFileLink = async function (path) {
  try {
    const resp = await window.sendJsonData("/file_info", { path });
    if (!resp.exists) {
      window.toast("File does not exist.", "error");
      return;
    }

    if (resp.is_dir) {
      fileBrowserModalProxy.openModal(resp.abs_path);
    } else {
      fileBrowserModalProxy.downloadFile({
        path: resp.abs_path,
        name: resp.file_name,
      });
    }
  } catch (e) {
    window.toastFetchError("Error opening file", e);
  }
};
window.openFileLink = openFileLink;

// Added for the new file creation features - need a generic modal for prompts/viewing
function escapeHTML(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
