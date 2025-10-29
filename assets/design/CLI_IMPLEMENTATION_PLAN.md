# CLI & TUI Implementation Plan

## Phase 1: Fix Current CLI (1-2 weeks)

### Immediate Issues to Fix

1. **Default Behavior**: Remove auto-GUI launch when no args provided
2. **Add Missing Features**: Integrate batch processing, anonymization
3. **Better Argument Structure**: Subcommands for different operations
4. **Output Formats**: JSON, CSV, TSV options

### Enhanced CLI Structure

```bash
# Main commands
pii-detector analyze [FILE] [OPTIONS]          # Detect PII
pii-detector anonymize [FILE] [OPTIONS]        # Anonymize data
pii-detector batch [PATTERN] [OPTIONS]         # Batch processing
pii-detector report [FILE] [OPTIONS]           # Generate reports

# Global options
--output-format {json,csv,table,quiet}         # Output format
--config [CONFIG_FILE]                         # Configuration file
--verbose, -v                                  # Verbose output
--quiet, -q                                    # Minimal output

# Analysis options
--presidio                                      # Enable Presidio
--no-location-check                            # Disable location API
--confidence-threshold FLOAT                   # Minimum confidence
--sample-size INT                              # Sample size for text analysis

# Batch options
--chunk-size INT                               # Batch chunk size
--workers INT                                  # Parallel workers
--resume                                       # Resume interrupted batch

# Anonymization options
--method {hash,remove,categorize,presidio}     # Anonymization method
--preserve-structure                           # Keep original structure
```

### Implementation Files

- `src/pii_detector/cli/commands/analyze.py` - Analysis command
- `src/pii_detector/cli/commands/anonymize.py` - Anonymization command
- `src/pii_detector/cli/commands/batch.py` - Batch processing command
- `src/pii_detector/cli/config.py` - Configuration handling
- `src/pii_detector/cli/output.py` - Output formatting

## Phase 2: Add TUI with Textual (2-3 weeks)

### TUI Features

1. **File Selection**: Browse and select files
2. **Data Preview**: Show dataset structure and sample data
3. **Configuration Forms**: Interactive settings
4. **Progress Tracking**: Real-time processing feedback
5. **Results Review**: Browse and filter results
6. **Export Options**: Save reports and anonymized data

### TUI Components

- `src/pii_detector/tui/app.py` - Main Textual application
- `src/pii_detector/tui/widgets/` - Custom widgets
- `src/pii_detector/tui/screens/` - Different screens (analysis, config, results)

### Key TUI Screens

1. **Welcome Screen**: File selection and recent files
2. **Configuration Screen**: Detection and anonymization settings
3. **Analysis Screen**: Real-time processing with progress
4. **Results Screen**: Tabular view of PII detections
5. **Export Screen**: Output options and file selection

## Phase 3: Integration & Polish (1 week)

### Hybrid Mode Logic

```python
def determine_interface_mode(args):
    """Intelligently choose CLI vs TUI mode."""
    if args.tui:
        return "tui"
    elif args.file or args.batch or not sys.stdin.isatty():
        return "cli"
    elif args.gui:
        return "gui"
    else:
        return "tui"  # Default to TUI for interactive use
```

### Testing Strategy

- Unit tests for CLI commands
- Integration tests for batch processing
- Manual testing for TUI interactions
- Cross-platform compatibility testing

## Pros and Cons Analysis

### Enhanced CLI Only

**Pros:**

- Zero new dependencies
- Excellent for automation
- Universal compatibility
- Fast development
- Pipe-friendly

**Cons:**

- Less user-friendly for complex tasks
- No interactive data preview
- Harder to configure visually

### TUI Addition

**Pros:**

- Best user experience for interactive use
- Visual data preview and configuration
- Modern, attractive interface
- Guided workflows

**Cons:**

- Additional dependency (Textual ~2MB)
- More development time
- Terminal compatibility considerations
- Less scriptable

### Hybrid Approach (Recommended)

**Pros:**

- ✅ Best of both worlds
- ✅ CLI for scripting, TUI for interactive use
- ✅ Intelligent mode detection
- ✅ Covers all use cases

**Cons:**

- ❌ More code to maintain
- ❌ Longer development time
- ❌ Need to keep both interfaces in sync

## Recommendation: Hybrid Implementation

1. **Start with Enhanced CLI** - Fix immediate issues, add missing features
2. **Add TUI Later** - Implement Textual interface for interactive use
3. **Intelligent Defaults** - Auto-detect when to use CLI vs TUI vs GUI

This approach provides:

- **Immediate value** with enhanced CLI
- **Future user experience** improvements with TUI
- **Flexibility** for all types of users (scriptable CLI, interactive TUI, visual GUI)

### Development Priority

1. Fix current CLI default behavior
2. Add batch processing and anonymization commands
3. Implement JSON/CSV output formats
4. Add configuration file support
5. Create TUI interface with Textual
6. Add intelligent mode detection
