# PII Detector Desktop Application Design Brief

**Version:** 2.0
**Date:** September 2025
**Target Platform:** Flet + Flutter Desktop Application

## Product Vision

Design a **professional desktop application** that enables researchers, data analysts, and compliance officers to **safely detect and anonymize PII in research datasets**. The application must feel trustworthy, efficient, and guide users through complex data privacy workflows with confidence.

## Core User Problem

Researchers have sensitive datasets containing personally identifiable information (PII) that must be anonymized before sharing, publication, or analysis. Current solutions are either too technical (command-line tools) or too basic (simple find-and-replace). Users need a **desktop application that intelligently detects PII and provides flexible, research-grade anonymization options**.

## Target Users

1. **Research Data Analysts** - Process survey data, need batch capabilities, value accuracy
2. **Graduate Students** - Clean thesis datasets, often work with Stata files, need guidance
3. **IRB Compliance Officers** - Audit data safety, require detailed reporting and audit trails

---

## Technology Decision: Flet + Flutter (100% Python)

**Why Flet + Flutter is the Right Choice:**

- ✅ **Keep 100% Python codebase** - No JavaScript/TypeScript learning curve
- ✅ **Modern Flutter UI** - Beautiful Material Design widgets and animations
- ✅ **Native desktop performance** - Compiled Flutter engine, not web wrapper
- ✅ **Real-time reactive updates** - Built-in state management for progress tracking
- ✅ **Rich widget ecosystem** - Charts, data tables, progress indicators out-of-the-box
- ✅ **Simple deployment** - Single executable like current PyInstaller solution
- ✅ **Future-proof** - Can easily extend to web and mobile from same codebase

---

## Application Design Requirements

### 1. Core User Workflows

**Primary Workflow - Single File Analysis:**

1. **File Selection** → 2. **Detection Configuration** → 3. **Analysis Progress** → 4. **Results Review** → 5. **Export Options**

**Secondary Workflow - Batch Processing:**

1. **Multi-File Selection** → 2. **Batch Configuration** → 3. **Processing Monitor** → 4. **Results Dashboard** → 5. **Bulk Export**

### 2. Key Screen Layouts

#### Dashboard (Landing Page)

```text
┌─────────────────────────────────────────┐
│ PII Detector v3.0          [Settings]   │
├─────────────────────────────────────────┤
│ Quick Actions                           │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│ │ Single   │ │ Batch    │ │ Recent   │  │
│ │ Analysis │ │ Process  │ │ Projects │  │
│ │ [Icon]   │ │ [Icon]   │ │ [List]   │  │
│ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────┤
│ System Status                           │
│ • Detection Methods: ✅ Standard ✅ AI  │
│ • Last Processing: 3 files, 10 min ago │
│ • Performance: All systems active      │
└─────────────────────────────────────────┘
```

#### File Selection Component

```text
┌─────────────────────────────────────────┐
│ Select Dataset Files                    │
│ ┌─────────────────────────────────────┐ │
│ │     📁 Drag files here              │ │
│ │        or click to browse           │ │
│ │                                     │ │
│ │ Supports: .csv .xlsx .dta (100MB)   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Selected Files:                         │
│ ✓ survey_data.csv (2.1MB)              │
│ ✓ responses.dta (5.8MB)                 │
│ [Clear All] [Add More]                  │
└─────────────────────────────────────────┘
```

#### Detection Configuration Panel

```text
┌─────────────────────────────────────────┐
│ Detection Configuration                 │
│                                         │
│ Methods: [Quick] [Balanced] [Thorough]  │
│ ☑️ Column Name Analysis                 │
│ ☑️ Format Pattern Detection            │
│ ☑️ Sparsity Analysis                   │
│ ☑️ AI Text Analysis (Presidio)         │
│ ☐ Population Lookup (slower)           │
│                                         │
│ ▼ Advanced Settings                     │
│   Language: English ▼                  │
│   Confidence: 0.7 ──●────              │
│   Workers: 4                           │
│                                         │
│ [Start Analysis]                        │
└─────────────────────────────────────────┘
```

#### Results Display with Actions

```text
┌─────────────────────────────────────────┐
│ PII Detection Results                   │
│                                         │
│ Summary: 5 PII columns found (of 12)   │
│ ● High confidence: 3  ● Medium: 1  ● Low: 1 │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │Column    │Method  │Conf│Action      │ │
│ ├─────────────────────────────────────┤ │
│ │email     │Presidio│0.95│[🔒Anonymize] │ │
│ │phone_num │Pattern │0.87│[🔒Anonymize] │ │
│ │full_name │ML-Text │0.82│[❌Remove]   │ │
│ │survey_id │Sparsity│0.45│[✅Keep]     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Preview Data] [Generate Export]        │
└─────────────────────────────────────────┘
```

#### Real-time Progress Tracking

```text
┌─────────────────────────────────────────┐
│ Processing: survey_responses.csv        │
│                                         │
│ Overall: 73% ████████████▒▒▒▒           │
│ ├ Loading data: ✅ Complete (1.2s)      │
│ ├ Column analysis: ✅ Complete (0.8s)   │
│ ├ AI detection: 🔄 Running... (45%)     │
│ └ Report generation: ⏳ Pending         │
│                                         │
│ Time remaining: ~1m 23s                 │
│ Processing 2 of 5 files                 │
│                                         │
│ [Pause] [Cancel] [Show Details]         │
└─────────────────────────────────────────┘
```

### 3. Design System Guidelines

#### Color Palette

- **Primary:** #2563eb (blue) - main actions, progress bars
- **Success:** #059669 (green) - high confidence, completed states
- **Warning:** #d97706 (orange) - medium confidence, cautions
- **Error:** #dc2626 (red) - low confidence, critical PII
- **Neutral:** #6b7280 (gray) - secondary text, borders

#### Typography

- **Headers:** System font, semibold
- **Body:** System font, regular
- **Code/Data:** Monospace font for column names and values

#### Interactive Elements

- **Cards:** Rounded corners (8px), subtle shadows
- **Buttons:** Rounded (6px), hover states with slight elevation
- **Progress bars:** Smooth animations, gradient fills
- **Tables:** Alternating row colors, sortable headers

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

- [ ] Set up Flet development environment
- [ ] Create app structure with navigation
- [ ] Implement file selection with drag-and-drop
- [ ] Basic single-file analysis workflow

### Phase 2: Core Features (Weeks 3-4)

- [ ] Detection configuration panel
- [ ] Real-time progress tracking
- [ ] Results visualization with action buttons
- [ ] Export functionality

### Phase 3: Batch Processing (Weeks 5-6)

- [ ] Multi-file selection UI
- [ ] Batch progress monitoring
- [ ] Results dashboard for multiple files
- [ ] Bulk export options

### Phase 4: Polish & Deploy (Weeks 7-8)

- [ ] Error handling and recovery flows
- [ ] Help documentation integration
- [ ] Performance optimization
- [ ] Build executable and installer

---

## Key Flet Implementation Notes

### Application Structure

```python
def main(page: ft.Page):
    # Configure desktop app
    page.title = "PII Detector v3.0"
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.LIGHT

    # State management
    app_state = AppState()

    # Main layout with navigation
    page.add(create_main_layout(page, app_state))
```

### Real-time Updates

```python
async def run_analysis(page, files, config):
    def update_progress(percent, message):
        # Update UI components in real-time
        progress_bar.value = percent
        status_text.value = message
        page.update()

    # Run analysis with progress callbacks
    results = await analyze_files_async(files, config, update_progress)
    display_results(results)
```

### Deployment Command

```bash
# Development
uv run flet run src/pii_detector/gui/flet_main.py

# Production build
uv run flet build windows
```

---

## Success Criteria

**User Experience Goals:**

- Users can analyze a file in under 3 clicks
- Batch processing handles 100+ files smoothly
- Real-time progress keeps users informed
- Results are immediately actionable (Keep/Anonymize/Remove)

**Technical Goals:**

- Single executable deployment (like current version)
- Handles files up to 100MB without performance issues
- Responsive UI during long operations
- Preserve all current detection capabilities

**Business Goals:**

- Maintain 100% Python codebase for easier maintenance
- Support all current file formats (.csv, .xlsx, .dta)
- Provide professional interface suitable for institutional use
- Create foundation for future web/mobile versions

---

## Next Steps for Designer

1. **Create wireframes** for the 5 core screens listed above
2. **Design interactive prototypes** showing the file → analyze → results flow
3. **Specify component behaviors** for progress tracking and real-time updates
4. **Create design system** with colors, typography, and component styles
5. **Test user flows** with target personas (researchers, compliance officers)

**Deliverables:**

- High-fidelity mockups
- Interactive prototype demonstrating core workflows
- Component library with Flet-compatible specifications
- User testing results and iteration recommendations

This brief provides everything needed to create a modern, professional PII detection tool that researchers will trust and enjoy using.
