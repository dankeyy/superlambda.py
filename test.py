# coding: superlambda

f = lambda n:
        a, b = 0, 1
        for i in range(n):
            a, b = b, a + b
        return a

g = lambda:
        yield 1
        yield 2

h = lambda: return 3

k = lambda: yield from "gottem"

m = λ n:
    if n == 1:
        return n
    return n * m(n-1)

maptest = map(lambda x:
                  if x > 7:
                      print("banana")
                      return x - 1
                  print("apple")
                  return x + 1
              , (6,7,8,9))


print(f(10))
print(*g())
print(*k())
print(m(5))
print(list(maptest))
