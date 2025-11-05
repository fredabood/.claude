# Diagram Handoff: {{ handoff_title }}

**Document Type:** Handoff Template
**From:** {{ config.roles.diagram_engineer or 'Diagram Engineer / Technical Writer' }}
**To:** {{ config.roles.documentation_engineer or 'Documentation Engineer / Team' }}
**Purpose:** Handoff diagrams and documentation assets
**Related Workflow:** Documentation & Diagrams Workflow

---

## Handoff Metadata

| Field | Value |
|-------|-------|
| **Date** | {{ handoff_date }} |
| **Diagrams Created** | {{ diagram_count }} diagrams |
| **Diagram Tool** | {{ diagram_tool }} |
| **Total Size** | {{ total_size }} |
| **Target Documentation** | {{ target_documentation }} |

---

## 1. Diagrams Created

{% for diagram in diagrams %}
### {{ loop.index }}. {{ diagram.name }}

**File:** `{{ diagram.file_path }}`
**Type:** {{ diagram.type }}
**Format:** {{ diagram.format }}
**Purpose:** {{ diagram.purpose }}

{% if diagram.tool == 'mermaid' %}
**Diagram Type:** {{ diagram.mermaid_type }}
**Tested At:** https://mermaid.live
**Renders:** {{ diagram.renders_correctly }}

{% elif diagram.tool == 'drawio' %}
**Source File:** `{{ diagram.drawio_source }}`
**Export Format:** {{ diagram.export_format }}
**Editable:** {{ diagram.editable_location }}

{% elif diagram.tool == 'plantuml' %}
**PlantUML Type:** {{ diagram.plantuml_type }}
**Generated From:** `{{ diagram.source_file }}`

{% elif diagram.tool == 'lucidchart' %}
**Lucidchart URL:** {{ diagram.lucidchart_url }}
**Export Format:** {{ diagram.export_format }}
**Sharing:** {{ diagram.sharing_permissions }}

{% elif diagram.tool == 'figma' %}
**Figma File:** {{ diagram.figma_url }}
**Frame Name:** {{ diagram.frame_name }}
**Export Settings:** {{ diagram.export_settings }}
{% endif %}

**Key Elements:**
{% for element in diagram.key_elements %}
- {{ element }}
{% endfor %}

**Suggested Placement:**
- **Primary:** {{ diagram.primary_placement }}
- **Secondary:** {{ diagram.secondary_placement }}
{% if diagram.related_placement %}
- **Related:** {{ diagram.related_placement }}
{% endif %}

**Context to Include:**
```markdown
{{ diagram.context_description }}
```

**Dimensions:** {{ diagram.width }} × {{ diagram.height }}
**File Size:** {{ diagram.file_size }}

---

{% endfor %}

---

## 2. Diagram Index

{% if diagram_index_created %}
**Created/Updated:** `{{ diagram_index_path }}`

**Index Structure:**
{% for category in diagram_categories %}
- {{ category.count }} {{ category.name }}
{% endfor %}

**Index Preview:**
```markdown
{{ diagram_index_preview }}
```
{% endif %}

---

## 3. Quality Verification

### Syntax & Rendering

{% if diagram_tool == 'mermaid' %}
- {{ mermaid_syntax_verified }} All diagrams tested at https://mermaid.live
- {{ no_syntax_errors }} No syntax errors found
- {{ renders_correctly }} All diagrams render correctly
- {{ simplified_where_needed }} Complex diagrams simplified where needed

{% elif diagram_tool == 'drawio' %}
- {{ exports_correctly }} All diagrams export correctly to {{ export_formats }}
- {{ no_broken_links }} No broken links or missing resources
- {{ text_readable }} All text is readable at standard zoom levels

{% elif diagram_tool == 'plantuml' %}
- {{ plantuml_syntax_valid }} All PlantUML syntax validated
- {{ generates_successfully }} All diagrams generate successfully
- {{ output_quality }} Output quality verified (DPI: {{ dpi }})
{% endif %}

### Accuracy

{% for accuracy_check in accuracy_checks %}
- {{ accuracy_check.status }} {{ accuracy_check.description }}
{% endfor %}

### Consistency

{% for consistency_check in consistency_checks %}
- {{ consistency_check.status }} {{ consistency_check.description }}
{% endfor %}

### Context

{% for context_check in context_checks %}
- {{ context_check.status }} {{ context_check.description }}
{% endfor %}

---

## 4. Component Names & Terminology

**Exact Names Used:**
{% for component_name in component_names %}
- {{ component_name.actual_name }} (not "{{ component_name.avoid_name }}")
{% endfor %}

**Terminology Standards:**
{% for term in terminology_standards %}
- **{{ term.term }}**: {{ term.standard_usage }}
{% endfor %}

---

## 5. Embedding Recommendations

{% for embedding_rec in embedding_recommendations %}
### {{ loop.index }}. {{ embedding_rec.location }}

**Section:** {{ embedding_rec.section }}
**Diagram(s):** `{{ embedding_rec.diagrams }}`

**Context:**
```markdown
{{ embedding_rec.embedding_example }}
```

**Purpose:** {{ embedding_rec.purpose }}

---

{% endfor %}

---

## 6. Diagram Types & Descriptions

### Architecture Diagrams

{% for arch_diagram in architecture_diagrams %}
**{{ arch_diagram.name }}**
- **Shows:** {{ arch_diagram.shows }}
- **Level:** {{ arch_diagram.level }}
- **Audience:** {{ arch_diagram.audience }}
{% endfor %}

### Workflow/Flow Diagrams

{% for workflow_diagram in workflow_diagrams %}
**{{ workflow_diagram.name }}**
- **Shows:** {{ workflow_diagram.shows }}
- **Type:** {{ workflow_diagram.flow_type }}
- **Swimlanes:** {{ workflow_diagram.has_swimlanes }}
{% endfor %}

### Data Model Diagrams

{% for data_diagram in data_model_diagrams %}
**{{ data_diagram.name }}**
- **Shows:** {{ data_diagram.shows }}
- **Notation:** {{ data_diagram.notation }}
- **Entities:** {{ data_diagram.entity_count }}
{% endfor %}

### Sequence Diagrams

{% for sequence_diagram in sequence_diagrams %}
**{{ sequence_diagram.name }}**
- **Shows:** {{ sequence_diagram.shows }}
- **Participants:** {{ sequence_diagram.participants }}
- **Interactions:** {{ sequence_diagram.interaction_count }}
{% endfor %}

### UI/UX Diagrams

{% for ui_diagram in ui_diagrams %}
**{{ ui_diagram.name }}**
- **Shows:** {{ ui_diagram.shows }}
- **Fidelity:** {{ ui_diagram.fidelity }}
- **Screens:** {{ ui_diagram.screen_count }}
{% endfor %}

---

## 7. Related Diagrams Suggested

**Based on diagrams created, these additional diagrams would complement the documentation:**

{% for suggested_diagram in suggested_diagrams %}
{{ loop.index }}. **{{ suggested_diagram.name }}**
   - **Type:** {{ suggested_diagram.type }}
   - **Would Show:** {{ suggested_diagram.description }}
   - **Useful For:** {{ suggested_diagram.useful_for }}
   - **Priority:** {{ suggested_diagram.priority }}
   - **Effort:** {{ suggested_diagram.effort }}

{% endfor %}

---

## 8. Documentation Updates Needed

### Files to Update

{% for file_update in documentation_updates %}
**{{ loop.index }}. {{ file_update.file }}**
{% for task in file_update.tasks %}
- [ ] {{ task }}
{% endfor %}

{% endfor %}

---

## 9. Cross-References

### Diagrams Reference Each Other

{% for cross_ref in diagram_cross_references %}
- `{{ cross_ref.from_diagram }}` references `{{ cross_ref.to_diagram }}`
{% endfor %}

### Documentation References Diagrams

{% for doc_ref in documentation_references %}
- {{ doc_ref.document }} links to `{{ doc_ref.diagram }}`
{% endfor %}

---

## 10. Maintenance Guidelines

### When to Update Diagrams

**Architecture Changes:**
{% for arch_change in architecture_change_triggers %}
- {{ arch_change.trigger }} → {{ arch_change.diagram_impact }}
{% endfor %}

**Feature Additions:**
{% for feature_change in feature_change_triggers %}
- {{ feature_change.trigger }} → {{ feature_change.diagram_impact }}
{% endfor %}

**Regular Reviews:**
- **Frequency:** {{ maintenance_frequency }}
- **Trigger Events:** {{ maintenance_triggers }}
- **Ownership:** {{ maintenance_owner }}

### Diagram Versioning

**Version Control:** {{ version_control_method }}
{% if version_control_method == 'git' %}
- All diagrams stored in git repository
- Changes tracked through commits
- Previous versions available in git history
- Diagrams evolve with codebase
{% endif %}

**Version Naming:** {{ version_naming_convention }}

---

## 11. Style Guide

### Color Palette

{% if has_color_palette %}
{% for color in color_palette %}
- **{{ color.name }}**: {{ color.hex }} - {{ color.usage }}
{% endfor %}
{% endif %}

### Typography

{% if has_typography_standards %}
- **Font:** {{ diagram_font }}
- **Title Size:** {{ title_size }}
- **Body Text Size:** {{ body_text_size }}
- **Label Size:** {{ label_size }}
{% endif %}

### Shape Standards

{% for shape_standard in shape_standards %}
- **{{ shape_standard.shape }}**: {{ shape_standard.usage }}
{% endfor %}

### Arrow/Connection Standards

{% for arrow_standard in arrow_standards %}
- **{{ arrow_standard.type }}**: {{ arrow_standard.meaning }}
{% endfor %}

---

## 12. Testing Checklist

### Rendering

{% for render_check in rendering_checks %}
- [ ] {{ render_check }}
{% endfor %}

### Content

{% for content_check in content_checks %}
- [ ] {{ content_check }}
{% endfor %}

### Style

{% for style_check in style_checks %}
- [ ] {{ style_check }}
{% endfor %}

### Documentation

{% for doc_check in documentation_checks %}
- [ ] {{ doc_check }}
{% endfor %}

### Accessibility

{% if has_accessibility_requirements %}
{% for a11y_check in accessibility_checks %}
- [ ] {{ a11y_check }}
{% endfor %}
{% endif %}

---

## 13. Embedding Examples

{% for embedding_example in embedding_examples %}
### Example {{ loop.index }}: {{ embedding_example.title }}

**Location:** {{ embedding_example.location }}
**Section:** {{ embedding_example.section }}

```markdown
{{ embedding_example.markdown_code }}
```

**Preview:**
{{ embedding_example.preview_description }}

---

{% endfor %}

---

## 14. Export Specifications

{% if diagram_tool in ['drawio', 'lucidchart', 'figma', 'visio'] %}
### Export Settings

{% for export_spec in export_specifications %}
**Format: {{ export_spec.format }}**
- **Resolution:** {{ export_spec.resolution }}
- **DPI:** {{ export_spec.dpi }}
- **Color Space:** {{ export_spec.color_space }}
- **Transparency:** {{ export_spec.transparency }}
- **Compression:** {{ export_spec.compression }}
- **Output Path:** `{{ export_spec.output_path }}`
{% endfor %}
{% endif %}

---

## 15. Source Files

{% if has_source_files %}
**Editable Source Files:**
{% for source_file in source_files %}
- **{{ source_file.diagram_name }}**: `{{ source_file.path }}`
  - **Tool:** {{ source_file.tool }}
  - **Version:** {{ source_file.version }}
  - **Last Modified:** {{ source_file.last_modified }}
{% endfor %}

**Editing Instructions:**
1. {{ editing_instruction_1 }}
2. {{ editing_instruction_2 }}
3. {{ editing_instruction_3 }}
{% endif %}

---

## 16. Notes for Documentation Engineer

### High Priority

{% for high_priority_task in high_priority_tasks %}
{{ loop.index }}. **{{ high_priority_task.task }}** - {{ high_priority_task.reason }}
{% endfor %}

### Medium Priority

{% for medium_priority_task in medium_priority_tasks %}
{{ loop.index }}. {{ medium_priority_task }}
{% endfor %}

### Low Priority (Future)

{% for low_priority_task in low_priority_tasks %}
{{ loop.index }}. {{ low_priority_task }}
{% endfor %}

### Tips

{% for tip in documentation_tips %}
- {{ tip }}
{% endfor %}

---

## 17. Deliverables Summary

**Created:**
{% for deliverable in deliverables_created %}
- {{ deliverable }}
{% endfor %}

**Tested:**
{% for test_completed in tests_completed %}
- ✅ {{ test_completed }}
{% endfor %}

**Ready For:**
{% for ready_for in ready_for_list %}
- {{ ready_for }}
{% endfor %}

---

## 18. File Structure

```
{{ diagram_directory_structure }}
```

**Total Files:** {{ total_file_count }}
**Total Size:** {{ total_directory_size }}
**All verified and tested:** {{ all_verified }}

---

## Appendix A: Diagram Metadata

| Diagram | Type | Size (KB) | Dimensions | Last Updated |
|---------|------|-----------|------------|--------------|
{% for metadata in diagram_metadata %}
| {{ metadata.name }} | {{ metadata.type }} | {{ metadata.size_kb }} | {{ metadata.dimensions }} | {{ metadata.last_updated }} |
{% endfor %}

---

## Appendix B: Tool-Specific Notes

{% if diagram_tool == 'mermaid' %}
### Mermaid Notes

**Version:** {{ mermaid_version }}
**Supported Diagram Types:** {{ mermaid_supported_types }}

**Rendering Environments:**
- GitHub: {{ github_rendering_status }}
- GitLab: {{ gitlab_rendering_status }}
- mermaid.live: {{ mermaid_live_status }}

**Known Limitations:**
{% for limitation in mermaid_limitations %}
- {{ limitation }}
{% endfor %}

{% elif diagram_tool == 'drawio' %}
### Draw.io Notes

**Version:** {{ drawio_version }}
**File Format:** {{ drawio_format }}

**Integration:**
- VS Code Extension: {{ vscode_integration }}
- Desktop App: {{ desktop_app_version }}
- Online Editor: {{ online_editor_url }}

**Export Formats:**
{% for export_format in drawio_export_formats %}
- {{ export_format }}
{% endfor %}

{% elif diagram_tool == 'plantuml' %}
### PlantUML Notes

**Version:** {{ plantuml_version }}
**Server:** {{ plantuml_server_url }}

**Generation Command:**
```bash
{{ plantuml_generation_command }}
```

**Dependencies:**
{% for dependency in plantuml_dependencies %}
- {{ dependency }}
{% endfor %}

{% elif diagram_tool == 'lucidchart' %}
### Lucidchart Notes

**Account:** {{ lucidchart_account }}
**Sharing Settings:** {{ lucidchart_sharing }}

**Collaboration:**
- Edit Access: {{ lucidchart_edit_access }}
- Comment Access: {{ lucidchart_comment_access }}
- View Access: {{ lucidchart_view_access }}

{% elif diagram_tool == 'figma' %}
### Figma Notes

**File:** {{ figma_file_url }}
**Team:** {{ figma_team }}

**Access:**
- Edit: {{ figma_edit_access }}
- View: {{ figma_view_access }}

**Export Plugin:** {{ figma_export_plugin }}
{% endif %}

---

**Handoff Complete:** {{ handoff_date }}
**Diagram Engineer:** {{ config.roles.diagram_engineer or 'Diagram Engineer' }}
**Next Agent:** {{ config.roles.documentation_engineer or 'Documentation Engineer' }}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
