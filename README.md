### IN DEVELOPMENT

# Min Renovasjon Python API
Python 3 API for [Min Renovasjon][https://www.norkart.no/product/min-renovasjon/].

# Example
```
#!/usr/bin/env python3
from minrenovasjon import MinRenovasjon

search_string = "Jonas Lies gate 22, 200 Lillestrøm"
ren = MinRenovasjon(search_string)
```
Norwegian street names often contains the word veg/vei (it means road in English).
This package handles this automatically, so a lookup for 
`Hageveien` or `Hagevegen` should give the same result.

```
# Fractions
ren.fractions()

# Next waste collections
ren.waste_collections()
```

###

[https://www.norkart.no/product/min-renovasjon/]: https://www.norkart.no/product/min-renovasjon/