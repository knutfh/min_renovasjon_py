<p align="center">
    <a href="https://img.shields.io/pypi/v/min-renovasjon" alt="Version">
        <img src="https://img.shields.io/pypi/v/min-renovasjon" /></a>
    <a href="https://img.shields.io/pypi/l/min-renovasjon" alt="License">
        <img src="https://img.shields.io/pypi/l/min-renovasjon" /></a>
</p>

### IN DEVELOPMENT

# Min Renovasjon Python API
Python 3 API for [Min Renovasjon][https://www.norkart.no/product/min-renovasjon/].

# Installation
`pip install min-renovasjon`

# Example
```python
from min_renovasjon import MinRenovasjon

search_string = "Jonas Lies gate 22, 200 Lillestrøm"
ren = MinRenovasjon(search_string)
```
Norwegian street names often contains the word veg/vei (it means road in English).
This package handles this automatically, so a lookup for 
`Hageveien` or `Hagevegen` should give the same result.

```python
# Fractions
ren.fractions()

# Next waste collections
ren.waste_collections()
```

###

[https://www.norkart.no/product/min-renovasjon/]: https://www.norkart.no/product/min-renovasjon/
