# Envarify
Environment variables parsing and validation using python type hints


# Usage

Having some environment variables set:
```bash
export TIMEOUT_S=2.5
export API_KEY=some_key
export ENABLE_FEATURE=true
```
We can create a config object in Python:
```python
from envarify import BaseModel, Envvar

class MyConfig(BaseModel):
    timeout_s: float = Envvar("TIMEOUT_S")
    api_key: str = Envvar("API_KEY")
    enable_feature = Envvar("ENABLE_FEATURE", default=False)

config = MyConfig.fromenv()
print(config)
#> MyConfig(timeout_s=2.5, api_key="some_key", enable_feature=True)
```

# Testing
In unit tests for your application you don't have to worry about mocking the environment variables. Instead just create a mock config object:  
```python
mock_config = MyConfig(timeout_s=4.2, api_key="dummy", enable_feature=True)
```
Or just a partial object:
```python
mock_config = MyConfig.partial(enable_feature=True)
print(mock_config)
#> MyConfig(enable_feature=True)
```


# Missing environment variables
If there are some required environment variables that are not set, error will be raised:
```python
config = MyConfig.fromenv()
#> MissingEnvVars: TIMEOUT_S, API_KEY, ENABLE_FEATURE
```
