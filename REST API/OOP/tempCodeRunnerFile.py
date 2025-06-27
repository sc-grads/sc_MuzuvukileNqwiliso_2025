
from my_module import greet
# main.py
import tools


# main.py
from tools import greet, add

import tools as t

greet_message = greet("Malinda")
print(greet_message)


print(tools.greet("Mzu"))
print("Version:", tools.version)
print("Sum:", tools.add(5, 3))
print("Users:", tools.users)
print("Config:", tools.config)



print(greet("Thabo"))
print("Addition:", add(10, 7))


print(t.greet("Lerato"))
print("Config theme:", t.config["theme"])
