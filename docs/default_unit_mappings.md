# Default unit mappings

When no output unit is specified, Sandpiper will try to convert to another
related unit. Some units convert two ways (Celsius <-> Fahrenheit), and others
map only one way for simplicity (Kelvin -> Celsius).

## Two-way

The units in each row will convert to each other.

### Length
| Metric          | Imperial       |
|-----------------|----------------|
| Kilometre `km`  | Mile `mi`      |
| Metre `m`       | Foot `ft or '` |
| Centimetre `cm` | Inch `in or "` |

### Area
| Metric       | Imperial    |
|--------------|-------------|
| Hectare `ha` | Acre `acre` |

### Speed
| Metric                           | Imperial                    |
|----------------------------------|-----------------------------|
| Kilometre per hour `kph or km/h` | Mile per hour `mph or mi/h` |

### Mass
| Metric        | Imperial          |
|---------------|-------------------|
| Gram `g`      | Ounce `oz`        |
| Kilogram `kg` | Pound `lb or lbs` |

### Volume
| Metric          | Imperial          |
|-----------------|-------------------|
| Litre `L`       | Gallon (US) `gal` |
| Millilitre `ml` | Cup `cup`         |

### Pressure
| Metric          | Imperial                             |
|-----------------|--------------------------------------|
| Pascal `pascal` | Pound\[-force] per square inch `psi` |

### Temperature
| Metric                    | Imperial                     |
|---------------------------|------------------------------|
| Celsius `C or degC or °C` | Fahrenheit `F or degF or °F` |

### Energy
| Metric    | Imperial                         |
|-----------|----------------------------------|
| Joule `J` | Foot pound `ft_lb or foot_pound` |

### Angle
| Radian       | Degree       |
|--------------|--------------|
| Radian `rad` | Degree `deg` |

## One-way

Only the units on the left will map to the unit on the right.

### Length
| From      | To        |
|-----------|-----------|
| Yard `yd` | Metre `m` |

### Speed
| From                          | To                               |
|-------------------------------|----------------------------------|
| Metre per second `mps or m/s` | Kilometre per hour `kph or km/h` |
| Foot per second `ft/s`        | Mile per hour `mph or mi/h`      |

### Mass
| From          | To            |
|---------------|---------------|
| Stone `stone` | Kilogram `kg` |

### Volume
| From                    | To              |
|-------------------------|-----------------|
| Pint (US) `pint`        | Litre `L`       |
| Fluid ounce (US) `floz` | Millilitre `ml` |

### Pressure
| From             | To                                         |
|------------------|--------------------------------------------|
| Atmosphere `atm` | Pound\[-force] per square inch `psi`       |
| Bar `bar`        | Pound\[-force] force per square inch `psi` |

### Temperature
| From       | To                        |
|------------|---------------------------|
| Kelvin `K` | Celsius `C or degC or °C` |

### Time
| From              | To             |
|-------------------|----------------|
| Second `s or sec` | Minute `min`   |
| Minute `min`      | Hour `h or hr` |
| Hour `h or hr`    | Day `day`      |
| Day `day`         | Week `week`    |
