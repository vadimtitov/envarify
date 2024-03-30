# Envarify
Environment variables parsing and validation using python type hints


# Usage

Having some environment variables:
```bash
export TIMEOUT_S=2.5
export API_KEY=some_key
export ALLOWED_IDS=1,2,3
export ENABLE_FEATURE=true
```
We can create a config object in Python:
```python
from envarify import BaseConfig, EnvVar

class MyConfig(BaseConfig):
    timeout_s: float = EnvVar("TIMEOUT_S")
    api_key: str = EnvVar("API_KEY")
    allowed_ids: set[int] = EnvVar("ALLOWED_IDS")
    enable_feature: bool = EnvVar("ENABLE_FEATURE", default=False)
    optional_arg: str | None = EnvVar("OPTIONAL_ARG", default=None)

config = MyConfig.fromenv()
print(config)
#> MyConfig(timeout_s=2.5, api_key="some_key", allowed_ids={1,2,3}, enable_feature=True, optional_arg=None)
```



# Missing environment variables
If there are some required environment variables that are not set, error will be raised:
```python
config = MyConfig.fromenv()
#> MissingEnvVarsError: TIMEOUT_S, API_KEY, ALLOWED_IDS
```


# Testing
In tests for your application you don't have to worry about mocking the environment variables. Instead just create a mock config object:
```python
mock_config = MyConfig(timeout_s=4.2, api_key="dummy", allowed_ids={1,2,3}, enable_feature=True)
```

# Supported Types

 - ### Primitive types
    - `int`
    - `float`
    - `bool`
    - `str`


- ### Dictionary

    `dict` type reads environmental variable as JSON


- ### Sequences (delimiter separated values)
    - `list[T]`
    - `set[T]`
    - `tuple[T]`

      where `T` is any primitive type


- ### `BaseConfig` subtype itself
    With environment variables ```COMPONENT_TIMEOUT=5``` and ```OTHER=dummy``` you can do:
    ```python
    from envarify import BaseConfig, EnvVar

    class ComponentConfig(BaseConfig):
        timeout: int = EnvVar("COMPONENT_TIMEOUT")

    class ApplicationConfig(BaseConfig):
        component: ComponentConfig
        other: str = EnvVar("OTHER")

    config = ApplicationConfig.fromenv()
    print(config)
    #> ApplicationConfig(component=ComponentConfig(timeout=5), other='dummy')
    ```