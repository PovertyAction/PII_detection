# IPA PII Detector - Complete Design Specification

## Python/Flet Implementation Guide

### Table of Contents

1. [Application Architecture Overview](#architecture)
2. [Design System & Visual Identity](#design-system)
3. [Component Library Specifications](#components)
4. [Screen-by-Screen Implementation Guide](#screens)
5. [State Management & Data Flow](#state-management)
6. [Implementation Priority Matrix](#implementation)
7. [Code Examples & Patterns](#code-examples)

---

## 1. Application Architecture Overview {#architecture}

### Core Framework Decision

The application uses **Flet (Flutter for Python)** to achieve native desktop performance while maintaining a 100% Python codebase. Flet provides Material Design components out-of-the-box, which aligns perfectly with our design requirements.

### Application Structure

```
src/
├── main.py                 # Application entry point
├── config/
│   ├── constants.py        # Colors, sizes, text constants
│   └── settings.py         # User preferences, detection configs
├── ui/
│   ├── app.py             # Main application controller
│   ├── screens/
│   │   ├── dashboard.py   # Landing page with quick actions
│   │   ├── file_selection.py  # File picker and validation
│   │   ├── configuration.py   # Detection method settings
│   │   ├── progress.py        # Real-time processing feedback
│   │   └── results.py         # Results display and actions
│   ├── components/
│   │   ├── cards.py       # Reusable card components
│   │   ├── buttons.py     # Button styles and behaviors
│   │   ├── progress_bars.py   # Progress indicators
│   │   └── method_panels.py   # Expandable configuration panels
│   └── themes/
│       └── ipa_theme.py   # Complete IPA color theme
├── core/
│   ├── detector.py        # PII detection logic integration
│   ├── file_handler.py    # File I/O operations
│   └── script_generator.py # Python code generation
└── assets/
    ├── icons/             # Material Design icons (SVG format)
    └── fonts/             # System fonts fallback
```

This architecture separates concerns clearly, making the codebase maintainable and allowing the UI layer to focus purely on presentation while the core layer handles business logic.

---

## 2. Design System & Visual Identity {#design-system}

### Color Palette Implementation

Create a dedicated theme file that centralizes all color definitions. This ensures consistency and makes future updates simple.

**Primary Color Definitions:**

```python
# config/constants.py
class IPAColors:
    # Primary Brand Colors
    IPA_GREEN = "#49ac57"      # Primary actions, success states
    DARK_GREEN = "#155240"     # Sequential data, deep success
    LIGHT_BLUE = "#84d0d4"     # Secondary actions, hover states
    DARK_BLUE = "#2b4085"      # Headers, navigation, primary text
    RED_ORANGE = "#f26529"     # High-confidence alerts, critical actions

    # Neutral Palette
    LIGHT_GREY = "#f1f2f2"     # Background, card surfaces
    DARK_GREY = "#c9c9c8"      # Borders, secondary text
    CHARCOAL = "#414042"       # Primary text, icons
    BLUE_ACCENT = "#ceecee"    # Subtle highlights, table alternation

    # Confidence Level Indicators
    HIGH_CONFIDENCE = RED_ORANGE    # 0.8+ confidence scores
    MED_CONFIDENCE = "#f5cb57"      # 0.5-0.8 confidence scores
    LOW_CONFIDENCE = DARK_GREY      # <0.5 confidence scores

    # Interactive States
    HOVER_COLOR = BLUE_ACCENT
    ACTIVE_COLOR = IPA_GREEN
    DISABLED_COLOR = DARK_GREY
```

### Typography Hierarchy

```python
class IPATypography:
    # Font families (system fonts with fallbacks)
    PRIMARY_FONT = "Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif"
    MONOSPACE_FONT = "Consolas, Monaco, Courier New, monospace"

    # Font sizes (in pixels for Flet)
    HEADER_1 = 32              # Main page titles
    HEADER_2 = 24              # Section headers
    HEADER_3 = 18              # Subsection titles
    BODY_LARGE = 16            # Primary text, buttons
    BODY_REGULAR = 14          # Secondary text, labels
    BODY_SMALL = 12            # Captions, metadata
    CODE_TEXT = 12             # Monospace content

    # Font weights
    LIGHT = "300"
    REGULAR = "400"
    MEDIUM = "500"
    SEMIBOLD = "600"
    BOLD = "700"
```

### Spacing and Layout Constants

```python
class IPASpacing:
    # Base spacing unit (8px grid system)
    UNIT = 8

    # Common spacing values
    XS = UNIT // 2      # 4px - tight spacing
    SM = UNIT           # 8px - compact spacing
    MD = UNIT * 2       # 16px - standard spacing
    LG = UNIT * 3       # 24px - generous spacing
    XL = UNIT * 4       # 32px - section spacing
    XXL = UNIT * 6      # 48px - major section breaks

    # Component-specific spacing
    CARD_PADDING = MD
    BUTTON_PADDING_H = MD
    BUTTON_PADDING_V = SM
    INPUT_PADDING = SM

    # Border radius values
    RADIUS_SM = 4       # Small elements (checkboxes, small buttons)
    RADIUS_MD = 8       # Cards, input fields
    RADIUS_LG = 12      # Major containers, panels
```

---

## 3. Component Library Specifications {#components}

Understanding that consistency is crucial for professional software, we need to establish reusable components that maintain visual harmony throughout the application.

### Action Card Component

The action card serves as the primary navigation element on the dashboard, guiding users toward their intended workflow.

**Visual Specifications:**

- **Dimensions:** Minimum 200px width, 180px height
- **Background:** LIGHT_GREY (#f1f2f2) default, BLUE_ACCENT on hover
- **Border:** 2px solid DARK_GREY, changes to IPA_GREEN on hover
- **Border Radius:** RADIUS_LG (12px)
- **Padding:** XL (32px) all sides
- **Icon:** 60px diameter circle, IPA_GREEN background
- **Typography:** HEADER_3 for title, BODY_REGULAR for description

**Flet Implementation Pattern:**

```python
def create_action_card(title: str, description: str, icon: str, on_click_handler):
    return ft.Container(
        content=ft.Column([
            ft.Container(  # Icon container
                content=ft.Icon(icon, size=24, color="white"),
                width=60,
                height=60,
                bgcolor=IPAColors.IPA_GREEN,
                border_radius=30,
                alignment=ft.alignment.center,
            ),
            ft.Text(
                title,
                size=IPATypography.HEADER_3,
                weight=IPATypography.SEMIBOLD,
                color=IPAColors.CHARCOAL,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                description,
                size=IPATypography.BODY_REGULAR,
                color=IPAColors.CHARCOAL,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=IPASpacing.MD,
        ),
        width=200,
        height=180,
        padding=IPASpacing.XL,
        bgcolor=IPAColors.LIGHT_GREY,
        border=ft.border.all(2, IPAColors.DARK_GREY),
        border_radius=IPASpacing.RADIUS_LG,
        on_click=on_click_handler,
        # Hover behavior will be handled through Flet's built-in hover events
    )
```

### Expandable Method Panel Component

These panels house the detection method configurations and represent the most complex UI element in our application. The expandable nature allows us to provide detailed controls without overwhelming the interface.

**Visual Specifications:**

- **Header:** LIGHT_GREY background, 15px vertical padding, DARK_GREY bottom border
- **Content:** White background with 20px padding when expanded
- **Animation:** Smooth expand/collapse transition (300ms recommended)
- **Toggle Indicator:** Material Design expand_more icon, rotates 180° when expanded

**State Management Considerations:**
Each panel needs to track:

1. Expansion state (collapsed/expanded)
2. Method enabled state (checkbox in header)
3. Individual setting values within the panel
4. Validation state for required settings

### Progress Bar Component Specifications

Progress indicators need to feel responsive and provide meaningful feedback during potentially long-running operations.

**Visual Requirements:**

- **Height:** 12px for primary progress bars, 6px for mini progress indicators
- **Background:** DARK_GREY (#c9c9c8)
- **Fill:** Linear gradient from IPA_GREEN to LIGHT_BLUE
- **Border Radius:** Half of height value (6px for 12px bar)
- **Animation:** Smooth width transitions, 200ms duration

**Implementation Note:** Flet's ProgressBar component supports these specifications naturally, but you'll need to override the default colors to match our IPA theme.

---

## 4. Screen-by-Screen Implementation Guide {#screens}

Let me walk you through each screen systematically, explaining not just what to build, but why certain decisions were made and how they support the user workflow.

### Screen 1: Dashboard (Landing Page)

**Purpose:** This screen serves as the application's front door, providing immediate access to core functions while establishing trust through professional presentation and system status information.

**Layout Structure:**

```
┌─────────────────────────────────────────────────────┐
│ Header Bar (60px height)                           │
├─────────────────────────────────────────────────────┤
│ Quick Actions Grid (3 columns, flexible height)    │
├─────────────────────────────────────────────────────┤
│ System Status Panel (100px height, fixed)          │
└─────────────────────────────────────────────────────┘
```

**Header Bar Specifications:**

- **Background Color:** DARK_BLUE
- **Height:** 60px fixed
- **Left Content:** Application title "IPA PII Detector v3.0" with search icon
- **Right Content:** Settings button (IPA_GREEN background)
- **Typography:** BODY_LARGE, white color, SEMIBOLD weight

**Quick Actions Grid:**

- **Container:** 3 equal columns with 20px gaps
- **Padding:** 30px all sides
- **Card Specifications:** Use Action Card component (defined above)
- **Cards Required:**
  1. Single Analysis (icon: description, handler: navigate_to_file_selection)
  2. Batch Process (icon: bar_chart, handler: navigate_to_batch_selection)
  3. Recent Projects (icon: history, handler: navigate_to_recent_projects)

**System Status Panel:**

- **Background:** BLUE_ACCENT
- **Padding:** 20px all sides
- **Border Radius:** RADIUS_MD
- **Content:** Three status indicators with green/amber/red dot indicators
- **Typography:** BODY_REGULAR for labels, BODY_SMALL for values

**Flet Screen Structure:**

```python
def create_dashboard_screen():
    return ft.Column([
        create_header_bar(),
        ft.Container(
            content=ft.Row([
                create_action_card("Single Analysis", "Analyze one file...", ft.icons.DESCRIPTION, None),
                create_action_card("Batch Process", "Process multiple files...", ft.icons.BAR_CHART, None),
                create_action_card("Recent Projects", "View past analyses...", ft.icons.HISTORY, None),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            padding=ft.padding.all(30),
        ),
        create_system_status_panel(),
    ],
    expand=True,
    spacing=0,
    )
```

### Screen 2: File Selection Interface

**Purpose:** Enable intuitive file selection with clear format support indicators and file size validation. This screen builds confidence by showing exactly what files are supported and providing immediate feedback.

**Critical Implementation Details:**

- **Drag-and-Drop Zone:** Use `ft.DragTarget` with visual feedback
- **File Validation:** Immediate validation on selection (format, size, readability)
- **Multiple Selection:** Support both individual and batch file selection
- **Visual Feedback:** Clear success/error states for each selected file

**Drop Zone Specifications:**

- **Dimensions:** Full width, 200px minimum height
- **Border:** 3px dashed DARK_GREY, becomes IPA_GREEN on hover/drag-over
- **Background:** LIGHT_GREY default, BLUE_ACCENT on interaction
- **Icon:** Material Design folder_open, 48px size
- **Typography:** HEADER_3 for main text, BODY_SMALL for supported formats

**Selected Files List:**

- **Container:** White background, DARK_GREY border, RADIUS_MD
- **File Items:** Each row shows checkmark, filename, size, with subtle separator lines
- **Action Buttons:** "Clear All", "Add More", "Next: Configure Analysis"

### Screen 3: Detection Configuration Panel

**Purpose:** This is the most complex screen, allowing granular control over detection methods. The design needs to balance power with usability through progressive disclosure.

**Implementation Challenge:** Managing the state of 5 different expandable panels, each with multiple settings, while keeping the interface responsive and intuitive.

**Panel Structure Pattern:**
Each detection method follows this consistent pattern:

1. **Header Section:** Method name, enable/disable checkbox, expand/collapse toggle
2. **Description Section:** Brief explanation of what the method does
3. **Settings Section:** Method-specific configuration options
4. **Validation Feedback:** Real-time indication of valid/invalid settings

**Critical State Management:**
You'll need to track:

- Overall preset selection (Quick/Balanced/Thorough)
- Individual panel expansion states
- Method enable/disable states
- All individual setting values
- Setting validation states
- Interdependencies between methods

**Preset Button Behavior:**
When users select a preset (Quick/Balanced/Thorough), the system should:

1. Update all relevant method settings automatically
2. Provide visual feedback about what changed
3. Allow manual override of preset values
4. Remember that user has customized beyond preset

### Screen 4: Real-time Progress Tracking

**Purpose:** Keep users engaged during processing by showing detailed progress and maintaining control options.

**Critical Implementation Requirements:**

- **Real-time Updates:** Progress bars and status text must update smoothly
- **Granular Feedback:** Show progress for each processing stage
- **Time Estimation:** Calculate and display remaining time estimates
- **User Control:** Always provide pause/cancel options

**Progress Tracking Levels:**

1. **Overall Progress:** Main progress bar (0-100%)
2. **Stage Progress:** Individual task completion states
3. **File Progress:** When processing multiple files
4. **Time Estimates:** Based on historical performance data

**Visual Hierarchy:**

- **File Name:** Most prominent (20px, semibold)
- **Overall Progress:** Large progress bar with percentage
- **Stage Details:** Smaller text with status icons
- **Time Information:** Secondary information, smaller typography

### Screen 5: Results Display with Actions

**Purpose:** Present detection results clearly with immediate actionability. This screen determines whether users trust and adopt the tool.

**Table Specifications:**

- **Framework:** Use `ft.DataTable` for built-in sorting and interaction
- **Column Widths:** Column name (25%), Method (20%), Confidence (15%), PII Type (20%), Actions (20%)
- **Row Styling:** Alternating backgrounds using BLUE_ACCENT
- **Confidence Scores:** Color-coded badges (HIGH_CONFIDENCE, MED_CONFIDENCE, LOW_CONFIDENCE)

**Action Button Specifications:**
Each row contains contextual action buttons:

- **Anonymize:** IPA_GREEN background, lock icon
- **Remove:** RED_ORANGE background, delete icon
- **Keep:** DARK_GREY background, check icon

**Summary Cards Implementation:**
Create four metric cards above the table:

- Total PII columns found
- High confidence count (RED_ORANGE color)
- Medium confidence count (MED_CONFIDENCE color)
- Low confidence count (LOW_CONFIDENCE color)

### Screen 6: Python Script Export Feature

**Purpose:** Bridge the gap between GUI usability and programmatic reproducibility by generating executable Python code.

**Implementation Requirements:**

- **Code Generation:** Dynamic script creation based on user configurations
- **Syntax Highlighting:** Use a monospace font with basic color coding
- **Export Options:** File download, clipboard copy, email integration
- **Template System:** Maintainable code templates for different export scenarios

---

## 5. State Management & Data Flow {#state-management}

Understanding data flow is crucial for building a responsive application that maintains consistency across screens.

### Application State Structure

```python
@dataclass
class AppState:
    # Navigation state
    current_screen: str = "dashboard"
    screen_history: List[str] = field(default_factory=list)

    # File management
    selected_files: List[FileInfo] = field(default_factory=list)
    file_validation_results: Dict[str, ValidationResult] = field(default_factory=dict)

    # Configuration state
    detection_config: DetectionConfig = field(default_factory=DetectionConfig)
    preset_mode: str = "balanced"  # quick, balanced, thorough

    # Processing state
    is_processing: bool = False
    current_progress: float = 0.0
    processing_stage: str = ""
    estimated_time_remaining: Optional[int] = None

    # Results state
    detection_results: Optional[DetectionResults] = None
    user_actions: Dict[str, str] = field(default_factory=dict)  # column -> action mapping

    # UI state
    panel_expansion_states: Dict[str, bool] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)
    success_messages: List[str] = field(default_factory=list)
```

### State Update Patterns

All state changes should flow through a central update mechanism to ensure UI consistency:

```python
class StateManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.state = AppState()

    def update_state(self, **kwargs):
        """Central state update method with UI refresh"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)

        self.refresh_ui()

    def refresh_ui(self):
        """Trigger UI updates after state changes"""
        self.page.update()
```

### Critical Data Flow Patterns

**File Selection Flow:**

1. User selects files → Immediate validation → Update selected_files state
2. Validation results → Update file_validation_results → Refresh UI indicators
3. File removal → Update both states → Refresh file list display

**Configuration Flow:**

1. Preset selection → Update all method configurations → Refresh all panels
2. Individual setting change → Update specific config → Validate dependencies
3. Method enable/disable → Update config → Show/hide dependent settings

**Processing Flow:**

1. Start processing → Set is_processing=True → Show progress screen
2. Progress updates → Update current_progress, processing_stage → Refresh progress bars
3. Completion → Set results state → Navigate to results screen

---

## 6. Implementation Priority Matrix {#implementation}

To help you build efficiently, I've organized the implementation into logical phases that build upon each other.

### Phase 1: Foundation (Week 1)

**Priority:** Critical - Must be completed first

**Deliverables:**

1. **Project Structure Setup:** Create all directories and base files
2. **Theme System:** Implement IPAColors, IPATypography, IPASpacing classes
3. **Basic Navigation:** Screen switching mechanism and state management
4. **Dashboard Screen:** Complete implementation with action cards
5. **File Selection Screen:** Basic file picker functionality (no drag-and-drop yet)

**Success Criteria:** Users can launch app, see professional dashboard, and select files

### Phase 2: Core Detection Flow (Week 2)

**Priority:** High - Enables basic functionality

**Deliverables:**

1. **Configuration Screen:** All five method panels with basic settings
2. **Integration Layer:** Connect GUI to existing PII detector backend
3. **Progress Screen:** Real-time progress tracking with pause/cancel
4. **Basic Results Display:** Simple table showing detection results

**Success Criteria:** Complete end-to-end workflow from file selection to results

### Phase 3: Advanced Features (Week 3)

**Priority:** Medium - Enhances usability

**Deliverables:**

1. **Drag-and-Drop:** Enhanced file selection with visual feedback
2. **Advanced Configuration:** All granular settings for each method
3. **Results Actions:** Implement anonymize/remove/keep functionality
4. **Python Script Export:** Code generation and download capability

**Success Criteria:** Professional-grade feature set matching wireframe specifications

### Phase 4: Polish & Deployment (Week 4)

**Priority:** Low - Final touches

**Deliverables:**

1. **Error Handling:** Comprehensive error states and recovery flows
2. **Performance Optimization:** Smooth animations and responsive interactions
3. **Batch Processing:** Multiple file handling capabilities
4. **Build System:** Executable generation and installer creation

**Success Criteria:** Production-ready application with installer

---

## 7. Code Examples & Patterns {#code-examples}

These examples demonstrate the specific Flet patterns you'll need to implement our design specifications.

### Theme Integration Pattern

```python
# ui/themes/ipa_theme.py
import flet as ft
from config.constants import IPAColors, IPATypography

def create_ipa_theme():
    """Create Flet theme with IPA color palette"""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=IPAColors.IPA_GREEN,
            primary_container=IPAColors.LIGHT_BLUE,
            secondary=IPAColors.DARK_BLUE,
            secondary_container=IPAColors.BLUE_ACCENT,
            surface=IPAColors.LIGHT_GREY,
            surface_variant=IPAColors.BLUE_ACCENT,
            error=IPAColors.RED_ORANGE,
            on_primary=IPAColors.CHARCOAL,
            on_surface=IPAColors.CHARCOAL,
        ),
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(
                size=IPATypography.BODY_LARGE,
                color=IPAColors.CHARCOAL,
            ),
            body_medium=ft.TextStyle(
                size=IPATypography.BODY_REGULAR,
                color=IPAColors.CHARCOAL,
            ),
            headline_large=ft.TextStyle(
                size=IPATypography.HEADER_1,
                color=IPAColors.DARK_BLUE,
                weight=ft.FontWeight.BOLD,
            ),
        )
    )
```

### Expandable Panel Pattern

```python
def create_method_panel(method_name: str, description: str, settings_content, state_manager):
    """Create expandable detection method configuration panel"""

    # Panel expansion state key
    panel_key = f"panel_{method_name.lower().replace(' ', '_')}"
    is_expanded = state_manager.state.panel_expansion_states.get(panel_key, False)

    def toggle_expansion(e):
        new_state = not state_manager.state.panel_expansion_states.get(panel_key, False)
        state_manager.update_state(
            panel_expansion_states={
                **state_manager.state.panel_expansion_states,
                panel_key: new_state
            }
        )

    return ft.Container(
        content=ft.Column([
            # Header with checkbox and expand/collapse
            ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Checkbox(
                            value=True,  # Get from state
                            on_change=lambda e: handle_method_toggle(method_name, e),
                        ),
                        ft.Text(
                            method_name,
                            size=IPATypography.BODY_LARGE,
                            weight=ft.FontWeight.W_600,
                            color=IPAColors.CHARCOAL,
                        ),
                    ]),
                    ft.IconButton(
                        icon=ft.icons.EXPAND_MORE if not is_expanded else ft.icons.EXPAND_LESS,
                        on_click=toggle_expansion,
                        icon_color=IPAColors.IPA_GREEN,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.all(IPASpacing.MD),
                bgcolor=IPAColors.LIGHT_GREY,
                border=ft.border.only(bottom=ft.BorderSide(1, IPAColors.DARK_GREY)),
                on_click=toggle_expansion,
            ),

            # Expandable content
            ft.Container(
                content=ft.Column([
                    # Description
                    ft.Container(
                        content=ft.Text(
                            description,
                            size=IPATypography.BODY_SMALL,
                            color=IPAColors.DARK_GREY,
                        ),
                        padding=ft.padding.all(IPASpacing.SM),
                        bgcolor=IPAColors.BLUE_ACCENT,
                        border_radius=ft.border_radius.all(IPASpacing.RADIUS_SM),
                        margin=ft.margin.only(bottom=IPASpacing.MD),
                    ),

                    # Settings content (passed in)
                    settings_content,
                ]),
                padding=ft.padding.all(IPASpacing.MD),
                visible=is_expanded,
            ),
        ]),
        border=ft.border.all(1, IPAColors.DARK_GREY),
        border_radius=ft.border_radius.all(IPASpacing.RADIUS_MD),
        margin=ft.margin.only(bottom=IPASpacing.MD),
        bgcolor="white",
    )
```

### Progress Tracking Pattern

```python
class ProgressTracker:
    def __init__(self, page: ft.Page, state_manager):
        self.page = page
        self.state_manager = state_manager
        self.progress_bar = None
        self.stage_indicators = {}

    def create_progress_display(self):
        """Create the progress tracking UI elements"""

        # Overall progress bar
        self.progress_bar = ft.ProgressBar(
            width=500,
            height=12,
            bgcolor=IPAColors.DARK_GREY,
            color=IPAColors.IPA_GREEN,
            value=0,
        )

        # Stage indicators
        stages = [
            ("loading", "Loading data"),
            ("column_analysis", "Column analysis"),
            ("ai_detection", "AI detection"),
            ("report_generation", "Report generation"),
        ]

        stage_widgets = []
        for stage_key, stage_label in stages:
            icon = ft.Icon(
                ft.icons.CHECK_CIRCLE,
                color=IPAColors.DARK_GREY,
                size=16,
            )

            self.stage_indicators[stage_key] = icon

            stage_widgets.append(
                ft.Row([
                    icon,
                    ft.Text(
                        stage_label,
                        size=IPATypography.BODY_REGULAR,
                        color=IPAColors.CHARCOAL,
                    ),
                ])
            )

        return ft.Column([
            ft.Text(
                "Processing: survey_responses.csv",
                size=IPATypography.HEADER_3,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),

            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Overall Progress", size=IPATypography.BODY_REGULAR),
                        ft.Text("0%", size=IPATypography.BODY_REGULAR),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    self.progress_bar,
                ]),
                width=500,
            ),

            ft.Column(stage_widgets, spacing=IPASpacing.SM),

        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=IPASpacing.LG)

    def update_progress(self, overall_percent: float, current_stage: str, stage_percent: float):
        """Update progress indicators"""
        # Update overall progress bar
        self.progress_bar.value = overall_percent / 100.0

        # Update stage indicators
        stage_colors = {
            "complete": IPAColors.IPA_GREEN,
            "running": IPAColors.MED_CONFIDENCE,
            "pending": IPAColors.DARK_GREY,
        }

        # Logic to determine stage states based on current_stage and stage_percent
        # Update self.stage_indicators[stage_key].color accordingly

        # Refresh the page
        self.page.update()
```

### Results Table Pattern

```python
def create_results_table(detection_results, action_handlers):
    """Create the PII detection results table"""

    # Create table columns
    columns = [
        ft.DataColumn(ft.Text("Column", weight=ft.FontWeight.W_600)),
        ft.DataColumn(ft.Text("Method", weight=ft.FontWeight.W_600)),
        ft.DataColumn(ft.Text("Confidence", weight=ft.FontWeight.W_600)),
        ft.DataColumn(ft.Text("PII Type", weight=ft.FontWeight.W_600)),
        ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.W_600)),
    ]

    # Create table rows
    rows = []
    for result in detection_results:
        # Confidence badge with color coding
        confidence_color = IPAColors.HIGH_CONFIDENCE if result.confidence > 0.8 else \
                          IPAColors.MED_CONFIDENCE if result.confidence > 0.5 else \
                          IPAColors.LOW_CONFIDENCE

        confidence_badge = ft.Container(
            content=ft.Text(
                f"{result.confidence:.2f}",
                color="white",
                size=IPATypography.BODY_SMALL,
                weight=ft.FontWeight.W_600,
            ),
            bgcolor=confidence_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=ft.border_radius.all(IPASpacing.RADIUS_SM),
        )

        # Action buttons
        action_buttons = ft.Row([
            ft.ElevatedButton(
                "Anonymize",
                icon=ft.icons.LOCK,
                bgcolor=IPAColors.IPA_GREEN,
                color="white",
                on_click=lambda e, col=result.column: action_handlers['anonymize'](col),
            ),
            ft.ElevatedButton(
                "Remove",
                icon=ft.icons.DELETE,
                bgcolor=IPAColors.RED_ORANGE,
                color="white",
                on_click=lambda e, col=result.column: action_handlers['remove'](col),
            ),
            ft.ElevatedButton(
                "Keep",
                icon=ft.icons.CHECK,
                bgcolor=IPAColors.DARK_GREY,
                color="white",
                on_click=lambda e, col=result.column: action_handlers['keep'](col),
            ),
        ], spacing=IPASpacing.SM)

        rows.append(ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(result.column, weight=ft.FontWeight.W_600)),
                ft.DataCell(ft.Text(result.method)),
                ft.DataCell(confidence_badge),
                ft.DataCell(ft.Text(result.pii_type)),
                ft.DataCell(action_buttons),
            ],
            # Alternating row colors
            color=IPAColors.BLUE_ACCENT if len(rows) % 2 == 0 else "white",
        ))

    return ft.DataTable(
        columns=columns,
        rows=rows,
        border=ft.border.all(1, IPAColors.DARK_GREY),
        border_radius=ft.border_radius.all(IPASpacing.RADIUS_MD),
        bgcolor="white",
    )
```

---

## Implementation Checklist

**Before You Start:**

- [ ] Review existing PII detector backend code structure
- [ ] Set up development environment with Flet installed
- [ ] Create project directory structure as specified
- [ ] Implement color constants and theme system first

**Week 1 Deliverables:**

- [ ] Dashboard screen with three action cards
- [ ] Basic file selection with format validation
- [ ] Navigation system between screens
- [ ] IPA theme fully implemented

**Week 2 Deliverables:**

- [ ] All five expandable configuration panels
- [ ] Progress tracking screen with real-time updates
- [ ] Basic results table with confidence color coding
- [ ] Backend integration working end-to-end

**Week 3 Deliverables:**

- [ ] Drag-and-drop file selection
- [ ] All granular settings in configuration panels
- [ ] Action buttons working (anonymize/remove/keep)
- [ ] Python script generation and export

**Week 4 Deliverables:**

- [ ] Error handling and validation throughout
- [ ] Smooth animations and transitions
- [ ] Batch processing capabilities
- [ ] Executable build system

This specification provides everything needed to implement the IPA PII Detector exactly as designed. Each section builds upon the previous one, ensuring you have a clear path from setup through deployment. The code examples show specific Flet patterns that match our design requirements, and the implementation phases ensure you can deliver working software incrementally.
