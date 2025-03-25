from DesignTree import HierInstPath


if __name__ == "__main__":
    foo = HierInstPath("a.b.c", False)
    bar = HierInstPath("e.f.g", False)
    add = foo + bar
    print(f"foo = {foo}")
    print(f"bar = {bar}")
    print(f"foo + bar = {add}")
    print(f"foo.parent = {foo.parent()}")
    foo.names += ("d",)
    print(f"foo = {foo}")
    print(f"foo.parent = {foo.parent()}")
    print(f"foo + bar = {add}")
