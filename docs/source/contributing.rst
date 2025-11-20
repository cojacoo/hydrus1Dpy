Contributing
============

We welcome contributions to HYDRUS1DPy!

How to Contribute
-----------------

1. **Fork the repository**
2. **Create a feature branch**: ``git checkout -b feature-name``
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run tests**: ``pytest phase3/tests/``
6. **Commit**: ``git commit -m "Add feature"``
7. **Push**: ``git push origin feature-name``
8. **Create Pull Request**

Development Setup
-----------------

.. code-block:: bash

   # Clone repository
   git clone https://github.com/cojacoo/hydrus1Dpy.git
   cd hydrus1Dpy

   # Install in editable mode
   pip install -e phase3/

   # Install development dependencies
   pip install pytest pytest-cov black flake8

Code Style
----------

* Follow PEP 8 style guide
* Use type hints where appropriate
* Add docstrings to all public functions/classes
* Format code with ``black``

.. code-block:: bash

   black phase3/hydrus1dpy/

Testing
-------

All new code should include tests:

.. code-block:: bash

   # Run all tests
   pytest phase3/tests/

   # Run with coverage
   pytest phase3/tests/ --cov=hydrus1dpy

   # Run specific test
   pytest phase3/tests/test_unit.py::TestLinearSolver

Documentation
-------------

* Update docstrings for API changes
* Add examples for new features
* Update relevant guides/tutorials
* Build docs locally to check:

.. code-block:: bash

   cd docs
   make html
   # Open build/html/index.html

Pull Request Guidelines
-----------------------

Your PR should:

* Include tests for new functionality
* Pass all existing tests
* Update documentation
* Have clear commit messages
* Reference any related issues

Questions?
----------

* Open an issue on GitHub
* Email: [your email here]

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.
