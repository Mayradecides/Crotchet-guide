import json
from pathlib import Path

import customtkinter as ctk
from tkinter import BooleanVar, PhotoImage, messagebox, simpledialog

from stitch_counter import Project


PROJECTS_FILE = Path(__file__).with_name("projects.json")
SAVE_FILE = Path(__file__).with_name("stitch_counter_save.json")


class App(ctk.CTk):
	def __init__(self):
		super().__init__()
		ctk.set_appearance_mode("System")
		ctk.set_default_color_theme("blue")
		self.title("Crotchet")
		self._set_window_icon()
		self.resizable(True, True)
		self.geometry("460x560")
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)
		self.content_frame = ctk.CTkScrollableFrame(self)
		self.content_frame.grid(row=0, column=0, sticky="nsew")

		self.project_name = ctk.StringVar(value="")
		self.project_type = ctk.StringVar(value="")
		self.section_name = ctk.StringVar(value="Section 1")
		self.yarn_name = ctk.StringVar(value="")
		self.stitches_input = ctk.StringVar(value="")
		self.required_stitches = ctk.StringVar(value="")
		self.hook_type = ctk.StringVar(value="")
		self.done_var = BooleanVar(value=False)
		self.saved_projects = self._load_saved_projects()
		self._loaded_notes = ""
		self._submitted_name = ""
		self._project = None
		self._required_stitches = 0
		self._previous_stitches = 0
		self._total_stitches = 0
		self._yarn_trace_id = None
		self._suspend_autosave = False

		loaded_state = self._load_active_project_state()
		if loaded_state:
			self._apply_active_project_state(loaded_state)
			self._build_tracker_screen()
		else:
			self._build_project_screen()

	def _set_window_icon(self):
		icon = PhotoImage(width=32, height=32)
		icon.put("#f7f7f7", to=(0, 0, 32, 32))

		def set_pixel(x, y, color):
			icon.put(color, to=(x, y, x + 1, y + 1))

		for x in range(3, 19):
			for y in range(7, 25):
				if (x - 10) ** 2 + (y - 16) ** 2 <= 64:
					set_pixel(x, y, "#2d6cdf")

		for x in range(6, 16):
			set_pixel(x, 12 + (x - 6) // 2, "#dbe7ff")
			set_pixel(x, 19 - (x - 6) // 2, "#dbe7ff")

		for x in range(4, 9):
			set_pixel(x, 16, "#ffffff")
			set_pixel(x, 15, "#ffffff")

		for x in range(20, 25):
			set_pixel(x, 8, "#6d6d6d")
			set_pixel(x, 9, "#6d6d6d")
		for y in range(9, 20):
			set_pixel(24, y, "#6d6d6d")
		set_pixel(23, 19, "#6d6d6d")
		set_pixel(22, 20, "#6d6d6d")
		set_pixel(21, 20, "#6d6d6d")
		for x in range(20, 24):
			set_pixel(x, 21, "#6d6d6d")
		set_pixel(19, 8, "#6d6d6d")
		set_pixel(19, 7, "#6d6d6d")
		set_pixel(18, 7, "#6d6d6d")
		self._window_icon = icon
		self.iconphoto(True, icon)

	def _load_saved_projects(self):
		if not PROJECTS_FILE.exists():
			return []

		try:
			with PROJECTS_FILE.open("r", encoding="utf-8") as file_handle:
				projects = json.load(file_handle)
			return projects if isinstance(projects, list) else []
		except (OSError, json.JSONDecodeError):
			return []

	def _load_active_project_state(self):
		if not SAVE_FILE.exists():
			return None

		try:
			with SAVE_FILE.open("r", encoding="utf-8") as file_handle:
				project_state = json.load(file_handle)
		except (OSError, json.JSONDecodeError):
			return None

		if not isinstance(project_state, dict):
			return None

		project_name = str(project_state.get("project_name", project_state.get("name", ""))).strip()
		if not project_name:
			return None

		sections = project_state.get("sections")
		if not isinstance(sections, list) or not sections:
			return None

		return project_state

	def _get_primary_section_state(self, project_state):
		sections = project_state.get("sections")
		if isinstance(sections, list) and sections:
			section_state = sections[0]
			if isinstance(section_state, dict):
				return section_state
		return {}

	def _apply_active_project_state(self, project_state):
		section_state = self._get_primary_section_state(project_state)
		self._suspend_autosave = True
		self.project_name.set(str(project_state.get("project_name", project_state.get("name", ""))))
		self.project_type.set(str(project_state.get("project_type", "")))
		self.section_name.set(str(section_state.get("name", "Section 1")))
		self._required_stitches = int(section_state.get("total_rows", project_state.get("required_stitches", 0)))
		self._previous_stitches = int(section_state.get("previous_row", project_state.get("previous_stitches", 0)))
		self._total_stitches = int(section_state.get("current_row", project_state.get("total_stitches", 0)))
		self.yarn_name.set(str(section_state.get("yarn", project_state.get("yarn", ""))))
		self.hook_type.set(str(section_state.get("hook", project_state.get("hook", ""))))
		self.required_stitches.set(str(self._required_stitches) if self._required_stitches else "")
		self.done_var.set(bool(section_state.get("done", project_state.get("done", False))))
		self._loaded_notes = str(section_state.get("notes", project_state.get("notes", "")))
		self._submitted_name = self.project_name.get().strip()
		self._project = Project(self._submitted_name)
		self._suspend_autosave = False

	def _current_project_state(self):
		section_name = self.section_name.get().strip() or "Section 1"
		notes = self.notes_box.get("1.0", "end-1c").strip() if hasattr(self, "notes_box") else ""
		section_state = {
			"name": section_name,
			"total_rows": self._required_stitches,
			"current_row": self._total_stitches,
			"previous_row": self._previous_stitches,
			"notes": notes,
			"yarn": self.yarn_name.get().strip(),
			"hook": self.hook_type.get().strip(),
			"done": bool(self.done_var.get()),
		}
		return {
			"project_name": self.project_name.get().strip(),
			"project_type": self.project_type.get().strip(),
			"sections": [section_state],
			"name": self.project_name.get().strip(),
			"yarn": self.yarn_name.get().strip(),
			"hook": self.hook_type.get().strip(),
			"required_stitches": self._required_stitches,
			"previous_stitches": self._previous_stitches,
			"total_stitches": self._total_stitches,
			"done": bool(self.done_var.get()),
			"notes": notes,
		}

	def _write_saved_projects(self):
		try:
			with PROJECTS_FILE.open("w", encoding="utf-8") as file_handle:
				json.dump(self.saved_projects, file_handle, indent=2)
		except OSError:
			messagebox.showerror("Save error", "Could not save the project list.")

	def _save_current_project(self):
		if not self._submitted_name:
			return

		project_data = self._current_project_state()
		try:
			with SAVE_FILE.open("w", encoding="utf-8") as file_handle:
				json.dump(project_data, file_handle, indent=2)
		except OSError:
			messagebox.showerror("Save error", "Could not save the active project.")

		updated_projects = [project for project in self.saved_projects if project.get("name") != self._submitted_name]
		updated_projects.insert(0, project_data)
		self.saved_projects = updated_projects
		self._write_saved_projects()
		self._refresh_saved_projects()

	def _clear_active_project(self):
		try:
			SAVE_FILE.unlink(missing_ok=True)
		except OSError:
			messagebox.showerror("New project", "Could not clear the active save file.")

	def _start_new_project(self):
		confirm = messagebox.askyesno("New project", "Clear the current project and return to setup?")
		if not confirm:
			return

		self._clear_active_project()
		self._submitted_name = ""
		self._project = None
		self._required_stitches = 0
		self._previous_stitches = 0
		self._total_stitches = 0
		self._loaded_notes = ""
		self.project_name.set("")
		self.project_type.set("")
		self.section_name.set("Section 1")
		self.yarn_name.set("")
		self.stitches_input.set("")
		self.required_stitches.set("")
		self.hook_type.set("")
		self.done_var.set(False)
		self._build_project_screen()

	def _rename_saved_project(self, project_data):
		old_name = project_data.get("name", "").strip()
		if not old_name:
			return

		new_name = simpledialog.askstring("Rename project", "Enter a new project name:", initialvalue=old_name)
		if new_name is None:
			return

		new_name = new_name.strip()
		if not new_name or new_name == old_name:
			return

		if any(project.get("name") == new_name for project in self.saved_projects):
			messagebox.showerror("Rename project", "A project with that name already exists.")
			return

		updated_projects = []
		for project in self.saved_projects:
			if project.get("name") == old_name:
				updated_projects.append(
					{
						"name": new_name,
						"yarn": project.get("yarn", ""),
						"hook": project.get("hook", ""),
						"required_stitches": project.get("required_stitches", 0),
						"previous_stitches": project.get("previous_stitches", 0),
						"total_stitches": project.get("total_stitches", 0),
						"done": project.get("done", False),
					}
				)
			else:
				updated_projects.append(project)

		self.saved_projects = updated_projects
		if self._submitted_name == old_name:
			self._submitted_name = new_name
			self._project = Project(new_name)
			if hasattr(self, "project_header"):
				self.project_header.configure(text=new_name)
		self._write_saved_projects()
		self._refresh_saved_projects()

	def _delete_saved_project(self, project_data):
		project_name = project_data.get("name", "").strip()
		if not project_name:
			return

		confirm = messagebox.askyesno("Delete project", f"Delete '{project_name}' from saved projects?")
		if not confirm:
			return

		self.saved_projects = [project for project in self.saved_projects if project.get("name") != project_name]
		self._write_saved_projects()
		self._refresh_saved_projects()

	def _open_saved_project(self, project_data):
		section_state = self._get_primary_section_state(project_data)
		self._submitted_name = project_data.get("project_name", project_data.get("name", ""))
		self._project = Project(self._submitted_name)
		self.project_name.set(self._submitted_name)
		self.project_type.set(project_data.get("project_type", ""))
		self.section_name.set(section_state.get("name", "Section 1"))
		self._required_stitches = int(section_state.get("total_rows", project_data.get("required_stitches", 0)))
		self._previous_stitches = int(section_state.get("previous_row", project_data.get("previous_stitches", 0)))
		self._total_stitches = int(section_state.get("current_row", project_data.get("total_stitches", 0)))
		self.yarn_name.set(section_state.get("yarn", project_data.get("yarn", "")))
		self.hook_type.set(section_state.get("hook", project_data.get("hook", "")))
		self.required_stitches.set(str(self._required_stitches) if self._required_stitches else "")
		self.done_var.set(bool(section_state.get("done", project_data.get("done", False))))
		self._loaded_notes = section_state.get("notes", project_data.get("notes", ""))
		self._build_tracker_screen()
		self._update_project_info_display()
		self.previous_label.configure(text=f"Previous stitches: {self._previous_stitches}")
		self.total_label.configure(text=f"Total stitches: {self._total_stitches}")
		self._sync_yarn()
		self._sync_progress()

	def _refresh_saved_projects(self):
		if not hasattr(self, "saved_projects_frame"):
			return

		for widget in self.saved_projects_frame.winfo_children():
			widget.destroy()

		if not self.saved_projects:
			no_projects_label = ctk.CTkLabel(self.saved_projects_frame, text="No saved projects yet")
			no_projects_label.pack(anchor="w", padx=8, pady=8)
			return

		for project_data in self.saved_projects:
			project_frame = ctk.CTkFrame(self.saved_projects_frame)
			project_frame.pack(fill="x", padx=8, pady=6)

			project_name = project_data.get("name", "Untitled")
			hook_text = project_data.get("hook", "") or "Not set"
			done_text = "Yes" if project_data.get("done", False) else "No"
			project_summary = ctk.CTkLabel(
				project_frame,
				text=f"{project_name}  |  Total: {project_data.get('total_stitches', 0)}  |  Required: {project_data.get('required_stitches', 0)}  |  Hook: {hook_text}  |  Done: {done_text}",
				anchor="w",
			)
			project_summary.pack(fill="x", padx=10, pady=(8, 6))

			button_row = ctk.CTkFrame(project_frame, fg_color="transparent")
			button_row.pack(fill="x", padx=10, pady=(0, 10))

			button_row.grid_columnconfigure((0, 1, 2), weight=1)

			open_button = ctk.CTkButton(button_row, text="Open", corner_radius=0, height=32, command=lambda data=project_data: self._open_saved_project(data))
			open_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

			rename_button = ctk.CTkButton(button_row, text="Rename", corner_radius=0, height=32, command=lambda data=project_data: self._rename_saved_project(data))
			rename_button.grid(row=0, column=1, sticky="ew", padx=(0, 6))

			delete_button = ctk.CTkButton(button_row, text="Delete", corner_radius=0, height=32, command=lambda data=project_data: self._delete_saved_project(data))
			delete_button.grid(row=0, column=2, sticky="ew")

	def _clear_window(self):
		for widget in self.content_frame.winfo_children():
			widget.destroy()

	def _build_project_screen(self):
		self._clear_window()
		self.project_name.set("")
		self.project_type.set("")
		parent = self.content_frame
		parent.grid_columnconfigure(0, weight=1)

		self.title_label = ctk.CTkLabel(parent, text="Project name")
		self.title_label.grid(row=0, column=0, padx=16, pady=(18, 6), sticky="w")

		self.project_entry = ctk.CTkEntry(parent, textvariable=self.project_name, width=280)
		self.project_entry.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
		self.project_entry.focus_set()

		self.project_type_label = ctk.CTkLabel(parent, text="Project type")
		self.project_type_label.grid(row=2, column=0, padx=16, pady=(0, 6), sticky="w")

		self.project_type_entry = ctk.CTkEntry(parent, textvariable=self.project_type, width=280)
		self.project_type_entry.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="ew")

		self.submit_button = ctk.CTkButton(parent, text="Set project name", corner_radius=0, height=32, width=220, command=self.submit_project_name)
		self.submit_button.grid(row=4, column=0, padx=16, pady=(0, 18))

		self.saved_projects_title = ctk.CTkLabel(parent, text="Saved projects", font=ctk.CTkFont(size=18, weight="bold"))
		self.saved_projects_title.grid(row=5, column=0, padx=16, pady=(6, 8), sticky="w")

		self.saved_projects_frame = ctk.CTkScrollableFrame(parent, width=320, height=280)
		self.saved_projects_frame.grid(row=6, column=0, padx=16, pady=(0, 16), sticky="nsew")
		self._refresh_saved_projects()

	def submit_project_name(self):
		name = self.project_name.get().strip()
		if not name:
			return

		self._submitted_name = name
		self._project = Project(name)
		self._build_tracker_screen()

	def _build_tracker_screen(self):
		self._clear_window()
		parent = self.content_frame
		parent.grid_columnconfigure(0, weight=1)
		if self._yarn_trace_id is not None:
			self.yarn_name.trace_remove("write", self._yarn_trace_id)
			self._yarn_trace_id = None

		self.project_header = ctk.CTkLabel(parent, text=self._submitted_name, font=ctk.CTkFont(size=22, weight="bold"))
		self.project_header.grid(row=0, column=0, padx=16, pady=(18, 10), sticky="w")

		self.project_info_frame = ctk.CTkFrame(parent)
		self.project_info_frame.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
		self.project_info_frame.grid_columnconfigure(0, weight=1)

		self.project_info_title = ctk.CTkLabel(self.project_info_frame, text="Project info", font=ctk.CTkFont(size=16, weight="bold"))
		self.project_info_title.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")

		self.project_info_type = ctk.CTkLabel(self.project_info_frame, text=f"Project type: {self.project_type.get().strip() or 'Not set'}")
		self.project_info_type.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="w")

		self.project_info_section = ctk.CTkLabel(self.project_info_frame, text=f"Section: {self.section_name.get().strip() or 'Section 1'}")
		self.project_info_section.grid(row=2, column=0, padx=12, pady=(0, 4), sticky="w")

		self.project_info_required = ctk.CTkLabel(self.project_info_frame, text="Required stitches: Not set")
		self.project_info_required.grid(row=3, column=0, padx=12, pady=(0, 4), sticky="w")

		self.project_info_hook = ctk.CTkLabel(self.project_info_frame, text="Hook: Not set")
		self.project_info_hook.grid(row=4, column=0, padx=12, pady=(0, 4), sticky="w")

		self.project_info_yarn = ctk.CTkLabel(self.project_info_frame, text="Yarn: Not set")
		self.project_info_yarn.grid(row=5, column=0, padx=12, pady=(0, 4), sticky="w")

		self.project_info_done = ctk.CTkLabel(self.project_info_frame, text="Done: No")
		self.project_info_done.grid(row=6, column=0, padx=12, pady=(0, 10), sticky="w")

		self.required_button = ctk.CTkButton(parent, text="Set required stitches", corner_radius=0, height=32, width=220, command=self.set_required_stitches)
		self.required_button.grid(row=2, column=0, padx=16, pady=(0, 10))

		self.hook_button = ctk.CTkButton(parent, text="Set hook type", corner_radius=0, height=32, width=220, command=self.set_hook_type)
		self.hook_button.grid(row=3, column=0, padx=16, pady=(0, 10))

		self.progress_label = ctk.CTkLabel(parent, text="Progress: 0%")
		self.progress_label.grid(row=4, column=0, padx=16, pady=(0, 4), sticky="w")

		self.progress_bar = ctk.CTkProgressBar(parent)
		self.progress_bar.grid(row=5, column=0, padx=16, pady=(0, 14), sticky="ew")
		self.progress_bar.set(0)

		self.done_checkbox = ctk.CTkCheckBox(parent, text="Done with this project", variable=self.done_var, command=self.mark_done)
		self.done_checkbox.grid(row=6, column=0, padx=16, pady=(0, 12), sticky="w")

		self.yarn_label = ctk.CTkLabel(parent, text="Yarn")
		self.yarn_label.grid(row=7, column=0, padx=16, pady=(0, 4), sticky="w")

		self.yarn_entry = ctk.CTkEntry(parent, textvariable=self.yarn_name, width=280, placeholder_text="Enter the yarn you are using")
		self.yarn_entry.grid(row=8, column=0, padx=16, pady=(0, 14), sticky="ew")
		self._yarn_trace_id = self.yarn_name.trace_add("write", self._sync_yarn)

		self.stitches_label = ctk.CTkLabel(parent, text="Stitches added")
		self.stitches_label.grid(row=9, column=0, padx=16, pady=(0, 4), sticky="w")

		self.stitches_entry = ctk.CTkEntry(parent, textvariable=self.stitches_input, width=280, placeholder_text="Enter stitch count")
		self.stitches_entry.grid(row=10, column=0, padx=16, pady=(0, 10), sticky="ew")
		self.stitches_entry.bind("<Return>", lambda event: self.add_stitches())

		self.add_button = ctk.CTkButton(parent, text="Add stitches", corner_radius=0, height=32, width=220, command=self.add_stitches)
		self.add_button.grid(row=11, column=0, padx=16, pady=(0, 14))

		self.notes_label = ctk.CTkLabel(parent, text="Notes")
		self.notes_label.grid(row=12, column=0, padx=16, pady=(0, 4), sticky="w")

		self.notes_box = ctk.CTkTextbox(parent, height=90)
		self.notes_box.grid(row=13, column=0, padx=16, pady=(0, 14), sticky="ew")
		if self._loaded_notes:
			self.notes_box.insert("1.0", self._loaded_notes)
		self.notes_box.bind("<KeyRelease>", self._on_notes_changed)

		self.saved_projects_button = ctk.CTkButton(parent, text="Back to saved projects", corner_radius=0, height=32, width=220, command=self._build_project_screen)
		self.saved_projects_button.grid(row=14, column=0, padx=16, pady=(0, 10))

		self.new_project_button = ctk.CTkButton(parent, text="New Project", corner_radius=0, height=32, width=220, command=self._start_new_project)
		self.new_project_button.grid(row=15, column=0, padx=16, pady=(0, 10))

		self.save_button = ctk.CTkButton(parent, text="Save project", corner_radius=0, height=32, width=220, command=self._save_current_project)
		self.save_button.grid(row=16, column=0, padx=16, pady=(0, 10))

		self.total_button = ctk.CTkButton(parent, text="Show total", corner_radius=0, height=32, width=220, command=self.show_total)
		self.total_button.grid(row=17, column=0, padx=16, pady=(0, 10))

		self.stats_title = ctk.CTkLabel(parent, text="Stitch totals", font=ctk.CTkFont(size=18, weight="bold"))
		self.stats_title.grid(row=18, column=0, padx=16, pady=(4, 6), sticky="w")

		self.yarn_value_label = ctk.CTkLabel(parent, text="Yarn: ")
		self.yarn_value_label.grid(row=19, column=0, padx=16, pady=(0, 4), sticky="w")

		self.hook_value_label = ctk.CTkLabel(parent, text="Hook: Not set")
		self.hook_value_label.grid(row=20, column=0, padx=16, pady=(0, 4), sticky="w")

		self.previous_label = ctk.CTkLabel(parent, text="Previous stitches: 0")
		self.previous_label.grid(row=21, column=0, padx=16, pady=(0, 4), sticky="w")

		self.total_label = ctk.CTkLabel(parent, text="Total stitches: 0", font=ctk.CTkFont(size=18, weight="bold"))
		self.total_label.grid(row=22, column=0, padx=16, pady=(0, 16), sticky="w")

		self.yarn_entry.focus_set()
		self._sync_hook()
		self._sync_progress()
		self._sync_yarn()

	def set_required_stitches(self):
		value = simpledialog.askinteger("Required stitches", "How many stitches are required for this project?", minvalue=1)
		if value is None:
			return

		self._required_stitches = value
		self.required_stitches.set(str(value))
		self._sync_progress()
		self._update_project_info_display()
		self._save_current_project()

	def _on_notes_changed(self, event=None):
		if self._suspend_autosave:
			return
		self._save_current_project()

	def set_hook_type(self):
		value = simpledialog.askstring("Hook type", "Which type of hook are you using?")
		if value is None:
			return

		self.hook_type.set(value.strip())
		self._sync_hook()
		self._update_project_info_display()
		self._save_current_project()

	def _sync_yarn(self, *args):
		yarn = self.yarn_name.get().strip()
		if hasattr(self, "yarn_value_label"):
			self.yarn_value_label.configure(text=f"Yarn: {yarn if yarn else 'Not set'}")
		if hasattr(self, "project_info_yarn"):
			self.project_info_yarn.configure(text=f"Yarn: {yarn if yarn else 'Not set'}")

	def _sync_hook(self):
		hook_text = self.hook_type.get().strip()
		if hasattr(self, "hook_value_label"):
			self.hook_value_label.configure(text=f"Hook: {hook_text if hook_text else 'Not set'}")
		if hasattr(self, "project_info_hook"):
			self.project_info_hook.configure(text=f"Hook: {hook_text if hook_text else 'Not set'}")

	def _update_project_info_display(self):
		if hasattr(self, "project_info_type"):
			project_type = self.project_type.get().strip()
			self.project_info_type.configure(text=f"Project type: {project_type if project_type else 'Not set'}")
		if hasattr(self, "project_info_section"):
			section_name = self.section_name.get().strip()
			self.project_info_section.configure(text=f"Section: {section_name if section_name else 'Section 1'}")
		if hasattr(self, "project_info_required"):
			required_text = str(self._required_stitches) if self._required_stitches else "Not set"
			self.project_info_required.configure(text=f"Required stitches: {required_text}")
		if hasattr(self, "project_info_hook"):
			hook_text = self.hook_type.get().strip()
			self.project_info_hook.configure(text=f"Hook: {hook_text if hook_text else 'Not set'}")
		if hasattr(self, "project_info_yarn"):
			yarn_text = self.yarn_name.get().strip()
			self.project_info_yarn.configure(text=f"Yarn: {yarn_text if yarn_text else 'Not set'}")
		if hasattr(self, "project_info_done"):
			self.project_info_done.configure(text=f"Done: {'Yes' if self.done_var.get() else 'No'}")

	def _sync_progress(self):
		if not hasattr(self, "progress_bar") or not hasattr(self, "progress_label"):
			return

		if self.done_var.get() and self._required_stitches > 0:
			progress_value = 1.0
		elif self._required_stitches > 0:
			progress_value = min(self._total_stitches / self._required_stitches, 1.0)
		else:
			progress_value = 0.0

		self.progress_bar.set(progress_value)
		self.progress_label.configure(text=f"Progress: {int(progress_value * 100)}%")
		if self._required_stitches > 0:
			self.done_var.set(progress_value >= 1.0 or self.done_var.get())
		if hasattr(self, "project_info_done"):
			self.project_info_done.configure(text=f"Done: {'Yes' if self.done_var.get() else 'No'}")

	def mark_done(self):
		if self.done_var.get() and self._required_stitches > 0:
			self._total_stitches = max(self._total_stitches, self._required_stitches)
			self.total_label.configure(text=f"Total stitches: {self._total_stitches}")
		self._sync_progress()
		self._update_project_info_display()
		self._save_current_project()

	def add_stitches(self):
		raw_value = self.stitches_input.get().strip()
		if not raw_value:
			return

		try:
			stitches_added = int(raw_value)
		except ValueError:
			self.total_label.configure(text="Total stitches: enter a whole number")
			return

		self._previous_stitches = self._total_stitches
		self._total_stitches += stitches_added

		self.previous_label.configure(text=f"Previous stitches: {self._previous_stitches}")
		self.total_label.configure(text=f"Total stitches: {self._total_stitches}")
		self.stitches_input.set("")
		self.stitches_entry.focus_set()
		self._update_project_info_display()
		self._sync_progress()
		self._save_current_project()

	def show_total(self):
		messagebox.showinfo(
			"Stitch total",
			f"Previous stitches: {self._previous_stitches}\nTotal stitches: {self._total_stitches}",
		)

	def get_project_name(self):
		return self._submitted_name
