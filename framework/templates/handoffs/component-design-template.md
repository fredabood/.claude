# Component/Feature Specification: {{ component_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.product_designer or 'Product Designer / UI/UX Designer' }}
**To:** {{ config.roles.frontend_engineer or 'Frontend Engineer' }}
**Purpose:** Comprehensive component/feature design specification
**Related Workflow:** Single Feature Development - Design Phase

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Component** | {{ component_name }} |
| **Created By** | {{ author_name }} |
| **Date** | {{ creation_date }} |
| **Framework** | {{ config.web_framework.frontend or 'React/Vue/Angular/Svelte' }} |
| **Status** | {{ document_status }} |

---

## 1. Executive Summary

**Component Name:** {{ component_name }}
**Type:** {{ component_type }}
**Purpose:** {{ component_purpose }}
**Complexity:** {{ complexity_level }}
**Estimated Implementation Time:** {{ estimated_hours }} hours

**Component Category:**
- [ ] Page/View (full screen component with routing)
- [ ] Layout Component (header, sidebar, footer)
- [ ] Feature Component (business logic, API integration)
- [ ] Presentational Component (display only, no logic)
- [ ] Form Component (user input, validation)
- [ ] Utility Component (shared, reusable)

---

## 2. Component Overview

### File Location

{% if config.web_framework.frontend == 'react' %}
**Location:** `frontend/src/components/{{ component_path }}/{{ component_name }}.tsx`
**Test File:** `frontend/src/components/{{ component_path }}/__tests__/{{ component_name }}.test.tsx`
**Styles:** `frontend/src/components/{{ component_path }}/{{ component_name }}.module.css`

{% elif config.web_framework.frontend == 'vue' %}
**Location:** `frontend/src/components/{{ component_path }}/{{ component_name }}.vue`
**Test File:** `frontend/src/components/{{ component_path }}/__tests__/{{ component_name }}.spec.ts`

{% elif config.web_framework.frontend == 'angular' %}
**Location:** `frontend/src/app/components/{{ component_path }}/{{ component_name }}.component.ts`
**Template:** `frontend/src/app/components/{{ component_path }}/{{ component_name }}.component.html`
**Styles:** `frontend/src/app/components/{{ component_path }}/{{ component_name }}.component.scss`
**Test File:** `frontend/src/app/components/{{ component_path }}/{{ component_name }}.component.spec.ts`

{% elif config.web_framework.frontend == 'svelte' %}
**Location:** `frontend/src/components/{{ component_path }}/{{ component_name }}.svelte`
**Test File:** `frontend/src/components/{{ component_path }}/__tests__/{{ component_name }}.test.ts`
{% endif %}

### Component Hierarchy

**Parent:** {{ parent_component or 'N/A' }}
**Children:** {{ child_components_list }}
**Sibling Components:** {{ sibling_components_list }}

---

## 3. Props/Input Interface

{% if config.web_framework.frontend == 'react' %}
### TypeScript Interface

```typescript
interface {{ component_name }}Props {
  /** {{ prop1_description }} */
  {{ prop1_name }}: {{ prop1_type }};

  /** {{ prop2_description }} (optional) */
  {{ prop2_name }}?: {{ prop2_type }};

  /** Callback when {{ callback_action }} occurs */
  {{ callback_name }}?: (data: {{ callback_data_type }}) => void;

  /** Additional CSS class names */
  className?: string;

  /** Component ID for testing */
  testId?: string;
}
```

{% elif config.web_framework.frontend == 'vue' %}
### Props Definition

```typescript
<script setup lang="ts">
interface Props {
  /** {{ prop1_description }} */
  {{ prop1_name }}: {{ prop1_type }};

  /** {{ prop2_description }} (optional) */
  {{ prop2_name }}?: {{ prop2_type }};
}

const props = withDefaults(defineProps<Props>(), {
  {{ prop2_name }}: {{ prop2_default_value }},
});

const emit = defineEmits<{
  {{ event_name }}: [data: {{ event_data_type }}]
}>();
</script>
```

{% elif config.web_framework.frontend == 'angular' %}
### Component Inputs

```typescript
@Component({
  selector: 'app-{{ component_selector }}',
  templateUrl: './{{ component_name }}.component.html',
  styleUrls: ['./{{ component_name }}.component.scss']
})
export class {{ component_name }}Component {
  /** {{ prop1_description }} */
  @Input() {{ prop1_name }}!: {{ prop1_type }};

  /** {{ prop2_description }} (optional) */
  @Input() {{ prop2_name }}?: {{ prop2_type }};

  /** Emits when {{ event_action }} occurs */
  @Output() {{ event_name }} = new EventEmitter<{{ event_data_type }}>();
}
```

{% elif config.web_framework.frontend == 'svelte' %}
### Props Definition

```typescript
<script lang="ts">
  /** {{ prop1_description }} */
  export let {{ prop1_name }}: {{ prop1_type }};

  /** {{ prop2_description }} (optional) */
  export let {{ prop2_name }}: {{ prop2_type }} = {{ prop2_default_value }};

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher<{
    {{ event_name }}: {{ event_data_type }};
  }>();
</script>
```
{% endif %}

**Required Props:**
{% for prop in required_props %}
- `{{ prop.name }}`: {{ prop.description }} (type: `{{ prop.type }}`)
{% endfor %}

**Optional Props:**
{% for prop in optional_props %}
- `{{ prop.name }}`: {{ prop.description }} (default: `{{ prop.default }}`)
{% endfor %}

---

## 4. State Management

### Local State

{% if config.web_framework.frontend == 'react' %}
```typescript
// User selections
const [selected, setSelected] = useState<{{ selection_type }} | null>(null);

// Loading states
const [loading, setLoading] = useState<boolean>(false);

// Error states
const [error, setError] = useState<string | null>(null);

// Form data
const [formData, setFormData] = useState<{{ form_data_type }}>({
  {{ form_field_1 }}: {{ form_field_1_default }},
  {{ form_field_2 }}: {{ form_field_2_default }},
});
```

### Computed State (useMemo)

```typescript
const {{ computed_value_name }} = useMemo(() => {
  {{ computed_value_logic }}
}, [{{ dependencies }}]);
```

{% elif config.web_framework.frontend == 'vue' %}
```typescript
<script setup lang="ts">
import { ref, computed } from 'vue';

// User selections
const selected = ref<{{ selection_type }} | null>(null);

// Loading states
const loading = ref<boolean>(false);

// Error states
const error = ref<string | null>(null);

// Form data
const formData = ref<{{ form_data_type }}>({
  {{ form_field_1 }}: {{ form_field_1_default }},
  {{ form_field_2 }}: {{ form_field_2_default }},
});

// Computed values
const {{ computed_value_name }} = computed(() => {
  {{ computed_value_logic }}
});
</script>
```

{% elif config.web_framework.frontend == 'angular' %}
```typescript
export class {{ component_name }}Component {
  // User selections
  selected: {{ selection_type }} | null = null;

  // Loading states
  loading: boolean = false;

  // Error states
  error: string | null = null;

  // Form data
  formData: {{ form_data_type }} = {
    {{ form_field_1 }}: {{ form_field_1_default }},
    {{ form_field_2 }}: {{ form_field_2_default }},
  };

  // Computed values (getters)
  get {{ computed_value_name }}(): {{ computed_value_type }} {
    {{ computed_value_logic }}
  }
}
```

{% elif config.web_framework.frontend == 'svelte' %}
```typescript
<script lang="ts">
  import { writable, derived } from 'svelte/store';

  // User selections
  let selected: {{ selection_type }} | null = null;

  // Loading states
  let loading: boolean = false;

  // Error states
  let error: string | null = null;

  // Form data
  let formData: {{ form_data_type }} = {
    {{ form_field_1 }}: {{ form_field_1_default }},
    {{ form_field_2 }}: {{ form_field_2_default }},
  };

  // Reactive statements
  $: {{ computed_value_name }} = {{ computed_value_logic }};
</script>
```
{% endif %}

{% if config.state_management %}
### Global State Management

**State Management Library:** {{ config.state_management.library or 'Redux/Zustand/Pinia/NgRx' }}

{% if config.state_management.library == 'redux' %}
**Redux Slice:**
```typescript
// store/slices/{{ slice_name }}Slice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface {{ slice_name }}State {
  {{ state_property }}: {{ state_type }};
}

const {{ slice_name }}Slice = createSlice({
  name: '{{ slice_name }}',
  initialState: {{ initial_state }},
  reducers: {
    {{ action_name }}: (state, action: PayloadAction<{{ action_payload_type }}>) => {
      {{ action_logic }}
    },
  },
});

export const { {{ action_name }} } = {{ slice_name }}Slice.actions;
export default {{ slice_name }}Slice.reducer;
```

{% elif config.state_management.library == 'pinia' %}
**Pinia Store:**
```typescript
// stores/{{ store_name }}.ts
import { defineStore } from 'pinia';

export const use{{ store_name }}Store = defineStore('{{ store_name }}', {
  state: () => ({
    {{ state_property }}: {{ initial_value }},
  }),
  getters: {
    {{ getter_name }}(state) {
      {{ getter_logic }}
    },
  },
  actions: {
    {{ action_name }}(payload: {{ action_payload_type }}) {
      {{ action_logic }}
    },
  },
});
```

{% elif config.state_management.library == 'zustand' %}
**Zustand Store:**
```typescript
// store/{{ store_name }}Store.ts
import create from 'zustand';

interface {{ store_name }}State {
  {{ state_property }}: {{ state_type }};
  {{ action_name }}: (payload: {{ action_payload_type }}) => void;
}

export const use{{ store_name }}Store = create<{{ store_name }}State>((set) => ({
  {{ state_property }}: {{ initial_value }},
  {{ action_name }}: (payload) => set((state) => ({ {{ state_update_logic }} })),
}));
```
{% endif %}
{% endif %}

---

## 5. API Integration

### Endpoints Used

{% for endpoint in api_endpoints %}
**{{ loop.index }}. {{ endpoint.name }}**
- **Method:** `{{ endpoint.method }}` `{{ endpoint.path }}`
- **When:** {{ endpoint.trigger }}
- **Request:**
  {% if endpoint.request_body %}
  ```typescript
  {{ endpoint.request_body }}
  ```
  {% else %}
  No request body
  {% endif %}
- **Success Response:**
  ```typescript
  {{ endpoint.success_response }}
  ```
- **Error Handling:** {{ endpoint.error_handling }}

{% endfor %}

### API Call Implementation

{% if config.web_framework.frontend == 'react' %}
```typescript
useEffect(() => {
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.{{ api_method }}({{ api_params }});
      {{ success_handler }}
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      {{ error_handler }}
    } finally {
      setLoading(false);
    }
  };

  fetchData();
}, [{{ dependencies }}]);
```

{% elif config.web_framework.frontend == 'vue' %}
```typescript
<script setup lang="ts">
import { onMounted } from 'vue';

const fetchData = async () => {
  try {
    loading.value = true;
    error.value = null;

    const response = await api.{{ api_method }}({{ api_params }});
    {{ success_handler }}
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch data';
    {{ error_handler }}
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
});
</script>
```

{% elif config.web_framework.frontend == 'angular' %}
```typescript
export class {{ component_name }}Component implements OnInit {
  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.fetchData();
  }

  fetchData(): void {
    this.loading = true;
    this.error = null;

    this.apiService.{{ api_method }}({{ api_params }})
      .subscribe({
        next: (response) => {
          {{ success_handler }}
          this.loading = false;
        },
        error: (err) => {
          this.error = err.message || 'Failed to fetch data';
          {{ error_handler }}
          this.loading = false;
        }
      });
  }
}
```

{% elif config.web_framework.frontend == 'svelte' %}
```typescript
<script lang="ts">
  import { onMount } from 'svelte';

  onMount(async () => {
    try {
      loading = true;
      error = null;

      const response = await api.{{ api_method }}({{ api_params }});
      {{ success_handler }}
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to fetch data';
      {{ error_handler }}
    } finally {
      loading = false;
    }
  });
</script>
```
{% endif %}

---

## 6. UI States & Rendering

### Loading State

**When:** {{ loading_state_trigger }}

**Display:**
{% if config.web_framework.frontend == 'react' %}
```tsx
{loading && (
  <div className="loading-state" role="status" aria-live="polite">
    <Spinner size={{ spinner_size }} />
    <p>{{ loading_message }}</p>
  </div>
)}
```

{% elif config.web_framework.frontend == 'vue' %}
```vue
<div v-if="loading" class="loading-state" role="status" aria-live="polite">
  <Spinner :size="{{ spinner_size }}" />
  <p>{{ loading_message }}</p>
</div>
```

{% elif config.web_framework.frontend == 'angular' %}
```html
<div *ngIf="loading" class="loading-state" role="status" aria-live="polite">
  <app-spinner [size]="{{ spinner_size }}"></app-spinner>
  <p>{{ loading_message }}</p>
</div>
```

{% elif config.web_framework.frontend == 'svelte' %}
```svelte
{#if loading}
  <div class="loading-state" role="status" aria-live="polite">
    <Spinner size={{{ spinner_size }}} />
    <p>{{ loading_message }}</p>
  </div>
{/if}
```
{% endif %}

### Error State

**When:** {{ error_state_trigger }}

**Display:**
{% if config.web_framework.frontend == 'react' %}
```tsx
{error && (
  <div className="error-state" role="alert">
    <Icon name="error" color="danger" />
    <h3>{{ error_title }}</h3>
    <p>{error}</p>
    <Button onClick={retry}>Try Again</Button>
  </div>
)}
```

{% elif config.web_framework.frontend == 'vue' %}
```vue
<div v-if="error" class="error-state" role="alert">
  <Icon name="error" color="danger" />
  <h3>{{ error_title }}</h3>
  <p>{{ error }}</p>
  <Button @click="retry">Try Again</Button>
</div>
```

{% elif config.web_framework.frontend == 'angular' %}
```html
<div *ngIf="error" class="error-state" role="alert">
  <app-icon name="error" color="danger"></app-icon>
  <h3>{{ error_title }}</h3>
  <p>{{ error }}</p>
  <button (click)="retry()">Try Again</button>
</div>
```

{% elif config.web_framework.frontend == 'svelte' %}
```svelte
{#if error}
  <div class="error-state" role="alert">
    <Icon name="error" color="danger" />
    <h3>{{ error_title }}</h3>
    <p>{error}</p>
    <Button on:click={retry}>Try Again</Button>
  </div>
{/if}
```
{% endif %}

### Empty State

**When:** {{ empty_state_trigger }}

**Display:**
{{ empty_state_markup }}

### Success State

**When:** {{ success_state_trigger }}

**Display:**
{{ success_state_markup }}

---

## 7. User Interactions

{% for interaction in user_interactions %}
### {{ loop.index }}. {{ interaction.name }}

**Trigger:** {{ interaction.trigger }}

**Implementation:**
{% if config.web_framework.frontend == 'react' %}
```typescript
const {{ interaction.handler_name }} = useCallback(async ({{ interaction.params }}) => {
  try {
    {{ interaction.pre_logic }}
    setLoading(true);

    {{ interaction.api_call }}

    {{ interaction.success_logic }}
  } catch (err) {
    {{ interaction.error_logic }}
  } finally {
    setLoading(false);
  }
}, [{{ interaction.dependencies }}]);
```

{% elif config.web_framework.frontend == 'vue' %}
```typescript
const {{ interaction.handler_name }} = async ({{ interaction.params }}) => {
  try {
    {{ interaction.pre_logic }}
    loading.value = true;

    {{ interaction.api_call }}

    {{ interaction.success_logic }}
  } catch (err) {
    {{ interaction.error_logic }}
  } finally {
    loading.value = false;
  }
};
```

{% elif config.web_framework.frontend == 'angular' %}
```typescript
{{ interaction.handler_name }}({{ interaction.params }}): void {
  {{ interaction.pre_logic }}
  this.loading = true;

  {{ interaction.api_call }}
    .subscribe({
      next: (response) => {
        {{ interaction.success_logic }}
        this.loading = false;
      },
      error: (err) => {
        {{ interaction.error_logic }}
        this.loading = false;
      }
    });
}
```

{% elif config.web_framework.frontend == 'svelte' %}
```typescript
async function {{ interaction.handler_name }}({{ interaction.params }}) {
  try {
    {{ interaction.pre_logic }}
    loading = true;

    {{ interaction.api_call }}

    {{ interaction.success_logic }}
  } catch (err) {
    {{ interaction.error_logic }}
  } finally {
    loading = false;
  }
}
```
{% endif %}

**Expected Result:** {{ interaction.expected_result }}

{% endfor %}

---

## 8. UI Component Library

**Library:** {{ config.ui_library or 'Material-UI/Ant Design/Blueprint/Chakra UI/Custom' }}

**Components Used:**
{% for component in ui_components %}
- **{{ component.name }}**: {{ component.usage }}
{% endfor %}

**Import Statement:**
{% if config.ui_library == 'material-ui' %}
```typescript
import {
  {{ ui_component_imports }}
} from '@mui/material';
```

{% elif config.ui_library == 'ant-design' %}
```typescript
import {
  {{ ui_component_imports }}
} from 'antd';
```

{% elif config.ui_library == 'blueprint' %}
```typescript
import {
  {{ ui_component_imports }}
} from '@blueprintjs/core';
```

{% elif config.ui_library == 'chakra-ui' %}
```typescript
import {
  {{ ui_component_imports }}
} from '@chakra-ui/react';
```

{% elif config.ui_library == 'custom' %}
```typescript
import {
  {{ ui_component_imports }}
} from '@/components/ui';
```
{% endif %}

---

## 9. Accessibility Requirements

### ARIA Attributes

```html
<div role="{{ aria_role }}" aria-label="{{ aria_label }}">
  <input
    type="{{ input_type }}"
    aria-label="{{ input_label }}"
    aria-describedby="{{ describedby_id }}"
    aria-required="{{ is_required }}"
  />
  <p id="{{ describedby_id }}" class="sr-only">
    {{ help_text }}
  </p>
</div>

<button
  onClick={handleClick}
  aria-label="{{ button_label }}"
  aria-pressed="{{ is_pressed }}"
  aria-busy="{{ is_loading }}"
>
  {{ button_text }}
</button>

<div role="region" aria-label="{{ region_label }}" aria-live="polite">
  {{ dynamic_content }}
</div>
```

### Keyboard Navigation

{% for keyboard_action in keyboard_navigation %}
- **{{ keyboard_action.key }}**: {{ keyboard_action.action }}
{% endfor %}

### Screen Reader Support

{% for sr_requirement in screen_reader_requirements %}
- {{ sr_requirement }}
{% endfor %}

### WCAG Compliance

**Target Level:** {{ config.accessibility.wcag_level or 'WCAG 2.1 AA' }}

**Checklist:**
- [ ] Color contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- [ ] All interactive elements keyboard accessible
- [ ] Meaningful focus indicators
- [ ] Error messages clearly associated with form fields
- [ ] No information conveyed by color alone
- [ ] Alt text for all meaningful images

---

## 10. Form Validation

{% if has_form_validation %}
### Validation Schema

**Validation Library:** {{ config.validation.library or 'Yup/Zod/Joi' }}

{% if config.validation.library == 'yup' %}
```typescript
import * as yup from 'yup';

export const {{ schema_name }} = yup.object({
  {{ field_1_name }}: yup
    .{{ field_1_type }}()
    .required('{{ field_1_required_message }}')
    .{{ field_1_validation_rules }},

  {{ field_2_name }}: yup
    .{{ field_2_type }}()
    .{{ field_2_validation_rules }},
});
```

{% elif config.validation.library == 'zod' %}
```typescript
import { z } from 'zod';

export const {{ schema_name }} = z.object({
  {{ field_1_name }}: z
    .{{ field_1_type }}()
    .min({{ field_1_min }}, '{{ field_1_min_message }}'),

  {{ field_2_name }}: z
    .{{ field_2_type }}()
    .{{ field_2_validation_rules }},
});
```

{% elif config.validation.library == 'joi' %}
```typescript
import Joi from 'joi';

export const {{ schema_name }} = Joi.object({
  {{ field_1_name }}: Joi
    .{{ field_1_type }}()
    .required()
    .messages({ 'any.required': '{{ field_1_required_message }}' }),

  {{ field_2_name }}: Joi
    .{{ field_2_type }}()
    .{{ field_2_validation_rules }},
});
```
{% endif %}

### Client-Side Validation Rules

{% for field in validation_fields %}
**{{ field.name }}:**
{% for rule in field.rules %}
- {{ rule.description }} ({{ rule.constraint }})
{% endfor %}
{% endfor %}

### Server-Side Validation

**API Validation:** {{ api_validation_description }}

**Error Response Format:**
```typescript
{
  "status": 400,
  "message": "Validation failed",
  "errors": {
    "{{ field_name }}": ["{{ error_message }}"]
  }
}
```

{% endif %}

---

## 11. Styling

### CSS/SCSS Structure

{% if config.web_framework.frontend in ['react', 'vue'] %}
**File:** `{{ component_path }}/{{ component_name }}.module.css`

```css
.{{ component_class }} {
  {{ component_styles }}
}

.{{ component_class }}__header {
  {{ header_styles }}
}

.{{ component_class }}__title {
  {{ title_styles }}
}

.{{ component_class }}__list {
  {{ list_styles }}
}

.{{ component_class }}__card {
  {{ card_styles }}
}

.{{ component_class }}__card:hover {
  {{ card_hover_styles }}
}
```

{% elif config.web_framework.frontend == 'angular' %}
**File:** `{{ component_path }}/{{ component_name }}.component.scss`

```scss
:host {
  {{ host_styles }}
}

.{{ component_class }} {
  {{ component_styles }}
}
```

{% elif config.web_framework.frontend == 'svelte' %}
```svelte
<style>
  .{{ component_class }} {
    {{ component_styles }}
  }
</style>
```
{% endif %}

### Responsive Design

**Breakpoints:**
{% for breakpoint in responsive_breakpoints %}
- **{{ breakpoint.name }}**: {{ breakpoint.width }} ({{ breakpoint.description }})
{% endfor %}

**Mobile-First Approach:**
{{ mobile_first_approach_description }}

### Theming

{% if config.theming %}
**Theme Variables:**
```css
:root {
  --color-primary: {{ primary_color }};
  --color-secondary: {{ secondary_color }};
  --color-background: {{ background_color }};
  --color-text: {{ text_color }};
  --color-border: {{ border_color }};
  --spacing-unit: {{ spacing_unit }};
}
```
{% endif %}

---

## 12. Performance Optimizations

### Memoization

{% if config.web_framework.frontend == 'react' %}
```typescript
// Memoize expensive computations
const {{ computed_value }} = useMemo(() => {
  {{ computation_logic }}
}, [{{ dependencies }}]);

// Memoize callbacks
const {{ callback_name }} = useCallback(({{ params }}) => {
  {{ callback_logic }}
}, [{{ dependencies }}]);

// Memoize entire component
export default React.memo({{ component_name }});
```

{% elif config.web_framework.frontend == 'vue' %}
```typescript
<script setup lang="ts">
// Computed values are automatically memoized
const {{ computed_value }} = computed(() => {
  {{ computation_logic }}
});
</script>
```

{% elif config.web_framework.frontend == 'angular' %}
```typescript
// Use OnPush change detection
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class {{ component_name }}Component {
  // Computed values with getters
  get {{ computed_value }}(): {{ type }} {
    {{ computation_logic }}
  }
}
```

{% elif config.web_framework.frontend == 'svelte' %}
```typescript
<script lang="ts">
  // Reactive statements are automatically memoized
  $: {{ computed_value }} = {{ computation_logic }};
</script>
```
{% endif %}

### Debouncing

```typescript
{{ debounce_implementation }}
```

### Lazy Loading

{% if has_lazy_loading %}
{{ lazy_loading_implementation }}
{% endif %}

### Virtualization (for long lists)

{% if has_virtualization %}
**Library:** {{ virtualization_library or 'react-window/virtual-scroller' }}

{{ virtualization_implementation }}
{% endif %}

---

## 13. Testing Requirements

### Unit Tests

**Test File:** {{ test_file_path }}
**Testing Framework:** {{ config.testing.frontend_framework or 'Vitest/Jest/Cypress' }}

**Tests to Write:**

1. **Rendering Tests**
   {% for render_test in rendering_tests %}
   - {{ render_test }}
   {% endfor %}

2. **User Interaction Tests**
   {% for interaction_test in interaction_tests %}
   - {{ interaction_test }}
   {% endfor %}

3. **API Integration Tests** (mocked)
   {% for api_test in api_integration_tests %}
   - {{ api_test }}
   {% endfor %}

4. **Accessibility Tests**
   {% for a11y_test in accessibility_tests %}
   - {{ a11y_test }}
   {% endfor %}

**Coverage Target:** ≥ {{ config.quality_gates.test_coverage_minimum or 90 }}%

### Example Test

{% if config.testing.frontend_framework in ['vitest', 'jest'] %}
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/{{ config.web_framework.frontend }}';
import { describe, it, expect, vi } from '{{ config.testing.frontend_framework }}';
import {{ component_name }} from './{{ component_name }}';

describe('{{ component_name }}', () => {
  it('renders without crashing', () => {
    render(<{{ component_name }} {{ required_props }} />);
    expect(screen.getByText('{{ expected_text }}')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const mockHandler = vi.fn();
    render(<{{ component_name }} {{ required_props }} onAction={mockHandler} />);

    const button = screen.getByRole('button', { name: '{{ button_text }}' });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockHandler).toHaveBeenCalledWith({{ expected_call_args }});
    });
  });

  it('shows loading state', () => {
    render(<{{ component_name }} {{ required_props }} loading={true} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('handles errors gracefully', () => {
    render(<{{ component_name }} {{ required_props }} error="Test error" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Test error');
  });
});
```
{% endif %}

---

## 14. Documentation Requirements

### JSDoc/TSDoc

{% if config.web_framework.frontend in ['react', 'vue', 'svelte'] %}
```typescript
/**
 * {{ component_description }}
 *
 * This component {{ detailed_description }}
 *
 * @component
 * @since {{ component_version }}
 *
 * @example
 * Basic usage:
 * ```{{ config.web_framework.frontend == 'react' and 'tsx' or 'vue' }}
 * <{{ component_name }}
 *   {{ example_prop_1 }}="{{ example_value_1 }}"
 *   {{ example_prop_2 }}={{{ example_value_2 }}}
 * />
 * ```
 *
 * @example
 * With all props:
 * ```{{ config.web_framework.frontend == 'react' and 'tsx' or 'vue' }}
 * <{{ component_name }}
 *   {{ all_props_example }}
 * />
 * ```
 */
export const {{ component_name }}: {{ component_type }} = ({{ props }}) => {
  // Implementation
};
```

{% elif config.web_framework.frontend == 'angular' %}
```typescript
/**
 * {{ component_description }}
 *
 * This component {{ detailed_description }}
 *
 * @example
 * Basic usage:
 * ```html
 * <app-{{ component_selector }}
 *   [{{ example_prop_1 }}]="{{ example_value_1 }}"
 *   ({{ example_event }})="handleEvent($event)"
 * ></app-{{ component_selector }}>
 * ```
 */
@Component({
  selector: 'app-{{ component_selector }}',
  templateUrl: './{{ component_name }}.component.html',
  styleUrls: ['./{{ component_name }}.component.scss']
})
export class {{ component_name }}Component {
  // Implementation
}
```
{% endif %}

### README/Usage Documentation

Create `{{ component_path }}/README.md` with:
- Component purpose and overview
- Props/inputs documentation
- Usage examples (basic and advanced)
- Known limitations
- Related components

---

## 15. Implementation Checklist

**Setup:**
- [ ] Create component file(s)
- [ ] Create types/interfaces file
- [ ] Create styles file
- [ ] Create test file
- [ ] Create README documentation

**Implementation:**
- [ ] Define props/input interface
- [ ] Implement component structure
- [ ] Add state management (local and/or global)
- [ ] Integrate with API endpoints
- [ ] Implement all UI states (loading, error, empty, success)
- [ ] Add user interaction handlers
- [ ] Add form validation (if applicable)
- [ ] Add accessibility attributes (ARIA, keyboard nav)
- [ ] Add performance optimizations (memoization, debouncing)
- [ ] Add responsive design breakpoints

**Testing:**
- [ ] Write rendering tests (all UI states)
- [ ] Write interaction tests (user actions)
- [ ] Write API integration tests (mocked)
- [ ] Write accessibility tests (ARIA, keyboard)
- [ ] Achieve {{ config.quality_gates.test_coverage_minimum or 90 }}%+ coverage
- [ ] Manual testing in browser/device

**Documentation:**
- [ ] Add JSDoc/TSDoc to component
- [ ] Add usage examples in comments
- [ ] Document all props/inputs
- [ ] Add comments for complex logic
- [ ] Create README with usage guide

**Quality:**
- [ ] No TypeScript/ESLint errors
- [ ] No console warnings
- [ ] Linter passing
- [ ] Code reviewed
- [ ] Accessibility audit passed
- [ ] Performance audit passed

---

## 16. Next Steps

**For {{ config.roles.frontend_engineer or 'Frontend Engineer' }}:**

1. Read this specification thoroughly
2. Set up component files (component, styles, tests, README)
3. Implement component with framework-specific patterns
4. Add all UI states (loading, error, empty, success)
5. Integrate with API endpoints
6. Add accessibility attributes (WCAG {{ config.accessibility.wcag_level or 'AA' }})
7. Write comprehensive tests (≥{{ config.quality_gates.test_coverage_minimum or 90 }}% coverage)
8. Add JSDoc/TSDoc with usage examples
9. Manual test in browser at all breakpoints
10. Create integration handoff: `.claude/handoffs/integration-{{ component_name }}.md`

**Estimated Time:** {{ estimated_hours }} hours

**Handoff To:**
- Test Engineer (for comprehensive testing)
- Security Reviewer (for security audit)
- Documentation Engineer (for final docs)

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
