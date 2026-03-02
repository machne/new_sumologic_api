from sumologic import SumoLogic
import inspect

# Get all methods (functions) in the SumoLogic class
methods = [method for method in dir(SumoLogic) if not method.startswith('_') and callable(getattr(SumoLogic, method))]
print(methods)

# Or for more detail, use inspect
for name, method in inspect.getmembers(SumoLogic, predicate=inspect.ismethod):
    if not name.startswith('_'):
        print(f"{name}: {inspect.signature(method)}")