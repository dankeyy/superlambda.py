# superlambda.py
Eventually I'll make it a proper lang.

This is supercharged multi-line capable lambda statements for snake lang. \
Small digression - this implementation is pretty hand-wavey, naive, and frankly stupid. \
[Being lazy as I am, I don't write any special voodoo parser, literally looping over text. more on that later]
Created merely for entertainment purposes, don't try this at work (home may be ok).\
Usage is the same as incdec, see section [how codecs](#how-codecs)

As always;
# the why, the what, the how

### the why
So at first I was hesitant whether or not to take a shot at this, because well I've already dove nose deep into codecs when working on [incdec](https://github.com/dankeyy/incdec.py) and didn't wanna get repetetive.
[And this kinda stuff is pretty codecs centered, as it is definetly not syntactically correct.]

But I've come to think multi line lambdas are a pretty cool worthy goal.\
Besides, I think the needed transformation from a statement-like multi-line lambda to a valid py expression is pretty interesting and educating.\
Also, it seems to disturb a lot of people that python doesn't have those. And I am a man of the people, after all.

So this is codecs abuse, the sequel.

### the what
Presenting, multi line lambdas:

``` python
# coding: superlambda
# with love, to `def` haters

f = lambda n:
        a, b = 0, 1
        for i in range(n):
            a, b = b, a + b
        return a

print(f(10)) # prints 55, the 10th (11th? idk) fibonacci number
```

Now with the ability to make multiple yields, not as an expression

``` python
g = lambda:
        yield 1
        yield 2
```

And now here's something cute, with regular lambdas you can do `lambda: (yield 1)` with need to parenthesize the yield. superlambda special cases it so that you can

``` python
f = lambda: yield from "gottem"
```
[BTW this doesn't require a fancy transformation, parenthesis are just implicitly put around it lol]\
Speaking of weird special casing, ever wondered why you can't uselessly put a return in a lambda expression?
Well now you can.

``` python
f = lambda: return 1337
print(f()) # will trustly not raise a lame SyntaxError and print 1337
```
This again is done not with the special transformation, but just yeeting out the `return` from the code. Why? because I can.\
You can also use it in a a function call, for instance, let's see a map

``` python
maptest = map(lambda x:
                  if x > 7:
                      print("banana")
                      return x - 1
                  print("apple")
                  return x + 1
              , (6,7,8,9))
```
Executing by printing `list(maptest)` will ouput

``` python
apple
apple
banana
banana
[7, 8, 7, 8]
```
Do note the small caveat that we needed to put the comma on the line below the end of the lambda.
This may be annoying, but in my defense;
1. I parse like a lazy monkey.
2. This shit is pretty ambiguous, how would you know if you're returning a tuple of stuff or the rightmost element is just another argument to the function (map in this case). iirc that was guido's main argument against multi line lambdas.

More on that at the end of the post.

Anyways, now for the cherry on top;

``` python
m = λ n:
    if n == 1:
        return n
    return n * m(n-1)
```
Yes indeed you can make use of the actual lambda character. \
Also I forgot to mention, I parse the assignment too, so you can self reference the function name and make recursive calls. \
I'm no expert, but I'd say, that's pretty cool.

Now enough code, let's see how;

### the how
I will divide the `how`s into two parts.

#### _how codecs_ 
This question is pretty much already answered (I hope fullfillingly) over at the incdec repo. So to avoid repetition, please read the following- https://github.com/dankeyy/incdec.py#q-but-how-tf-do-you-do-text-replacements-i-thought-python-didnt-have-macros.

#### how is _how multi line lambda_
So I actually took a while to think what would be the cleanest approach to this. And after thinking and playing with it for a while, i've come to the following possible transformation: \
`"FunctionType(compile(<a def representation of the lambda>, '<preprocessed lambda>', 'single').co_consts[0], globals())\n"`.
So let's start breaking it down. \
[In favour of anyone not familiar with code obj stuff, here's a some mildly long tedious blob of text on how to mess with this sort of stuff, feel free to skip ahead.]

Remember, at this stage of compile/run-time (preprocessed time? encoding time? call it how you wish), all we have are strings and bytes. \
There are no live functions. We cannot create a function aside and pass it to the mapping or assignment (or whoever whatever requires it), \
simply because it does not exist yet.\
The most sophisticated transformation we can do is text replacement.
So what text replacement can we do?

First, we need to way to dynamically create a function from a blob of text.
Luckily, python allows the creation of functions dynamically with [FunctionType](https://docs.python.org/3/library/types.html?highlight=functiontype#types.FunctionType).

Small note is that in the the code itself I use `type(lambda:1)` instead of types FunctionType.
The explaination for this is that built-in types in python are often also initializers. e.g `type(1)` is equivalent to `int` so that `type(1)('2')` would be equivilant to `int('2')`.
In the same sense python, `type(lambda:"anything")` is equivilant to `types.FunctionType` (this is how roughly how it's implemented too, btw).
So we can take advantage of that and `type(lambda:1)` our way into a dynamic function ().
Why I use it instead of FunctionType is simply because I prefer to avoid types import. Though it would be possible in expression form as `__import__('types').FunctionType`.

Now to the fun part. The function initializer takes 5 arguments. 2 of them are relevant to us now, 1 may interest us later, the other 2 I don't care about for purposes of this post.
First two arguments are 2. globals, globals is simply the globals dict, env context for the function's use. \
And more importantly- 1. The code object that contains the actual function logic (at this point you may want to assist the docs/ cpython source as to what is a code object/ or try to follow along).

So how do we make a code object for our function, again from a blob of text? \
I believe there's a hard way, and an easy way. \
The hard way is to go through python's CodeType and create the code from the ground up.\
And believe me, that's pretty tedious. And I like easy ways so;
What's the easy way? it is of course, steal. \

Maybe we can steal a function's code object? \
First let's think, what happens when we `exec` a function definition?
``` python
In [98]: exec('def f(): pass')
```
Well obviously nothing because we haven't called it. But what has actually happened? We can compile the definition and see we get _some_ code object.

``` python
In [100]: compile('def f(): pass', filename='interactive', mode='exec')
Out[100]: <code object <module> at 0x7f493117d370, file "interactive", line 1>
```

But what's in it? we can use the dis module to look inside;

``` python
In [101]: from dis import dis
     ...: dis(compile('def f(): pass', filename='interactive', mode='exec'))
  1           0 LOAD_CONST               0 (<code object f at 0x7f49313bed90, file "interactive", line 1>)
              2 LOAD_CONST               1 ('f')
              4 MAKE_FUNCTION            0
              6 STORE_NAME               0 (f)
              8 LOAD_CONST               2 (None)
             10 RETURN_VALUE

Disassembly of <code object f at 0x7f49313bed90, file "interactive", line 1>:
  1           0 LOAD_CONST               0 (None)
              2 RETURN_VALUE

```
So clearly there's more than one thingy here. First there is some code, then there's some other inner code object.
Simply put, there's code object that's the return value of compile, and there's code object that's nested inside of it- the code for the function itself.
the first few lines are mostly prep work opcodes to make the function and return some value, the below are opcodes of the our `f` function.
We can see the structure of the returning code object via code object's `co_consts` attribute.
``` python
In [102]: compile('def f(): pass', filename='interactive', mode='exec').co_consts
Out[102]: (<code object f at 0x7f49313bc5b0, file "interactive", line 1>, 'f', None)
```
First element is the function code, second and third are out binding name and a the some return value from earlier (not of the function!), we can ignore them both for now.

So after observing this curious structure of code, we can see that it's possible for us to really touch the code object of the function we made (just for general knowledge, if it was an already existing function, it'd be `f.__code__`).
And if we can access it, we can steal it. And just to make sure we're getting everything right:

``` python
In [107]: FunctionType(compile("def f(): print(1)", filename="", mode="exec").co_consts[0], globals())()
1
```
And indeed it works.
The actual transformation is just like that, with the small caveat of needing to convert the header of the lambda decl to a def which is left for the reader to see it in the source code.

# problems & nitpicks
### You regex source code?? don't you know how bad it is??
[Why yes, yes I do.](https://i.redd.it/ior3kee8mjf71.jpg)


### How do you not fup indentation?
It actually is tricky.
See if you want to support functions with no explicit return, and/or just yields (not necessarily on last line ofc). You cannot rely on the `return` to stop parsing the function.
So how it's done is by the general off side rule, just marginally more naive/ stupider. Every line should start with the indentation of the first line after the lambda header.
Once reached a line that opens with indentation lesser than that set indentation, it counts as the end of the lambda function.

This is very very dumb in this context, because say you're mapping a lambda over some iterable, in the line below the lambda decl, you have to indent a bit further back than the lambda contents (even though inside parens every indentation should be allowed!). \
This sort of approach to indentation-based syntax is something that makes some sense for general statement-like cpython syntax, but not so much for location-flexible expressions. \
It makes the implementation pretty fragile. \
I mean, if you wanna break it, go ahead, it's very easy to do so, but I suggest playing nice.

Well that's all for now, hava nice day.
