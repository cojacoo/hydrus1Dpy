# HYDRUS1DPy Documentation

This directory contains the Sphinx documentation for HYDRUS1DPy.

## Building Documentation Locally

### Prerequisites

```bash
pip install -r requirements.txt
```

### Build HTML Documentation

```bash
cd docs
make html
```

The built documentation will be in `build/html/index.html`.

### Build PDF Documentation

```bash
make latexpdf
```

### Clean Build

```bash
make clean
```

## Live Preview

For development with auto-reload:

```bash
pip install sphinx-autobuild
make livehtml
```

Then open http://127.0.0.1:8000 in your browser.

## ReadTheDocs

Documentation is automatically built and hosted on ReadTheDocs when changes are pushed to the repository.

Configuration: `.readthedocs.yml` in repository root

## Documentation Structure

```
docs/
├── source/
│   ├── conf.py              # Sphinx configuration
│   ├── index.rst            # Main page
│   ├── api/                 # API reference (auto-generated from docstrings)
│   │   ├── core.rst
│   │   ├── processes.rst
│   │   ├── materials.rst
│   │   ├── numerics.rst
│   │   ├── io.rst
│   │   ├── visualization.rst
│   │   └── utils.rst
│   ├── tutorials/           # User tutorials
│   │   ├── installation.md
│   │   ├── quickstart.md
│   │   ├── atmospheric_bc.md
│   │   └── visualization.md
│   ├── guides/              # Detailed guides
│   │   ├── discretization.md
│   │   ├── boundary_conditions.md
│   │   └── soil_models.md
│   ├── examples/            # Code examples
│   │   ├── simple_infiltration.md
│   │   ├── atmospheric_bc.md
│   │   ├── xarray_usage.md
│   │   └── convergence_analysis.md
│   ├── contributing.rst     # Contribution guidelines
│   ├── changelog.rst        # Version history
│   └── license.rst          # License information
├── Makefile                 # Build commands
└── requirements.txt         # Documentation dependencies
```

## Writing Documentation

### Docstrings

All public functions and classes should have docstrings in NumPy or Google style:

```python
def my_function(param1, param2):
    """
    Short description.

    Longer description explaining what the function does.

    Parameters
    ----------
    param1 : type
        Description of param1
    param2 : type
        Description of param2

    Returns
    -------
    type
        Description of return value

    Examples
    --------
    >>> result = my_function(1, 2)
    >>> print(result)
    3
    """
    return param1 + param2
```

### reStructuredText (.rst) Files

Used for API documentation and formal pages:

```rst
Title
=====

Section
-------

Subsection
~~~~~~~~~~

**Bold** and *italic* text

Code block:

.. code-block:: python

   import hydrus1dpy
```

### Markdown (.md) Files

Used for tutorials and guides:

```markdown
# Title

## Section

### Subsection

**Bold** and *italic* text

Code block:
\`\`\`python
import hydrus1dpy
\`\`\`
```

## Autodoc

API documentation is automatically generated from docstrings using Sphinx autodoc:

```rst
.. autoclass:: hydrus1dpy.HydrusModel
   :members:
   :undoc-members:
   :show-inheritance:
```

## Updating Documentation

1. Edit docstrings in Python code
2. Update or add .rst/.md files
3. Rebuild documentation: `make html`
4. Check output in `build/html/`
5. Commit changes
6. Push to trigger ReadTheDocs build

## Troubleshooting

### Import errors during build

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
pip install -r ../phase3/requirements.txt
```

### Autodoc not finding modules

Check `sys.path` configuration in `source/conf.py`:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'phase3'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'phase2'))
```

### MyST parser errors

Ensure markdown extension is configured in `conf.py`:

```python
extensions = [
    ...
    'myst_parser',
]
```

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [ReadTheDocs](https://docs.readthedocs.io/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [MyST Parser](https://myst-parser.readthedocs.io/)
