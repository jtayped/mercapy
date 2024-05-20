<h1 align="center">
  <br>
  <img src="https://github.com/jtayped/mercapy/blob/main/images/logo.png?raw=true" alt="mercapy" width="200">
  <br>
  🛍️ mercapy
  <br>
</h1>

<h4 align="center">A Mercadona interface for Python to track product prices, amounts, and more.</h4>

<div align="center">
  <a href="https://pypi.org/project/mercapy/">
    <img src="https://img.shields.io/pypi/v/mercapy?style=for-the-badge">
  </a>
  <a href="https://github.com/jtayped/mercapy/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/jtayped/mercapy?style=for-the-badge" alt="License">
  </a>
  <a href="https://github.com/jtayped/mercapy/issues">
    <img src="https://img.shields.io/github/issues/jtayped/mercapy?style=for-the-badge" alt="License">
  </a>
  <a href="https://www.linkedin.com/in/jtayped/">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
</div>

<div align="center">
  <a href="#how-to-use">How to use it</a> •
  <a href="#related">Related</a>
</div>

## 🔧 How to use it

First of all, install the package using:

```bash
pip install mercapy
```

By initializing the mercadona class, you can search products, recommendations, and new arrivals:

```python
from mercapy import Mercadona

mercadona = Mercadona()

mercadona.search("galletas")
mercadona.get_new_arrivals()
mercadona.get_home_recommendations()
```

Each product has statistics such as:

```python
from mercapy import Product

# Find product by ID
prod = Product("12345")

prod.name               # Beer
prod.unit_price         # 1.25€
prod.previos_price      # 1.95€
prod.is_discounted      # True
prod.bulk_price         # 7.5€
prod.is_pack            # True
prod.weight             # 0.5kg
prod.age_check          # True
prod.alcohol_by_volume  # 3.2%
prod.iva                # 21%
```

You can also interact with product photos:

```python
from mercapy import Product

# Find product by ID
prod = Product("12345")
prod.images[0].save("product.png", width=1920, height=1080)
```

More docs coming soon...

<div id="related"></div>

## 🙋‍♂️ You may also like...

- [📷📱 pygramcore](https://github.com/jtayped/pygramcore) - A simple-to-use Instagram interface for Python using Selenium.
- [🧑‍💼My Portfolio](https://joeltaylor.business) - Check out my front-end and SEO skills on my Portfolio!
