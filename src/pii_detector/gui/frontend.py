"""Graphical user interface for the PII detector application."""

import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.filedialog import askopenfilename

import pandas as pd
from PIL import Image, ImageTk

from pii_detector.core import processor
from pii_detector.data import constants

# Application constants
INTRO_TEXT = (
    "This script is meant to assist in the detection of PII "
    "(personally identifiable information) and subsequent removal from a dataset. "
    "This is an alpha program, not fully tested yet."
)

INTRO_TEXT_P2 = (
    "You will first load a dataset that might contain PII variables. "
    "The system will try to identify the PII candidates. "
    "Please indicate if you would like to Drop, Encode or Keep them.\n\n"
    "Once finished, you will be able to export a list of the PII detected, a do-file "
    "to generate a deidentified dataset according to your options, and an already "
    "deidentified dataset in case your input file is not a .dta\n\n"
    "Please help improve the program by filling out the survey on your experience using it (Help -> Provide Feedback)."
)

VERSION_NUMBER = "0.2.23"
APP_TITLE = f"IPA's PII Detector - v{VERSION_NUMBER}"


class PIIDetectorGUI:
    """Main GUI application class."""

    def __init__(self):
        """Initialize the GUI application."""
        self.window = None
        self.canvas = None
        self.frame = None

        # Application state
        self.dataset = None
        self.dataset_path = None
        self.new_file_path = None
        self.label_dict = None
        self.value_label_dict = None

        # UI elements
        self.pii_candidates_to_dropdown_element = {}
        self.find_piis_options = {}

        # Configuration variables
        self.check_survey_cto_checkbutton_var = None
        self.check_locations_pop_checkbutton_var = None
        self.column_level_option_for_unstructured_text_checkbutton_var = None
        self.keep_unstructured_text_option_checkbutton_var = None

        self.country_dropdown = None
        self.language_dropdown = None

        # Frames for different sections
        self.piis_frame = None
        self.anonymized_dataset_creation_frame = None
        self.new_dataset_message_frame = None
        self.do_file_message_frame = None

        # Window dimensions
        self.window_width = None
        self.window_height = None

        self.setup_gui()

    def setup_gui(self):
        """Set up the main GUI window and components."""
        self.window = tk.Tk()
        self.window.title(APP_TITLE)

        # Set window size and position
        self.window_width = 640
        self.window_height = 700
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

        # Configure styles
        self.setup_styles()

        # Set up main frame with scrolling
        self.setup_scrollable_frame()

        # Set up menu
        self.setup_menu()

        # Load and display logo
        self.display_logo()

        # Display initial content
        self.display_intro_text()
        self.create_file_selection_section()

    def setup_styles(self):
        """Configure tkinter styles."""
        style = ttk.Style()
        style.configure("my.TLabel", background="white", foreground="black")

    def setup_scrollable_frame(self):
        """Set up the main scrollable frame."""
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.window, bg="white")
        scrollbar = ttk.Scrollbar(
            self.window, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create frame inside canvas
        self.frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # Bind frame configure event
        self.frame.bind("<Configure>", self.on_frame_configure)

        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

    def on_frame_configure(self, event=None):
        """Handle frame resize to update scroll region."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def setup_menu(self):
        """Set up the application menu bar."""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(
            label="Provide Feedback", command=self.open_feedback_survey
        )

    def display_logo(self):
        """Display the IPA logo."""
        try:
            # Get path to logo in assets
            logo_path = (
                Path(__file__).parent.parent.parent.parent / "assets" / "ipa_logo.jpg"
            )
            if logo_path.exists():
                img = Image.open(logo_path)
                img = img.resize((120, 60), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                logo_label = ttk.Label(self.frame, image=photo, style="my.TLabel")
                logo_label.image = photo  # Keep a reference
                logo_label.pack(anchor="nw", padx=(30, 30), pady=(10, 10))
        except Exception as e:
            print(f"Could not load logo: {e}")

    def display_intro_text(self):
        """Display the introductory text."""
        self.display_title("Welcome to the PII detector app")
        self.display_message(INTRO_TEXT)
        self.display_message(INTRO_TEXT_P2)

    def display_title(self, title):
        """Display a title label."""
        label = ttk.Label(
            self.frame,
            text=title,
            wraplength=546,
            justify=tk.LEFT,
            font=("Calibri", 12, "bold"),
            style="my.TLabel",
        )
        label.pack(anchor="nw", padx=(30, 30), pady=(0, 5))
        self.frame.update()
        return label

    def display_message(self, message):
        """Display a message label."""
        label = ttk.Label(
            self.frame,
            text=message,
            wraplength=546,
            justify=tk.LEFT,
            font=("Calibri Italic", 11),
            style="my.TLabel",
        )
        label.pack(anchor="nw", padx=(30, 30), pady=(0, 5))
        self.frame.update()
        return label

    def create_file_selection_section(self):
        """Create the file selection section."""
        self.display_title("Step 1: Select your dataset")
        self.display_message(
            "Click the button below to select the dataset you want to analyze."
        )

        button_frame = tk.Frame(self.frame, bg="white")
        button_frame.pack(anchor="nw", padx=(30, 30), pady=(10, 10))

        select_button = ttk.Button(
            button_frame, text="Select Dataset File", command=self.select_file
        )
        select_button.pack(side=tk.LEFT)

    def select_file(self):
        """Handle file selection."""
        file_path = askopenfilename(
            title="Select dataset file",
            filetypes=[
                ("All supported", "*.csv;*.xlsx;*.xls;*.dta"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx;*.xls"),
                ("Stata files", "*.dta"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            self.load_dataset(file_path)

    def load_dataset(self, file_path):
        """Load and process the selected dataset."""
        self.display_message(f"Loading dataset from: {file_path}")

        try:
            success, result = processor.import_dataset(file_path)

            if success:
                (
                    self.dataset,
                    self.dataset_path,
                    self.label_dict,
                    self.value_label_dict,
                ) = result
                self.display_message(
                    f"Successfully loaded dataset with {len(self.dataset)} rows and {len(self.dataset.columns)} columns."
                )

                # Continue with PII detection workflow
                self.create_pii_detection_options()

            else:
                error_message = result
                messagebox.showerror(
                    "Error", f"Failed to load dataset: {error_message}"
                )
                self.display_message(f"Error: {error_message}")

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            messagebox.showerror("Error", error_message)
            self.display_message(error_message)

    def create_pii_detection_options(self):
        """Create the PII detection options section."""
        self.display_title("Step 2: Configure PII Detection")
        self.display_message("Select the types of PII detection to perform:")

        options_frame = tk.Frame(self.frame, bg="white")
        options_frame.pack(anchor="nw", padx=(30, 30), pady=(10, 10))

        # Survey CTO variables option
        self.check_survey_cto_checkbutton_var = tk.BooleanVar(value=True)
        survey_cto_check = ttk.Checkbutton(
            options_frame,
            text="Check for SurveyCTO system variables",
            variable=self.check_survey_cto_checkbutton_var,
        )
        survey_cto_check.pack(anchor="w", pady=(0, 5))

        # Location population option
        self.check_locations_pop_checkbutton_var = tk.BooleanVar(value=False)
        locations_check = ttk.Checkbutton(
            options_frame,
            text="Check location populations (requires internet)",
            variable=self.check_locations_pop_checkbutton_var,
        )
        locations_check.pack(anchor="w", pady=(0, 5))

        # Country selection for location checking
        country_frame = tk.Frame(options_frame, bg="white")
        country_frame.pack(anchor="w", pady=(0, 10))

        ttk.Label(country_frame, text="Country:", style="my.TLabel").pack(side=tk.LEFT)
        self.country_dropdown = ttk.Combobox(
            country_frame, values=constants.ALL_COUNTRIES, state="readonly", width=20
        )
        self.country_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        if constants.ALL_COUNTRIES:
            self.country_dropdown.set(constants.ALL_COUNTRIES[0])

        # Language selection
        language_frame = tk.Frame(options_frame, bg="white")
        language_frame.pack(anchor="w", pady=(0, 10))

        ttk.Label(language_frame, text="Language:", style="my.TLabel").pack(
            side=tk.LEFT
        )
        self.language_dropdown = ttk.Combobox(
            language_frame,
            values=[constants.ENGLISH, constants.SPANISH, constants.OTHER],
            state="readonly",
            width=20,
        )
        self.language_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        self.language_dropdown.set(constants.ENGLISH)

        # Start detection button
        detect_button = ttk.Button(
            options_frame, text="Start PII Detection", command=self.start_pii_detection
        )
        detect_button.pack(anchor="w", pady=(20, 0))

    def start_pii_detection(self):
        """Start the PII detection process."""
        self.display_title("Step 3: PII Detection Results")
        self.display_message("Analyzing dataset for potential PII...")

        # Configure detection options
        self.find_piis_options = {
            constants.CONSIDER_SURVEY_CTO_VARS: self.check_survey_cto_checkbutton_var.get(),
            constants.CHECK_LOCATIONS_POP: self.check_locations_pop_checkbutton_var.get(),
        }

        try:
            # Run PII detection algorithms
            all_pii_candidates = []

            # 1. Column name/label matching
            self.display_message("Checking column names and labels...")
            column_name_piis = processor.find_piis_based_on_column_name(
                self.dataset,
                self.label_dict or {},
                self.language_dropdown.get(),
                self.country_dropdown.get(),
                constants.STRICT,
            )
            all_pii_candidates.extend(
                [(col, "Column Name Match") for col in column_name_piis]
            )

            # 2. Format pattern detection
            self.display_message("Checking data formats...")
            format_piis = processor.find_piis_based_on_column_format(self.dataset)
            all_pii_candidates.extend([(col, "Format Pattern") for col in format_piis])

            # 3. Sparsity analysis
            self.display_message("Checking for sparse columns...")
            sparse_piis = processor.find_piis_based_on_sparse_entries(self.dataset)
            all_pii_candidates.extend([(col, "Sparse Data") for col in sparse_piis])

            # 4. Location population check (if enabled)
            if self.find_piis_options[constants.CHECK_LOCATIONS_POP]:
                self.display_message(
                    "Checking location populations (this may take a moment)..."
                )
                location_piis = processor.find_piis_based_on_locations_population(
                    self.dataset
                )
                all_pii_candidates.extend(
                    [(col, "Small Location") for col in location_piis]
                )

            # Remove duplicates while preserving detection methods
            unique_piis = {}
            for col, method in all_pii_candidates:
                if col not in unique_piis:
                    unique_piis[col] = [method]
                else:
                    unique_piis[col].append(method)

            # Display results
            if unique_piis:
                self.display_pii_results(unique_piis)
            else:
                self.display_message("✅ No PII detected in this dataset.")
                self.display_message(
                    "The dataset appears to be clean of obvious personally identifiable information."
                )

        except Exception as e:
            error_msg = f"Error during PII detection: {str(e)}"
            self.display_message(f"❌ {error_msg}")
            messagebox.showerror("PII Detection Error", error_msg)

    def display_pii_results(self, unique_piis):
        """Display PII detection results with action options."""
        self.display_message(f"🔍 Found {len(unique_piis)} potential PII columns:")

        # Store PII results for later processing
        self.pii_results = unique_piis
        self.pii_actions = {}  # Will store user's chosen actions

        # Create frame for PII results
        results_frame = tk.Frame(self.frame, bg="white")
        results_frame.pack(anchor="nw", padx=(30, 30), pady=(10, 10), fill="x")

        # Header row
        header_frame = tk.Frame(results_frame, bg="lightgray")
        header_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(
            header_frame,
            text="Column",
            font=("Calibri", 10, "bold"),
            background="lightgray",
        ).pack(side="left", padx=(5, 20))
        ttk.Label(
            header_frame,
            text="Detection Method",
            font=("Calibri", 10, "bold"),
            background="lightgray",
        ).pack(side="left", padx=(0, 20))
        ttk.Label(
            header_frame,
            text="Action",
            font=("Calibri", 10, "bold"),
            background="lightgray",
        ).pack(side="left", padx=(0, 20))

        # Results rows
        for column, methods in unique_piis.items():
            row_frame = tk.Frame(results_frame, bg="white", relief="solid", bd=1)
            row_frame.pack(fill="x", pady=(0, 2))

            # Column name
            col_label = ttk.Label(
                row_frame, text=column, font=("Calibri", 9), style="my.TLabel"
            )
            col_label.pack(side="left", padx=(5, 20), anchor="w")

            # Detection methods
            methods_text = ", ".join(methods)
            methods_label = ttk.Label(
                row_frame, text=methods_text, font=("Calibri", 9), style="my.TLabel"
            )
            methods_label.pack(side="left", padx=(0, 20), anchor="w")

            # Action dropdown
            action_var = tk.StringVar(value="Keep")
            self.pii_actions[column] = action_var

            action_dropdown = ttk.Combobox(
                row_frame,
                textvariable=action_var,
                values=["Keep", "Drop", "Encode"],
                state="readonly",
                width=10,
            )
            action_dropdown.pack(side="left", padx=(0, 5))

        # Export options
        self.create_export_section()

    def create_export_section(self):
        """Create the export options section."""
        self.display_title("Step 4: Export Options")
        self.display_message(
            "Choose your export options and generate the cleaned dataset:"
        )

        export_frame = tk.Frame(self.frame, bg="white")
        export_frame.pack(anchor="nw", padx=(30, 30), pady=(10, 10))

        # Export buttons
        ttk.Button(
            export_frame,
            text="Generate Summary Report",
            command=self.generate_summary_report,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            export_frame,
            text="Export Cleaned Dataset",
            command=self.export_cleaned_dataset,
        ).pack(side="left", padx=(0, 10))

    def generate_summary_report(self):
        """Generate a summary report of PII detection results."""
        if not hasattr(self, "pii_results"):
            messagebox.showwarning("No Results", "Please run PII detection first.")
            return

        report_lines = [
            "PII Detection Summary Report",
            "=" * 40,
            f"Dataset: {self.dataset_path}",
            f"Total columns analyzed: {len(self.dataset.columns)}",
            f"Potential PII columns found: {len(self.pii_results)}",
            "",
            "Detection Results:",
        ]

        for column, methods in self.pii_results.items():
            action = self.pii_actions[column].get()
            report_lines.append(f"  • {column}: {', '.join(methods)} → {action}")

        report_lines.extend(
            [
                "",
                "Actions Summary:",
                f"  • Keep: {sum(1 for var in self.pii_actions.values() if var.get() == 'Keep')} columns",
                f"  • Drop: {sum(1 for var in self.pii_actions.values() if var.get() == 'Drop')} columns",
                f"  • Encode: {sum(1 for var in self.pii_actions.values() if var.get() == 'Encode')} columns",
            ]
        )

        report_text = "\n".join(report_lines)

        # Show in a new window
        report_window = tk.Toplevel(self.window)
        report_window.title("PII Detection Report")
        report_window.geometry("600x400")

        text_widget = tk.Text(report_window, wrap="word", font=("Courier", 10))
        scrollbar = ttk.Scrollbar(
            report_window, orient="vertical", command=text_widget.yview
        )
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        text_widget.insert("1.0", report_text)
        text_widget.config(state="disabled")

    def export_cleaned_dataset(self):
        """Export the dataset with PII handling applied."""
        if not hasattr(self, "pii_results"):
            messagebox.showwarning("No Results", "Please run PII detection first.")
            return

        try:
            # Create cleaned dataset based on user actions
            cleaned_dataset = self.dataset.copy()
            dropped_columns = []
            encoded_columns = []

            for column, action_var in self.pii_actions.items():
                action = action_var.get()

                if action == "Drop":
                    if column in cleaned_dataset.columns:
                        cleaned_dataset = cleaned_dataset.drop(column, axis=1)
                        dropped_columns.append(column)

                elif action == "Encode" and column in cleaned_dataset.columns:
                    # Simple encoding - replace with hash
                    from pii_detector.core.hash_utils import generate_hash

                    cleaned_dataset[f"{column}_encoded"] = (
                        cleaned_dataset[column]
                        .astype(str)
                        .apply(
                            lambda x: generate_hash(str(x))
                            if pd.notna(x) and x != ""
                            else x
                        )
                    )
                    cleaned_dataset = cleaned_dataset.drop(column, axis=1)
                    encoded_columns.append(column)

            # Save cleaned dataset
            from tkinter.filedialog import asksaveasfilename

            save_path = asksaveasfilename(
                title="Save cleaned dataset",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*"),
                ],
            )

            if save_path:
                if save_path.endswith(".csv"):
                    cleaned_dataset.to_csv(save_path, index=False)
                elif save_path.endswith(".xlsx"):
                    cleaned_dataset.to_excel(save_path, index=False)

                summary = f"Successfully exported cleaned dataset to: {save_path}\n\n"
                summary += f"Original columns: {len(self.dataset.columns)}\n"
                summary += f"Cleaned columns: {len(cleaned_dataset.columns)}\n"
                if dropped_columns:
                    summary += f"Dropped: {', '.join(dropped_columns)}\n"
                if encoded_columns:
                    summary += f"Encoded: {', '.join(encoded_columns)}"

                messagebox.showinfo("Export Complete", summary)
                self.display_message(f"✅ Dataset exported successfully to {save_path}")

        except Exception as e:
            error_msg = f"Error exporting dataset: {str(e)}"
            messagebox.showerror("Export Error", error_msg)
            self.display_message(f"❌ {error_msg}")

    def show_about(self):
        """Show the About dialog."""
        about_text = (
            f"{APP_TITLE}\n\n"
            "A tool for identifying and handling personally identifiable information (PII) in datasets.\n\n"
            "Developed by IPA's Global Research and Data Science Team\n"
            "License: MIT"
        )
        messagebox.showinfo("About", about_text)

    def open_feedback_survey(self):
        """Open the GitHub issues page for feedback."""
        github_issues_url = "https://github.com/PovertyAction/PII_detection/issues"
        try:
            webbrowser.open(github_issues_url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open web browser: {e}")

    def run(self):
        """Start the GUI application."""
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            self.window.destroy()


def main():
    """Launch the PII detector GUI application."""
    try:
        app = PIIDetectorGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI application: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
