import inspect

import mink

print(getattr(mink, "__version__", "?"))
print(inspect.signature(mink.PostureTask.__init__))
print([n for n in dir(mink.PostureTask) if not n.startswith("__")])
