# UI-D1 Component Reference Code Research

Date: 2026-05-25

Purpose: external PySide6 / Qt Widgets reference-code research for BioMedPilot UI-D1c, UI-D1d, and UI-D1e component shape and API design. This is documentation-only research. It does not copy source code, introduce dependencies, vendor third-party code, or change runtime UI behavior.

Scope boundaries:

- Do not copy GPL, LGPL, commercial-library, or third-party source code into BioMedPilot.
- Do not add Python dependencies or package metadata.
- Do not modify `app/**`, `tests/**`, `assets/**`, runtime launchers, packaging files, executors, reports, exports, engines, downloads, uploads, or cloud services.
- Use references for component shape, state vocabulary, API naming, and native PySide implementation direction only.

## Source Reviews

### 1. Qt for Python official docs

1. Source name: Qt for Python official docs, PySide6 QtWidgets
2. URL:
   - https://doc.qt.io/qtforpython-6/
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QScrollArea.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QFrame.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTableView.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTableWidget.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QListView.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QListWidget.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTabBar.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTabWidget.html
   - https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QStyledItemDelegate.html
3. License: PySide6 is available under LGPLv3/GPLv3 and Qt commercial license. The documentation page itself is under GNU Free Documentation License 1.3. BioMedPilot already uses PySide6 patterns, so this is a native framework reference rather than a new dependency.
4. Relevant BioMedPilot components: WorkflowStepper, SecondaryNavTabs, DataTable, HistoryList, KeyValuePanel, ResultPanel, WarningList, GateNotice, TwoColumnWorkbench, ThreeColumnWorkbench, LeftListMiddleFormRightPreview, RightSummaryPanel, SplitterWorkbench, DenseTablePanel, MatrixGrid96Well, ReferenceQueuePanel, ExtractionFormTable, ReportViewerShell, SettingsResourceTable, ProjectRecentTable, AuditLogPanel.
5. Useful design/code patterns:
   - Prefer `QTableView` plus a local model for dynamic data, filtering, sorting, role-driven display, and large result sets.
   - Use `QTableWidget` only for small static grids, prototypes, or deliberately item-based tables where a custom model would add unnecessary weight.
   - Use `QListView` plus a model for history, queues, audit logs, and selectable row lists; reserve `QListWidget` for small fixed lists.
   - Use `QStyledItemDelegate` for compact status cells, progress-like visual cells, action-like cells, and formatted scientific values without embedding many child widgets in table cells.
   - Use `QSplitter` for workbench layouts where users need to adjust column widths; persist and restore splitter state only if project/user settings later require it.
   - Use `QScrollArea` as the page/workbench scroll container, with a single content widget and stable resize behavior.
   - Use `QFrame` as the base for card, panel, notice, and result surfaces because it gives object-name-based QSS hooks without introducing third-party abstractions.
   - Use `QTabBar` when BioMedPilot needs compact tab navigation without owning page content, and `QTabWidget` when the component should manage content pages itself.
6. What must not be copied: no documentation source snippets, examples, generated HTML, Qt sample code, or upstream style text should be copied into BioMedPilot. Use Qt APIs directly and write BioMedPilot-native wrappers.
7. Whether dependency introduction is recommended: safe to consider. This is the existing native UI framework surface, not a new dependency, assuming the current PySide6 licensing position remains approved for the product.
8. Suggested BioMedPilot-native implementation approach: build shared components as small subclasses or factory functions around Qt Widgets already in use. Keep public APIs data-oriented, for example `rows`, `columns`, `state`, `actions`, `empty_text`, `disabled_reason`, `selection_key`, and `on_*` callbacks. Keep behavior in local models/delegates rather than cell widgets where tables may grow.

### 2. QExtraWidgets

1. Source name: QExtraWidgets
2. URL:
   - https://github.com/gpedrosobernardes/QExtraWidgets
   - https://gpedrosobernardes.github.io/QExtraWidgets/
   - https://pypi.org/project/qextrawidgets/
3. License: MIT.
4. Relevant BioMedPilot components: DataTable, SecondaryNavTabs, HistoryList, WarningList, GateNotice, ReferenceQueuePanel, DenseTablePanel, MatrixGrid96Well, ExtractionFormTable, FilePickerButton, KeyValuePanel.
5. Useful design/code patterns:
   - `QFilterableTable` is useful as a feature checklist for column filters, compact search, type-aware display, and user-friendly table controls.
   - `QAccordion` is relevant for optional detail sections, warning grouping, extraction sections, and settings/resource grouping where visual density matters.
   - Theme-aware icon and label handling is a useful pattern for avoiding hard-coded dark/light assets.
   - Small convenience widgets such as icon combo boxes and search inputs point toward narrow component APIs instead of oversized generic panels.
6. What must not be copied: do not copy widget implementation, icon wrappers, animations, table filtering internals, QSS, examples, or naming that would make the component a derivative implementation.
7. Whether dependency introduction is recommended: maybe later. MIT is permissive, but dependency introduction is unnecessary for UI-D1 research and would expand the runtime/package surface.
8. Suggested BioMedPilot-native implementation approach: use QExtraWidgets as a checklist only. Implement native filter rows and accordion-like disclosure with `QFrame`, `QToolButton`, `QVBoxLayout`, `QSortFilterProxyModel`, and existing BioMedPilot tokens. For icons, route through BioMedPilot asset keys and semantic state metadata rather than adopting QExtraWidgets icon classes.

### 3. qt-material

1. Source name: qt-material
2. URL:
   - https://github.com/dunderlab/qt-material
   - https://qt-material.readthedocs.io/en/latest/
   - https://pypi.org/project/qt-material/
3. License: BSD-2-Clause.
4. Relevant BioMedPilot components: ModuleEntryCard, WorkflowStepper, SecondaryNavTabs, DataTable, FormFieldRow, KeyValuePanel, ResultPanel, GateNotice, DisabledActionButton, TwoColumnWorkbench, ThreeColumnWorkbench, DenseTablePanel, ReportViewerShell, ExportGatePanel, SettingsResourceTable, ProjectRecentTable.
5. Useful design/code patterns:
   - Theme values are organized as reusable tokens and can be exported into QSS.
   - Built-in light themes and runtime theme switching show how a single palette contract can drive many widgets.
   - `density_scale` is a useful concept for compact desktop layouts, especially dense forms, tables, and workbench side panels.
   - The `extra` customization concept is relevant for a BioMedPilot-owned QSS layer that lets components opt into menu/table/button refinements without adding new classes.
6. What must not be copied: do not copy XML theme files, generated QSS, resource files, token names, demo code, or material visual identity. BioMedPilot should not become a Material Design themed app.
7. Whether dependency introduction is recommended: no. The license is permissive, but the design language is not BioMedPilot's target. Use the token/density organization idea only.
8. Suggested BioMedPilot-native implementation approach: define BioMedPilot-owned light theme tokens for surface, border, text, muted text, accent, semantic warning/blocking/testing states, row heights, and density levels. Generate or hand-maintain local QSS from those tokens inside existing style infrastructure, with no qt-material runtime import.

### 4. PyQt-Fluent-Widgets / QFluentWidgets

1. Source name: PyQt-Fluent-Widgets / QFluentWidgets
2. URL:
   - https://github.com/zhiyiYo/PyQt-Fluent-Widgets
   - https://qfluentwidgets.com/
   - https://pypi.org/project/PyQt-Fluent-Widgets/
3. License: GPLv3 for non-commercial use; commercial license required for commercial use. The repository README also notes separate PySide branches and commercial/pro offerings.
4. Relevant BioMedPilot components: ModuleEntryCard, SecondaryNavTabs, GateNotice, WarningList, ResultPanel, DisabledActionButton, ExternalEngineStatusPanel, ReviewConfirmationPanel, AuditLogPanel, ReportViewerShell.
5. Useful design/code patterns:
   - Navigation panel shape: route-key based items, separated top/scroll/bottom positions, expandable/collapsible rail behavior, and clear distinction between navigation state and content ownership.
   - Card shape: consistent frame-like surfaces with title/body/action areas and restrained hierarchy.
   - Info bar shape: severity variants, closable notices, duration/position concepts, and manager-like stacking behavior for transient feedback.
   - Status-like widgets: compact semantic surfaces with icons, severity, title, and content; useful as a reference for GateNotice and WarningList behavior boundaries.
6. What must not be copied: do not copy GPL/commercial source, class structure, route manager code, icon resources, QSS, animations, Fluent visual identity, examples, or API signatures wholesale. Do not add the package as a dependency.
7. Whether dependency introduction is recommended: no. The GPL/commercial posture is too risky for BioMedPilot without an explicit later licensing decision.
8. Suggested BioMedPilot-native implementation approach: borrow only the product ideas: route-key metadata for navigation-like components, severity-driven notice factories, and card/panel anatomy. Implement with `QFrame`, `QBoxLayout`, `QStackedWidget`, `QTabBar`, and BioMedPilot semantic tokens. Keep component names and APIs aligned with BioMedPilot state language rather than Fluent naming.

### 5. pyside6-utils

1. Source name: pyside6-utils
2. URL:
   - https://github.com/Woutah/pyside6-utils
   - https://pypi.org/project/pyside6-utils/
3. License: LGPL-2.1 based on repository license file; PyPI metadata currently reports `LPGPLv2`, likely a typo for LGPL.
4. Relevant BioMedPilot components: FormFieldRow, KeyValuePanel, HistoryList, ReferenceQueuePanel, ExtractionFormTable, SettingsResourceTable, ProjectRecentTable, Collapsible sections inside GateNotice or ResultPanel.
5. Useful design/code patterns:
   - `CollapsibleGroupBox` is a useful pattern for progressive disclosure of technical details, warnings, and optional settings.
   - `WidgetList` is relevant for repeatable form rows and queue/editor rows that users can add or remove.
   - `PandasTableView` / table model concepts are relevant for dataframes and scientific tables, but BioMedPilot should keep pandas-specific coupling outside shared UI components unless a page explicitly owns pandas data.
   - `WidgetSwitcher` suggests a local way to swap editor types inside dynamic extraction rows without changing the parent component contract.
6. What must not be copied: do not copy LGPL source, UI files, widget implementations, model adapters, or example code. Do not vendor the library.
7. Whether dependency introduction is recommended: no for UI-D1. Maybe later only after legal/product approval and only if a specific utility materially reduces maintenance cost.
8. Suggested BioMedPilot-native implementation approach: implement collapsible and repeatable-row behavior directly with BioMedPilot-owned widgets. Use plain Python data descriptors for dynamic rows, local `QAbstractTableModel` or `QStandardItemModel` where appropriate, and avoid pandas assumptions in common components.

### 6. pyside6-datatable-widget

1. Source name: pyside6-datatable-widget
2. URL:
   - https://github.com/ultra-bugs/pyside6-datatable-widget
   - https://pypi.org/project/pyside6-datatable-widget/
3. License: GPLv3 according to PyPI metadata and repository license; PyPI classifiers also include MIT, so treat the package as GPL-risk unless clarified by the author.
4. Relevant BioMedPilot components: DataTable, DenseTablePanel, ExtractionFormTable, MatrixGrid96Well, SettingsResourceTable, ProjectRecentTable, AuditLogPanel.
5. Useful design/code patterns:
   - Feature breakdown: configurable columns, type-based sorting, global search, column-specific search, pagination, column visibility, custom formatting, row selection, aggregate helpers, inline actions, and filter/sort signals.
   - Model/view split: the documented `DataTableModel` concept reinforces keeping data transformation out of the visual table wrapper.
   - Signals for filtered data, sort changes, selection changes, and row actions are useful BioMedPilot API ideas.
   - Inline action columns should be treated carefully in BioMedPilot because disabled actions and formal export/report gates must remain explicit.
6. What must not be copied: do not copy GPL source, examples, model classes, fluent-interface signatures, action-button column implementation, progress/icon cell rendering, or QSS. Do not add the package as a dependency.
7. Whether dependency introduction is recommended: no. GPL-3.0 risk is not acceptable for this stage.
8. Suggested BioMedPilot-native implementation approach: define a BioMedPilot `DataTable` API around `columns`, `rows`, `visible_columns`, `sort_key`, `filter_text`, `selection_mode`, `empty_state`, and optional `row_actions`. Back it with `QAbstractTableModel` plus `QSortFilterProxyModel`. Use delegates for status, progress, and action presentation, and expose BioMedPilot-specific signals such as `row_selected`, `row_action_requested`, `filter_changed`, and `sort_changed`.

## Component Mapping Table

| BioMedPilot component | Best reference source | Reference idea | Native PySide implementation recommendation | License risk |
|---|---|---|---|---|
| ModuleEntryCard | QFluentWidgets | Card anatomy with title, body, icon/status, and action area | `QFrame` with fixed semantic slots: icon, title, description, status chip, disabled reason, entry callback | High if copied; safe as abstract idea |
| WorkflowStepper | Qt for Python official docs | Tabs/list/delegate-driven current step state | `QFrame` row or vertical `QListView` with step model and delegate; no workflow execution | Low |
| SecondaryNavTabs | Qt for Python official docs | `QTabBar` for compact navigation without content ownership | `QTabBar` wrapper with `tabs`, `active_key`, `enabled_map`, and `changed` signal | Low |
| DataTable | pyside6-datatable-widget | Feature checklist for columns, search, sort, visibility, selection, and row actions | `QTableView` + `QAbstractTableModel` + `QSortFilterProxyModel`; delegates for formatting/status/actions | High if copied |
| FormFieldRow | pyside6-utils | Repeatable/editable row shape and typed editor hints | `QFrame` or layout factory with label, control, helper, validation state, and disabled reason | Medium if copied |
| KeyValuePanel | Qt for Python official docs | Dense label/value display using native layouts and frames | `QFrame` with `QGridLayout`; support copy-safe values, semantic rows, and empty state | Low |
| HistoryList | Qt for Python official docs | Model/view list for selectable history rows | `QListView` with local model and optional delegate for timestamp/status/action metadata | Low |
| ResultPanel | QFluentWidgets | Card/info surface separation between result, warning, and status | `QFrame` with title, summary slots, severity state, and optional table/detail area | High if copied |
| WarningList | QFluentWidgets | Severity-grouped notices and info-bar style status | BioMedPilot notice rows inside `QFrame` or `QListView`; persistent, not transient toast UI | High if copied |
| GateNotice | QFluentWidgets | Info-bar severity model and close/action concepts | Persistent `QFrame` notice with severity, title, body, blocker reason, and safe action slots | High if copied |
| FilePickerButton | QExtraWidgets | Small convenience control with icon/search affordance discipline | Native `QPushButton`/`QToolButton` wrapper that opens picker only via caller callback | Low to medium |
| DisabledActionButton | QFluentWidgets | Explicit disabled state with reason and status-like affordance | `QPushButton` wrapper with disabled tooltip/reason and semantic metadata; no hidden side effects | High if copied |
| TwoColumnWorkbench | Qt for Python official docs | Splitter or fixed layout for primary/secondary panes | `QSplitter` when user-resizable; otherwise `QHBoxLayout` with documented width policy | Low |
| ThreeColumnWorkbench | Qt for Python official docs | Multi-pane splitter with stable sizing and collapsible children | `QSplitter` with left/middle/right panes, min widths, optional state persistence later | Low |
| LeftListMiddleFormRightPreview | Qt for Python official docs | List-view, form layout, preview frame composition | Compose `QListView`, form `QFrame`, preview `QFrame` inside `QSplitter`; callbacks only | Low |
| RightSummaryPanel | QFluentWidgets | Card/panel summary shape with compact status rows | `QFrame` side panel with key/value rows, warnings, and disabled summary actions | High if copied |
| SplitterWorkbench | Qt for Python official docs | `QSplitter` handles, sizing, orientation, save/restore concept | Thin wrapper around `QSplitter` with names, min widths, and optional settings key | Low |
| DenseTablePanel | pyside6-datatable-widget | Search/sort/filter control band around a table | BioMedPilot `DataTable` plus compact toolbar and empty/blocked states | High if copied |
| PreviewCard | QFluentWidgets | Framed preview card with metadata/action slots | `QFrame` with preview widget slot, caption, status, and safe action area | High if copied |
| LaneLayoutPreview | Qt for Python official docs | Custom frame/grid preview using native painting/layout | `QFrame` or lightweight custom widget using BioMedPilot colors; no third-party drawing code | Low |
| MatrixGrid96Well | Qt for Python official docs | Native table/grid as structured scientific layout | `QTableView` model for 8x12 wells or custom `QGridLayout` for small interactive grids | Low |
| ReferenceQueuePanel | pyside6-utils | Add/remove repeatable list rows | `QListView` or repeatable row container with queued item model and safe row actions | Medium if copied |
| ExtractionFormTable | pyside6-utils | Widget list and switcher ideas for dynamic typed rows | `QTableView` with delegates or form-row list; keep extraction data descriptors local | Medium if copied |
| ReportViewerShell | Qt for Python official docs | Scroll area and tabs for viewer shell/content selection | `QScrollArea` or `QStackedWidget` with disabled/report-gated states; no report generation | Low |
| ExportGatePanel | QFluentWidgets | Notice/status panel with blocked/allowed action affordance | Persistent `GateNotice` + disabled action rows; no export writer calls | High if copied |
| PlotPlaceholder | Qt for Python official docs | Framed placeholder surface with stable sizing | `QFrame` with neutral placeholder state and optional static metadata; no plotting dependency | Low |
| ExternalEngineStatusPanel | QFluentWidgets | Status-like cards and severity rows | `QFrame` list of resource/engine statuses using BioMedPilot semantic states | High if copied |
| SettingsResourceTable | pyside6-datatable-widget | Column visibility, status formatting, type-aware sorting | `QTableView` model with resource rows and delegates for availability/testing/blocked state | High if copied |
| ProjectRecentTable | Qt for Python official docs | Model/view table or list depending on density | `QTableView` for sortable project rows; `QListView` if card-like recent items win | Low |
| WizardFlowShell | Qt for Python official docs | `QStackedWidget`/tab-like page ownership and step state | `QStackedWidget` plus BioMedPilot stepper and guarded next/back callbacks | Low |
| ReviewConfirmationPanel | QFluentWidgets | Confirmation/status panel with explicit severity and action grouping | `QFrame` with summary, warnings, checkbox/ack state if needed, and disabled reason text | High if copied |
| AuditLogPanel | pyside6-datatable-widget | Searchable/sortable log table and event signals | `QTableView` with timestamp/action/status columns, filter proxy, and read-only delegate cells | High if copied |

## Cross-Component Native API Recommendations

- Prefer data descriptors over widget injection for reusable components: `columns`, `rows`, `items`, `state`, `severity`, `actions`, `disabled_reason`, `empty_state`, and `selection_key`.
- Keep business actions outside shared components. Components should emit `*_requested` signals or call injected callbacks; they must not invoke executors, report builders, exporters, installers, downloads, uploads, or cloud services.
- Use object names and semantic properties for QSS. Avoid importing theme engines or third-party style resources.
- For tables, prefer `QTableView` plus local models for anything sortable, filterable, or potentially large. Use `QTableWidget` only for small fixed matrices or prototypes such as a simple 96-well grid if model overhead is unjustified.
- Use delegates for compact table cell visualization rather than embedding many widgets in cells.
- Treat GPL, LGPL, and commercial-library references as design inspiration only. MIT/BSD references are still not dependencies for UI-D1 unless later approved.

## License Risk Summary

| Source | License posture | Dependency recommendation | Risk summary |
|---|---|---|---|
| Qt for Python official docs | PySide6 LGPLv3/GPLv3/commercial; docs under GNU FDL 1.3 | safe to consider because PySide6 is the native framework | Low if using approved PySide6 APIs |
| QExtraWidgets | MIT | maybe later | Low license risk, but unnecessary dependency surface now |
| qt-material | BSD-2-Clause | no | Low license risk, but visual system mismatch and dependency not needed |
| PyQt-Fluent-Widgets / QFluentWidgets | GPLv3 or commercial | no | High GPL/commercial risk |
| pyside6-utils | LGPL-2.1 | no; maybe later only with approval | Medium LGPL compliance and packaging risk |
| pyside6-datatable-widget | GPLv3 risk | no | High GPL risk; feature checklist only |

## Research Conclusion

The safest implementation path for BioMedPilot is native PySide6 composition:

- `QFrame` for cards, panels, notices, result shells, preview shells, and status surfaces.
- `QTabBar` / `QTabWidget` / `QStackedWidget` for secondary navigation and wizard shells.
- `QSplitter` for user-resizable workbenches.
- `QScrollArea` for stable page and report shells.
- `QTableView` / `QListView` plus local models and delegates for data-heavy tables, queues, history, recent projects, settings resources, extraction rows, and audit logs.

No external widget dependency is recommended for UI-D1c, UI-D1d, or UI-D1e. The third-party libraries are useful only as reference material for API ergonomics, state surfaces, density, filtering, and navigation/card/notice shape.
