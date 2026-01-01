# DocuForge

**A Custom Document Generation Engine with Type-Safe Template Processing**

DocuForge is a Django-based document generation API featuring a custom template engine designed for legal and clinical document automation. It demonstrates best practices for building production-grade template systems with proper type safety and boolean logic handling.

## Key Features

### Custom Template Engine (Not Django/Jinja2)
- **Custom syntax** designed for document generation
- **Type-safe variable substitution** - handles None, tuples, lists without crashing
- **Conditional sections** with correct AND/OR precedence
- **Circular dependency detection** for section references

### Production-Ready
- RESTful API with Django REST Framework
- Multi-tenant support with subdomain isolation
- Comprehensive test coverage
- Ready for deployment on Heroku/Railway/Render

## The Problems This Solves

### Problem 1: Type Coercion Bugs

Common bug in template engines:
```python
# CRASHES with: "'tuple' object has no attribute 'strip'"
def substitute(template, context):
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", value.strip())  # Fails!
```

DocuForge solution:
```python
# Handles all types safely
context = {
    'name': 'John',           # String -> "John"
    'items': ('A', 'B', 'C'), # Tuple -> "A, B, C"
    'notes': None,            # None -> ""
    'active': True,           # Bool -> "Yes"
}
```

### Problem 2: AND/OR Precedence Bug

Common bug where OR is evaluated before AND:
```
Condition: "A AND B OR C"

WRONG (OR before AND): A AND (B OR C)
RIGHT (AND before OR): (A AND B) OR C

With A=False, B=True, C=True:
WRONG: False AND (True OR True) = False
RIGHT: (False AND True) OR True = True  ✓
```

DocuForge implements standard precedence: `NOT > AND > OR`

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/docuforge.git
cd docuforge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

## API Usage

### Render a Template

```bash
POST /api/render/

{
    "template": "Hello {{name}}, your items: {{items}}",
    "context": {
        "name": "John",
        "items": ["Apple", "Orange", "Banana"]
    }
}

Response:
{
    "content": "Hello John, your items: Apple, Orange, Banana",
    "variables_used": ["name", "items"],
    "conditions_evaluated": []
}
```

### Test a Condition

```bash
POST /api/test-condition/

{
    "condition": "age >= 18 AND has_consent OR is_emergency",
    "context": {
        "age": 16,
        "has_consent": false,
        "is_emergency": true
    }
}

Response:
{
    "condition": "age >= 18 AND has_consent OR is_emergency",
    "result": true,
    "explanation": "Condition evaluated to True"
}
```

### Validate a Template

```bash
POST /api/validate/

{
    "template": "Hello {{name}}, {% if active %}Welcome{% endif %}"
}

Response:
{
    "valid": true,
    "variables": ["name", "active"],
    "conditions": ["active"],
    "errors": []
}
```

## Template Syntax

### Variables
```
{{variable_name}}
{{user.profile.name}}  (dot notation for nested access)
```

### Conditionals
```
{% if condition %}
    Content shown if true
{% endif %}

{% if condition %}
    True content
{% else %}
    False content
{% endif %}
```

### Sections
```
{% section header %}
    This is the header content
{% endsection %}

{% include header %}
```

### Supported Condition Operators
- Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Logical: `AND`, `OR`, `NOT`
- Grouping: `(` `)`

## Type Handling

| Input Type | Output |
|------------|--------|
| `None` | `""` (empty string) |
| `str` | Stripped string |
| `int`/`float` | String representation |
| `bool` | `"Yes"` or `"No"` |
| `list`/`tuple` | Comma-separated values |
| `datetime` | ISO format string |

## Multi-Tenant Support

DocuForge supports subdomain-based multi-tenancy:

```
acme.docuforge.com -> Tenant: acme
lawfirm.docuforge.com -> Tenant: lawfirm
```

Or use the `X-Tenant-ID` header for API requests:
```bash
curl -H "X-Tenant-ID: acme" https://docuforge.com/api/templates/
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest tests/test_condition_evaluator.py -v
```

## Project Structure

```
docuforge/
├── core/
│   ├── parser/
│   │   ├── template_engine.py    # Custom template engine
│   │   ├── condition_evaluator.py # Boolean logic with correct precedence
│   │   ├── variable_resolver.py   # Dot notation variable access
│   │   └── exceptions.py          # Custom exceptions
│   └── models.py                  # Template & Document models
├── api/
│   ├── views.py                   # REST API endpoints
│   ├── serializers.py             # DRF serializers
│   └── urls.py                    # URL routing
├── tenants/
│   ├── models.py                  # Tenant model
│   └── middleware.py              # Subdomain routing
└── tests/
    ├── test_template_engine.py    # Template engine tests
    └── test_condition_evaluator.py # Precedence tests
```

## Deployment

### Heroku
```bash
heroku create docuforge
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run python manage.py migrate
```

### Railway
```bash
railway init
railway add postgresql
railway up
```

### Environment Variables
```
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgres://...
ALLOWED_HOSTS=.yourdomain.com
```

## License

MIT License - see LICENSE file for details.

## Author

**Ahmed Sallemi** | MediaTree
- Senior Full-Stack Developer
- Django | Python | SaaS Architecture

---

*Built to demonstrate best practices in custom template engine development with proper type safety and boolean logic handling.*
