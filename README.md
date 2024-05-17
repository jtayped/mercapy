<h1 align="center">
  <br>
  <img src="https://github.com/jtayped/mercapy/blob/main/images/logo.png?raw=true" alt="mercapy" width="200">
  <br>
  🛍️ mercapy
  <br>
</h1>

<h4 align="center">A Mercadona SDK for Python to track product prices, amounts, and more.</h4>

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

Now you can start tracking multiple product's prices, availability, weight, etc.
```python
from mercapy import Product

water = Product("27335")
print(water.ean)
print(water.price)
print(water.origin)
```

And you can also get other recommended products:
```python
# Get recommended product's prices
recommeded = water.get_recommended()
for product in recommeded:
    print(product.price)
```

<div id="related"></div>

## 🙋‍♂️ You may also like...

- [📷📱 pygramcore](https://github.com/jtayped/pygramcore) - A simple-to-use Instagram SDK for Python using Selenium.
- [🧑‍💼My Portfolio](https://joeltaylor.business) - Check out my front-end and SEO skills on my Portfolio!
